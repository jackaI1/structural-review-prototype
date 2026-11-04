using System.Diagnostics;
using System.Net;
using System.Net.Http.Json;
using System.Text.Json;
using Microsoft.Data.Sqlite;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging.Abstractions;
using Xunit;

namespace Review.Api.Tests;

public sealed class Scratch : IDisposable
{
    public string Path { get; } = System.IO.Path.Combine(System.IO.Path.GetTempPath(), "review tests " + Guid.NewGuid());
    public Scratch() => Directory.CreateDirectory(Path);
    public string WriteScript(string code)
    {
        var script = System.IO.Path.Combine(Path, "engine test.py");
        File.WriteAllText(script, code);
        return script;
    }
    public void Dispose() => Directory.Delete(Path, true);
}

public class LifecycleTests
{
    private static string Python => Environment.GetEnvironmentVariable("REVIEW_TEST_PYTHON") ?? "python3";

    [Fact]
    public async Task Missing_python_becomes_safe_engine_failure()
    {
        var engine = new PythonEngine(new ReviewOptions { Python = "no-such-review-python-executable" }, NullLogger<PythonEngine>.Instance);
        var error = await Assert.ThrowsAsync<EngineException>(() => engine.RunAsync("unused.pdf", CancellationToken.None));
        Assert.Equal("engine_failed", error.Code);
    }

    [Theory]
    [InlineData(false)]
    [InlineData(true)]
    public async Task Timeout_or_cancellation_reaps_owned_python(bool cancel)
    {
        using var scratch = new Scratch();
        var pidFile = Path.Combine(scratch.Path, "pid");
        var script = scratch.WriteScript("import os,time\nfrom pathlib import Path\nPath(" + JsonSerializer.Serialize(pidFile) + ").write_text(str(os.getpid()))\ntime.sleep(60)\n");
        var engine = new PythonEngine(new ReviewOptions { Python = Python, EngineScript = script, TimeoutSeconds = cancel ? 10 : 1 }, NullLogger<PythonEngine>.Instance);
        using var cancellation = new CancellationTokenSource();
        var running = engine.RunAsync("unused.pdf", cancellation.Token);
        Process? owned = null;
        try
        {
            using var startup = new CancellationTokenSource(TimeSpan.FromSeconds(5));
            while (!File.Exists(pidFile)) await Task.Delay(10, startup.Token);
            owned = Process.GetProcessById(int.Parse(await File.ReadAllTextAsync(pidFile, startup.Token)));
            var startTime = owned.StartTime;
            if (cancel)
            {
                cancellation.Cancel();
                await Assert.ThrowsAnyAsync<OperationCanceledException>(() => running);
            }
            else
            {
                var error = await Assert.ThrowsAsync<EngineException>(() => running);
                Assert.Equal("engine_timeout", error.Code);
            }
            Assert.True(owned.HasExited, $"Owned PID {owned.Id}, started {startTime:o}, was not reaped");
        }
        finally
        {
            cancellation.Cancel();
            if (owned is not null)
            {
                if (!owned.HasExited) owned.Kill(entireProcessTree: true);
                await owned.WaitForExitAsync();
                owned.Dispose();
            }
            try { await running; } catch (Exception) { }
        }
    }

    [Theory]
    [InlineData("import sys,time\nsys.stdout.write('x'*300000);sys.stdout.flush();time.sleep(60)", "engine_output_limit")]
    [InlineData("import os,sys,time\nos.close(1);sys.stderr.write('x'*300000);sys.stderr.flush();time.sleep(60)", "engine_output_limit")]
    [InlineData("print('[]')", "engine_failed")]
    [InlineData("print('invalid json')", "engine_failed")]
    public async Task Invalid_or_excessive_engine_output_is_safe_failure(string code, string expected)
    {
        using var scratch = new Scratch();
        var script = scratch.WriteScript(code);
        var engine = new PythonEngine(new ReviewOptions { Python = Python, EngineScript = script, TimeoutSeconds = 3 }, NullLogger<PythonEngine>.Instance);
        var elapsed = Stopwatch.StartNew();
        var error = await Assert.ThrowsAsync<EngineException>(() => engine.RunAsync("unused.pdf", CancellationToken.None));
        Assert.Equal(expected, error.Code);
        Assert.True(elapsed.Elapsed < TimeSpan.FromSeconds(2), "Output overflow should stop the child immediately, without waiting for the timeout.");
    }

    [Fact]
    public async Task Queued_and_interrupted_jobs_recover_and_results_survive_restart()
    {
        using var scratch = new Scratch();
        var options = new ReviewOptions { DataDirectory = scratch.Path };
        Directory.CreateDirectory(options.UploadDirectory);
        var queued = new ReviewJob { Id = Guid.NewGuid() };
        var interrupted = new ReviewJob { Id = Guid.NewGuid(), Status = "running" };
        var dbOptions = new DbContextOptionsBuilder<JobsDb>().UseSqlite(new SqliteConnectionStringBuilder
        { DataSource = Path.Combine(scratch.Path, "jobs.db"), Pooling = false }.ToString()).Options;
        await using (var db = new JobsDb(dbOptions))
        {
            await db.Database.EnsureCreatedAsync();
            db.Jobs.AddRange(queued, interrupted);
            await db.SaveChangesAsync();
        }
        await File.WriteAllBytesAsync(options.PdfPath(queued.Id), ApiTests.Sample);
        await File.WriteAllBytesAsync(options.PdfPath(interrupted.Id), ApiTests.Sample);
        var orphan = Path.Combine(options.UploadDirectory, Guid.NewGuid().ToString("N") + ".pdf");
        await File.WriteAllBytesAsync(orphan, ApiTests.Sample);
        await using (var first = new ApiHost { ExistingDataPath = scratch.Path })
        {
            using var client = first.CreateClient();
            foreach (var id in new[] { queued.Id, interrupted.Id })
            {
                var status = await ApiTests.Terminal(client, $"/jobs/{id}");
                Assert.Equal("succeeded", status.GetProperty("status").GetString());
            }
            Assert.False(File.Exists(orphan));
        }
        await using (var second = new ApiHost { ExistingDataPath = scratch.Path })
        {
            using var client = second.CreateClient();
            var result = await client.GetFromJsonAsync<JsonElement>($"/jobs/{interrupted.Id}/result");
            Assert.Equal(15, result.GetProperty("members")[0].GetProperty("reactionKn").GetDouble());
        }
    }

    [Fact]
    public async Task Running_result_is_409_and_timed_out_job_is_terminal()
    {
        using var scratch = new Scratch();
        await using var host = new ApiHost { Script = scratch.WriteScript("import time\ntime.sleep(60)"), TimeoutSeconds = 1 };
        using var client = host.CreateClient();
        using var response = await ApiTests.Upload(client, ApiTests.Sample);
        var location = response.Headers.Location!.ToString();
        Assert.Equal(HttpStatusCode.Conflict, (await client.GetAsync(location + "/result")).StatusCode);
        var status = await ApiTests.Terminal(client, location);
        Assert.Equal("failed", status.GetProperty("status").GetString());
        Assert.Equal("engine_timeout", status.GetProperty("error").GetString());
    }
}
