using System.Windows;
using System.Windows.Input;
using System.Windows.Media;
using StokYonetim.Models;
using StokYonetim.Services;

namespace StokYonetim.Views;

public partial class LoginWindow : Window
{
    private bool _passwordVisible;

    private static readonly Geometry EyeOpen = Geometry.Parse(
        "M12,4.5C7,4.5 2.73,7.61 1,12c1.73,4.39 6,7.5 11,7.5s9.27,-3.11 11,-7.5c-1.73,-4.39 -6,-7.5 -11,-7.5zM12,17c-2.76,0 -5,-2.24 -5,-5s2.24,-5 5,-5 5,2.24 5,5 -2.24,5 -5,5zM12,9c-1.66,0 -3,1.34 -3,3s1.34,3 3,3 3,-1.34 3,-3 -1.34,-3 -3,-3z");

    private static readonly Geometry EyeClosed = Geometry.Parse(
        "M12,7c2.76,0 5,2.24 5,5 0,0.65 -0.13,1.26 -0.36,1.83l2.92,2.92c1.51,-1.26 2.7,-2.89 3.43,-4.75 -1.73,-4.39 -6,-7.5 -11,-7.5 -1.4,0 -2.74,0.25 -4,0.7l2.17,2.17C10.74,7.13 11.35,7 12,7zM2,4.27l2.28,2.28 0.46,0.46C3.08,8.3 1.78,10.02 1,12c1.73,4.39 6,7.5 11,7.5 1.55,0 3.03,-0.3 4.38,-0.84l0.42,0.42L19.73,22 21,20.73 3.27,3 2,4.27zM7.53,9.8l1.55,1.55c-0.05,0.21 -0.08,0.43 -0.08,0.65 0,1.66 1.34,3 3,3 0.22,0 0.44,-0.03 0.65,-0.08l1.55,1.55c-0.67,0.33 -1.41,0.53 -2.2,0.53 -2.76,0 -5,-2.24 -5,-5 0,-0.79 0.2,-1.53 0.53,-2.2zM11.84,9.02l3.15,3.15 0.02,-0.16c0,-1.66 -1.34,-3 -3,-3l-0.17,0.01z");

    public LoginWindow()
    {
        InitializeComponent();
        Loaded += (_, _) => UpdateCapsLockBanner();

        PreviewKeyDown += (_, e) =>
        {
            if (e.Key == Key.CapsLock) UpdateCapsLockBanner();
        };

        PasswordBox.GotKeyboardFocus += (_, _) => UpdateCapsLockBanner();
        PasswordText.GotKeyboardFocus += (_, _) => UpdateCapsLockBanner();
        PasswordBox.PreviewKeyDown += PasswordInput_PreviewKeyDown;
        PasswordText.PreviewKeyDown += PasswordInput_PreviewKeyDown;
        PasswordBox.PreviewKeyUp += PasswordInput_PreviewKeyUp;
        PasswordText.PreviewKeyUp += PasswordInput_PreviewKeyUp;
        PasswordBox.LostKeyboardFocus += (_, _) => CapsLockBanner.Visibility = Visibility.Collapsed;
        PasswordText.LostKeyboardFocus += (_, _) => CapsLockBanner.Visibility = Visibility.Collapsed;

        EmailBox.Focus();
    }

    private void PasswordInput_PreviewKeyDown(object sender, KeyEventArgs e)
    {
        if (e.Key == Key.CapsLock) Dispatcher.BeginInvoke(UpdateCapsLockBanner);
        else UpdateCapsLockBanner();
    }

    private void PasswordInput_PreviewKeyUp(object sender, KeyEventArgs e) => UpdateCapsLockBanner();

    private void UpdateCapsLockBanner()
    {
        var passwordFocused = PasswordBox.IsKeyboardFocused || PasswordText.IsKeyboardFocused;
        CapsLockBanner.Visibility = passwordFocused && Keyboard.IsKeyToggled(Key.CapsLock)
            ? Visibility.Visible
            : Visibility.Collapsed;
    }

    private string Password =>
        _passwordVisible ? PasswordText.Text : PasswordBox.Password;

    private void TogglePassword_Click(object sender, RoutedEventArgs e)
    {
        _passwordVisible = !_passwordVisible;
        if (_passwordVisible)
        {
            PasswordText.Text = PasswordBox.Password;
            PasswordBox.Visibility = Visibility.Collapsed;
            PasswordText.Visibility = Visibility.Visible;
            EyeIcon.Data = EyeClosed;
            PasswordText.Focus();
            PasswordText.CaretIndex = PasswordText.Text.Length;
        }
        else
        {
            PasswordBox.Password = PasswordText.Text;
            PasswordText.Visibility = Visibility.Collapsed;
            PasswordBox.Visibility = Visibility.Visible;
            EyeIcon.Data = EyeOpen;
            PasswordBox.Focus();
        }
        UpdateCapsLockBanner();
    }

    private void Input_KeyDown(object sender, KeyEventArgs e)
    {
        if (e.Key == Key.Enter) TryLogin();
    }

    private void PasswordBox_KeyDown(object sender, KeyEventArgs e)
    {
        if (e.Key == Key.Enter) TryLogin();
    }

    private void Login_Click(object sender, RoutedEventArgs e) => TryLogin();

    private void TryLogin()
    {
        ErrorText.Visibility = Visibility.Collapsed;
        LoginBtn.IsEnabled = false;

        try
        {
            var email = EmailBox.Text.Trim();
            var auth = AppServices.Instance.Auth;

            if (!auth.ValidateCredentials(email, Password, out var user, out var error))
            {
                ShowError(error ?? "Giriş başarısız.");
                return;
            }

            OpenMain(user!);
        }
        finally
        {
            LoginBtn.IsEnabled = true;
        }
    }

    private void ShowError(string message)
    {
        ErrorText.Text = message;
        ErrorText.Visibility = Visibility.Visible;
    }

    private void OpenMain(AppUser user)
    {
        CurrentUserService.Set(user);
        var main = new MainWindow();
        main.Show();
        Close();
    }
}
