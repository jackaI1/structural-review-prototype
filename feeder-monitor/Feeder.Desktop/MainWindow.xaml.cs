using System.Windows;
namespace Feeder.Desktop;
public partial class MainWindow : Window
{
    private readonly DesktopViewModel model;
    public MainWindow() { InitializeComponent(); model = new DesktopViewModel(); DataContext = model; Loaded += async (_, _) => await model.StartAsync(); Closed += (_, _) => model.Dispose(); }
}
