using System.Globalization;
using System.Windows;
using Feeder.Core;
using Feeder.Data;
namespace Feeder.Desktop;
public sealed class DesktopViewModel : ObservableObject, IDisposable
{
    private readonly CancellationTokenSource stop = new();
    private readonly ReadingRepository repository = new(Environment.GetEnvironmentVariable("FEEDER_SQL") ?? @"Server=(localdb)\MSSQLLocalDB;Database=FeederMonitor;Integrated Security=true;TrustServerCertificate=true");
    public MonitorViewModel Monitor { get; } = new();
    private string status = "Connecting to SQL Server...";
    public string Status { get => status; private set { status = value; Changed(); } }
    public string Trend => string.Join(" ", Monitor.Readings.Reverse().Select((r, i) => $"{i * 4},{(180 - Math.Clamp(r.Current, 0, 150) * 1.2).ToString(CultureInfo.InvariantCulture)}"));
    public async Task StartAsync()
    {
        try {
            await repository.InitializeAsync();
            foreach (var r in (await repository.RecentReadingsAsync()).AsEnumerable().Reverse()) Monitor.Readings.Insert(0, new(r.Feeder, r.RecordedAtUtc, r.Voltage, r.Current, r.BreakerClosed));
            foreach (var a in (await repository.RecentAlarmsAsync()).AsEnumerable().Reverse()) Monitor.Alarms.Insert(0, new Alarm { Id = a.Id, RecordedAtUtc = a.RecordedAtUtc, Message = a.Message, Acknowledged = a.Acknowledged });
            Changed(nameof(Trend));
            Monitor.AcknowledgementRequested += Acknowledge;
            Status = "Simulation running; readings saved to SQL Server.";
            _ = Task.Run(SimulateAsync);
        } catch (Exception ex) { Status = $"Could not connect to SQL Server: {ex.Message}"; }
    }
    private async void Acknowledge(Alarm alarm)
    {
        try { await repository.AcknowledgeAsync(alarm.Id); alarm.Acknowledged = true; Monitor.AcknowledgeCommand.Refresh(); }
        catch (Exception ex) { Status = $"Could not acknowledge alarm: {ex.Message}"; }
    }
    private async Task SimulateAsync()
    {
        var random = new Random();
        try {
            while (!stop.IsCancellationRequested) {
                var reading = new Reading("Feeder A", DateTime.UtcNow, Math.Round(120 + random.NextDouble() * 16 - 8, 1), Math.Round(40 + random.NextDouble() * 80, 1), random.Next(30) != 0);
                var message = AlarmRules.Evaluate(reading);
                var storedAlarm = message is null ? null : new Alarm { RecordedAtUtc = reading.RecordedAtUtc, Message = $"{reading.Feeder}: {message}" };
                await repository.SaveAsync(reading, storedAlarm);
                await Application.Current.Dispatcher.InvokeAsync(() => {
                    Monitor.Accept(reading);
                    if (storedAlarm is not null) Monitor.Alarms[0].Id = storedAlarm.Id;
                    Changed(nameof(Trend));
                });
                await Task.Delay(TimeSpan.FromSeconds(2), stop.Token);
            }
        } catch (OperationCanceledException) { }
        catch (Exception ex) { if (!stop.IsCancellationRequested) await Application.Current.Dispatcher.InvokeAsync(() => Status = $"Simulation stopped: {ex.Message}"); }
    }
    public void Dispose() => stop.Cancel();
}
