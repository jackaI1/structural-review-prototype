using FlaUI.Core;
using FlaUI.UIA3;
using Xunit;
public class DesktopTests
{
    [Fact] public void ShowsLiveSimulation()
    {
        var executable = Environment.GetEnvironmentVariable("FEEDER_APP") ?? throw new InvalidOperationException("Set FEEDER_APP to the published executable");
        using var app = Application.Launch(executable);
        try {
            using var automation = new UIA3Automation();
            var window = app.GetMainWindow(automation, TimeSpan.FromSeconds(30));
            Assert.NotNull(window);
            var status = window.FindFirstDescendant(cf => cf.ByAutomationId("Status"));
            Assert.NotNull(status);
            Assert.True(SpinWait.SpinUntil(() => status.Name.Contains("Simulation running"), TimeSpan.FromSeconds(90)), $"Unexpected status: {status.Name}");
            var grid = window.FindFirstDescendant(cf => cf.ByAutomationId("Readings"));
            Assert.NotNull(grid);
            Assert.True(SpinWait.SpinUntil(() => grid.FindAllChildren().Length > 1, TimeSpan.FromSeconds(20)), "No readings appeared in the grid");
            Assert.NotNull(window.FindFirstDescendant(cf => cf.ByAutomationId("Acknowledge")));
        } finally { if (!app.HasExited) app.Close(); }
    }
}
