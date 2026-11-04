using System.Diagnostics;
using System.Text;
using System.Text.Json;

namespace Review.Api;

public sealed class EngineException(string code) : Exception(code)
{
    public string Code { get; } = code;
}

public sealed class PythonEngine(ReviewOptions options, ILogger<PythonEngine> logger)
{
    private const int MaxOutputChars = 256 * 1024;

    public async Task<string> RunAsync(string pdfPath, CancellationToken cancellationToken)
    {
        using var deadline = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
        deadline.CancelAfter(TimeSpan.FromSeconds(options.TimeoutSeconds));
        var start = new ProcessStartInfo(options.Python)
        {
            UseShellExecute = false, RedirectStandardOutput = true,
            RedirectStandardError = true, CreateNoWindow = true,
        };
        start.ArgumentList.Add(options.EngineScript);
        start.ArgumentList.Add(pdfPath);
        start.Environment["PYTHONDONTWRITEBYTECODE"] = "1";
        using var process = new Process { StartInfo = start };
        var started = false;
        Task<string>? output = null;
        Task<string>? errors = null;
        try
        {
            process.Start();
            started = true;
            logger.LogInformation("Owned Python process {Pid}, started {Started:o}; no port; cleanup: kill owned process tree on cancellation", process.Id, process.StartTime.ToUniversalTime());
            output = ReadBoundedAsync(process.StandardOutput, deadline.Token);
            errors = ReadBoundedAsync(process.StandardError, deadline.Token);
            // Observe each pipe independently so EOF on one cannot hide a fault
            // on the other while a process is still running.
            var pending = new List<Task> { output, errors, process.WaitForExitAsync(deadline.Token) };
            while (pending.Count != 0)
            {
                var completed = await Task.WhenAny(pending);
                await completed;
                pending.Remove(completed);
            }
            var json = await output;
            await errors; // Drain stderr, but never expose it or keep it beyond the call.
            if (process.ExitCode != 0) throw new EngineException("engine_failed");
            using var document = JsonDocument.Parse(json);
            if (document.RootElement.ValueKind != JsonValueKind.Object)
                throw new EngineException("engine_failed");
            return json;
        }
        catch (OperationCanceledException) when (!cancellationToken.IsCancellationRequested)
        {
            throw new EngineException("engine_timeout");
        }
        catch (OperationCanceledException) { throw; }
        catch (EngineException) { throw; }
        catch (Exception) { throw new EngineException("engine_failed"); }
        finally
        {
            if (started)
            {
                if (!process.HasExited) process.Kill(entireProcessTree: true);
                await process.WaitForExitAsync(CancellationToken.None);
                deadline.Cancel();
                if (output is not null && errors is not null)
                {
                    try { await Task.WhenAll(output, errors); }
                    catch (Exception) { /* Original failure is preserved. */ }
                }
                logger.LogInformation("Owned Python process {Pid} exited", process.Id);
            }
        }
    }

    private static async Task<string> ReadBoundedAsync(StreamReader reader, CancellationToken token)
    {
        var result = new StringBuilder();
        var buffer = new char[4096];
        int read;
        while ((read = await reader.ReadAsync(buffer.AsMemory(), token)) != 0)
        {
            if (result.Length + read > MaxOutputChars) throw new EngineException("engine_output_limit");
            result.Append(buffer, 0, read);
        }
        return result.ToString();
    }
}
