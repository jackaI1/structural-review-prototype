using System.Net;
using System.Net.Http.Headers;
using System.Net.Http.Json;
using System.Text;
using System.Text.Json;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Mvc.Testing;
using Xunit;
using Microsoft.Extensions.DependencyInjection;
using Swashbuckle.AspNetCore.Swagger;

namespace Review.Api.Tests;

public sealed class ApiHost : WebApplicationFactory<Program>
{
    public string DataPath { get; } = Path.Combine(Path.GetTempPath(), "review-tests-" + Guid.NewGuid());
    public string? Script { get; init; }
    public string? ExistingDataPath { get; init; }
    public int TimeoutSeconds { get; init; } = 10;
    protected override void ConfigureWebHost(IWebHostBuilder builder)
    {
        builder.UseSetting("Review:DataDirectory", ExistingDataPath ?? DataPath);
        builder.UseSetting("Review:Python", Environment.GetEnvironmentVariable("REVIEW_TEST_PYTHON") ?? "python3");
        builder.UseSetting("Review:TimeoutSeconds", TimeoutSeconds.ToString());
        builder.UseSetting("Logging:LogLevel:Default", "Warning");
        if (Script is not null) builder.UseSetting("Review:EngineScript", Script);
    }
    public override async ValueTask DisposeAsync()
    {
        await base.DisposeAsync();
        if (Directory.Exists(DataPath)) Directory.Delete(DataPath, true);
    }
}

public class ApiTests
{
    internal static byte[] Sample => File.ReadAllBytes(Path.Combine(AppContext.BaseDirectory, "synthetic-framing.pdf"));
    internal static async Task<HttpResponseMessage> Upload(HttpClient client, byte[] data, string name = "drawing.pdf", string type = "application/pdf")
    {
        using var form = new MultipartFormDataContent();
        var file = new ByteArrayContent(data);
        file.Headers.ContentType = new MediaTypeHeaderValue(type);
        form.Add(file, "file", name);
        return await client.PostAsync("/jobs", form);
    }
    internal static async Task<JsonElement> Terminal(HttpClient client, string location)
    {
        using var timeout = new CancellationTokenSource(TimeSpan.FromSeconds(15));
        while (true)
        {
            var status = await client.GetFromJsonAsync<JsonElement>(location, timeout.Token);
            if (status.GetProperty("status").GetString() is "succeeded" or "failed") return status;
            await Task.Delay(50, timeout.Token);
        }
    }

    [Fact]
    public async Task Upload_runs_real_python_and_returns_illustrative_result()
    {
        await using var host = new ApiHost();
        using var client = host.CreateClient();
        using var response = await Upload(client, Sample, "../../drawing.pdf");
        Assert.Equal(HttpStatusCode.Accepted, response.StatusCode);
        var location = response.Headers.Location!.ToString();
        var status = await Terminal(client, location);
        Assert.Equal("succeeded", status.GetProperty("status").GetString());
        var result = await client.GetFromJsonAsync<JsonElement>(location + "/result");
        Assert.Equal("synthetic-demo", result.GetProperty("mode").GetString());
        Assert.True(result.GetProperty("requiresEngineerApproval").GetBoolean());
        Assert.Equal(15, result.GetProperty("members")[0].GetProperty("momentKnM").GetDouble());
        Assert.Empty(Directory.GetFiles(Path.Combine(host.DataPath, "uploads")));
        Assert.DoesNotContain("drawing.pdf", await client.GetStringAsync(location));
    }

    [Theory]
    [InlineData("empty", "drawing.pdf", "application/pdf", 400)]
    [InlineData("wrong-header", "drawing.pdf", "application/pdf", 400)]
    [InlineData("valid", "drawing.txt", "application/pdf", 400)]
    [InlineData("valid", "drawing.pdf", "text/plain", 400)]
    [InlineData("oversize", "drawing.pdf", "application/pdf", 413)]
    public async Task Rejects_invalid_uploads_without_creating_files(string kind, string name, string type, int expected)
    {
        await using var host = new ApiHost();
        using var client = host.CreateClient();
        var data = kind switch
        {
            "empty" => [], "wrong-header" => Encoding.UTF8.GetBytes("not a PDF"),
            "oversize" => new byte[5 * 1024 * 1024 + 1], _ => Sample
        };
        using var response = await Upload(client, data, name, type);
        Assert.Equal(expected, (int)response.StatusCode);
        Assert.Empty(Directory.GetFiles(Path.Combine(host.DataPath, "uploads")));
    }

    [Fact]
    public async Task Unknown_jobs_and_results_are_404()
    {
        await using var host = new ApiHost();
        using var client = host.CreateClient();
        var id = Guid.NewGuid();
        Assert.Equal(HttpStatusCode.NotFound, (await client.GetAsync($"/jobs/{id}")).StatusCode);
        Assert.Equal(HttpStatusCode.NotFound, (await client.GetAsync($"/jobs/{id}/result")).StatusCode);
    }

    [Fact]
    public async Task Invalid_pdf_becomes_safe_failure_and_removes_upload()
    {
        await using var host = new ApiHost();
        using var client = host.CreateClient();
        using var response = await Upload(client, Encoding.ASCII.GetBytes("%PDF-1.4\ninvalid"));
        Assert.Equal(HttpStatusCode.Accepted, response.StatusCode);
        var location = response.Headers.Location!.ToString();
        var status = await Terminal(client, location);
        Assert.Equal("failed", status.GetProperty("status").GetString());
        Assert.Equal("engine_failed", status.GetProperty("error").GetString());
        Assert.Equal(HttpStatusCode.Conflict, (await client.GetAsync(location + "/result")).StatusCode);
        Assert.Empty(Directory.GetFiles(Path.Combine(host.DataPath, "uploads")));
        Assert.DoesNotContain(host.DataPath, status.ToString());
    }

    [Fact]
    public async Task Swagger_documents_upload_status_result_and_responses()
    {
        await using var host = new ApiHost();
        using var client = host.CreateClient();
        host.Services.GetRequiredService<ISwaggerProvider>().GetSwagger("v1");
        using var response = await client.GetAsync("/swagger/v1/swagger.json");
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
        var doc = await response.Content.ReadFromJsonAsync<JsonElement>();
        var paths = doc.GetProperty("paths");
        var post = paths.GetProperty("/jobs").GetProperty("post");
        Assert.True(post.GetProperty("requestBody").GetProperty("content").TryGetProperty("multipart/form-data", out _));
        Assert.True(post.GetProperty("responses").TryGetProperty("202", out _));
        Assert.True(paths.TryGetProperty("/jobs/{id}", out _));
        Assert.True(paths.TryGetProperty("/jobs/{id}/result", out _));
    }
}
