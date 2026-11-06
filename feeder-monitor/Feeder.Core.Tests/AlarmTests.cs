using Xunit;
using Feeder.Core;

public class AlarmTests
{
    [Fact] public void OvercurrentRaisesAlarm() => Assert.Contains("current", AlarmRules.Evaluate(new Reading("F1", DateTime.UtcNow, 120, 110, true))!);
    [Fact] public void NormalReadingHasNoAlarm() => Assert.Null(AlarmRules.Evaluate(new Reading("F1", DateTime.UtcNow, 120, 50, true)));
}
