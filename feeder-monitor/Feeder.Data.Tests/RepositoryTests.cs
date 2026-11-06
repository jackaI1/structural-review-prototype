using Feeder.Core;
using Feeder.Data;
using Testcontainers.MsSql;
using Xunit;
public class RepositoryTests
{
    [Fact] public async Task StoresReadingAndAcknowledgement()
    {
        await using var server = new MsSqlBuilder().Build();
        await server.StartAsync();
        var store = new ReadingRepository(server.GetConnectionString());
        await store.InitializeAsync();
        var alarm = new Alarm { RecordedAtUtc = DateTime.UtcNow, Message = "F1: High current" };
        await store.SaveAsync(new Reading("F1", DateTime.UtcNow, 120, 110, true), alarm);
        await store.AcknowledgeAsync(alarm.Id);
        Assert.Single(await store.RecentReadingsAsync());
        Assert.True((await store.RecentAlarmsAsync()).Single().Acknowledged);
    }
}
