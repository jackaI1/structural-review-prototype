namespace Feeder.Core;
public record Reading(string Feeder, DateTime RecordedAtUtc, double Voltage, double Current, bool BreakerClosed);
public static class AlarmRules
{
    public static string? Evaluate(Reading r) => !r.BreakerClosed ? "Breaker open" : r.Voltage < 108 || r.Voltage > 132 ? "Voltage outside 108–132 V" : r.Current > 100 ? "High current" : null;
}
