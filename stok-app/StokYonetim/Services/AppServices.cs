namespace StokYonetim.Services;

public sealed class AppServices
{
    public static AppServices Instance { get; } = new();

    public AppConfig Config { get; private set; } = new();
    public EmailService Email { get; private set; } = null!;
    public AuthService Auth { get; private set; } = null!;

    public static void Initialize()
    {
        var s = Instance;
        s.Config = AppConfig.Load();
        s.Email = new EmailService(s.Config.Smtp);
        s.Auth = new AuthService();
    }
}
