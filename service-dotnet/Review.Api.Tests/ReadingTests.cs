using System.Net;
using System.Net.Http.Json;
using System.Text.Json;
using Review.Api;
using Xunit;

namespace Review.Api.Tests;

public class ReadingTests
{
    [Fact]
    public void Validation_rejects_blank_names_and_nonfinite_values()
    {
        Assert.NotEmpty(new ReadingInput(" ", "load", 2, "kN", DateTimeOffset.UtcNow).Validate());
        Assert.NotEmpty(new ReadingInput("beam-1", "load", double.NaN, "kN", DateTimeOffset.UtcNow).Validate());
        Assert.Empty(new ReadingInput("beam-1", "load", 2, "kN", DateTimeOffset.UtcNow).Validate());
    }

    [Fact]
    public async Task Concurrent_writes_are_all_preserved_and_filterable()
    {
        await using var host = new ApiHost();
        using var client = host.CreateClient();
        var now = DateTimeOffset.UtcNow;
        var responses = await Task.WhenAll(Enumerable.Range(0, 20).Select(i => client.PostAsJsonAsync("/readings", new ReadingInput("beam-1", "load", i, "kN", now))));
        Assert.All(responses, response => Assert.Equal(HttpStatusCode.Created, response.StatusCode));
        var readings = await client.GetFromJsonAsync<JsonElement[]>("/readings?equipment=beam-1");
        Assert.Equal(20, readings!.Length);
        Assert.Equal(20, readings.Select(r => r.GetProperty("value").GetDouble()).Distinct().Count());
        Assert.Empty((await client.GetFromJsonAsync<JsonElement[]>("/readings?equipment=other"))!);
        Assert.Equal(HttpStatusCode.BadRequest, (await client.PostAsJsonAsync("/readings", new ReadingInput("", "load", 1, "kN", now))).StatusCode);
    }
}
