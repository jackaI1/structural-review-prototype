using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Runtime.CompilerServices;
using System.Windows.Input;
namespace Feeder.Core;
public abstract class ObservableObject : INotifyPropertyChanged
{
    public event PropertyChangedEventHandler? PropertyChanged;
    protected void Changed([CallerMemberName] string? name = null) => PropertyChanged?.Invoke(this, new(name));
}
public sealed class RelayCommand(Action action, Func<bool>? can = null) : ICommand
{
    public event EventHandler? CanExecuteChanged;
    public bool CanExecute(object? parameter) => can?.Invoke() ?? true;
    public void Execute(object? parameter) => action();
    public void Refresh() => CanExecuteChanged?.Invoke(this, EventArgs.Empty);
}
public sealed class Alarm : ObservableObject
{
    public long Id { get; set; }
    public DateTime RecordedAtUtc { get; set; }
    public string Message { get; set; } = "";
    private bool acknowledged;
    public bool Acknowledged { get => acknowledged; set { acknowledged = value; Changed(); } }
}
public sealed class MonitorViewModel : ObservableObject
{
    public ObservableCollection<Reading> Readings { get; } = [];
    public ObservableCollection<Alarm> Alarms { get; } = [];
    public event Action<Reading, Alarm?>? ReadingAccepted;
    public event Action<Alarm>? AcknowledgementRequested;
    private Alarm? selectedAlarm;
    public Alarm? SelectedAlarm { get => selectedAlarm; set { selectedAlarm = value; Changed(); AcknowledgeCommand.Refresh(); } }
    public RelayCommand AcknowledgeCommand { get; }
    public MonitorViewModel() => AcknowledgeCommand = new RelayCommand(() => { if (SelectedAlarm is { } a) AcknowledgementRequested?.Invoke(a); }, () => SelectedAlarm is { Acknowledged: false });
    public void Accept(Reading reading)
    {
        Readings.Insert(0, reading); if (Readings.Count > 120) Readings.RemoveAt(Readings.Count - 1);
        var message = AlarmRules.Evaluate(reading);
        var alarm = message is null ? null : new Alarm { RecordedAtUtc = reading.RecordedAtUtc, Message = $"{reading.Feeder}: {message}" };
        if (alarm is not null) Alarms.Insert(0, alarm);
        ReadingAccepted?.Invoke(reading, alarm);
    }
}
