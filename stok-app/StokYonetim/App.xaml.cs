using System.Windows;
using StokYonetim.Services;
using StokYonetim.Views;

namespace StokYonetim;

public partial class App : Application
{
    protected override void OnStartup(StartupEventArgs e)
    {
        base.OnStartup(e);
        AppServices.Initialize();
        DatabaseService.Initialize();

        var login = new LoginWindow();
        login.Show();
    }
}
