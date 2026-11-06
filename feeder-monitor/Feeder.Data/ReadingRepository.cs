using Feeder.Core;
using Microsoft.EntityFrameworkCore;
namespace Feeder.Data;
public sealed class StoredReading
{
    public long Id { get; set; }
    public string Feeder { get; set; } = "";
    public DateTime RecordedAtUtc { get; set; }
    public double Voltage { get; set; }
    public double Current { get; set; }
    public bool BreakerClosed { get; set; }
}
public sealed class StoredAlarm
{
    public long Id { get; set; }
    public DateTime RecordedAtUtc { get; set; }
    public string Message { get; set; } = "";
    public bool Acknowledged { get; set; }
}
public sealed class MonitorDb(string connection) : DbContext
{
    public DbSet<StoredReading> Readings => Set<StoredReading>();
    public DbSet<StoredAlarm> Alarms => Set<StoredAlarm>();
    protected override void OnConfiguring(DbContextOptionsBuilder options) => options.UseSqlServer(connection);
}
public sealed class ReadingRepository(string connection)
{
    public async Task InitializeAsync() { await using var db = new MonitorDb(connection); await db.Database.EnsureCreatedAsync(); }
    public async Task SaveAsync(Reading reading, Alarm? alarm)
    {
        await using var db = new MonitorDb(connection);
        db.Readings.Add(new StoredReading { Feeder = reading.Feeder, RecordedAtUtc = reading.RecordedAtUtc, Voltage = reading.Voltage, Current = reading.Current, BreakerClosed = reading.BreakerClosed });
        StoredAlarm? item = alarm is null ? null : new StoredAlarm { RecordedAtUtc = alarm.RecordedAtUtc, Message = alarm.Message };
        if (item is not null) db.Alarms.Add(item);
        await db.SaveChangesAsync();
        if (item is not null) alarm!.Id = item.Id;
    }
    public async Task AcknowledgeAsync(long id) { await using var db = new MonitorDb(connection); var alarm = await db.Alarms.FindAsync(id) ?? throw new InvalidOperationException("Alarm not found"); alarm.Acknowledged = true; await db.SaveChangesAsync(); }
    public async Task<List<StoredReading>> RecentReadingsAsync() { await using var db = new MonitorDb(connection); return await db.Readings.OrderByDescending(x => x.Id).Take(120).ToListAsync(); }
    public async Task<List<StoredAlarm>> RecentAlarmsAsync() { await using var db = new MonitorDb(connection); return await db.Alarms.OrderByDescending(x => x.Id).Take(120).ToListAsync(); }
}
