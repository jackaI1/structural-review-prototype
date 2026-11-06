using Feeder.Core;
using Xunit;
public class MonitorTests
{
    [Fact] public void NewReadingUpdatesLatestAndRaisesAlarm() {
        var vm = new MonitorViewModel();
        vm.Accept(new Reading("F1", DateTime.UtcNow, 120, 110, true));
        Assert.Single(vm.Readings); Assert.Single(vm.Alarms);
        Assert.Equal(110, vm.Readings[0].Current);
    }
}
