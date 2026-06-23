using System.IO;
using Microsoft.Extensions.Configuration;

namespace StokYonetim.Services;

public class SmtpConfig
{
    public string Host { get; set; } = "smtp.gmail.com";
    public int Port { get; set; } = 587;
    public string User { get; set; } = "";
    public string Password { get; set; } = "";
    public string From { get; set; } = "";
}

public class AdminConfig
{
    public string Email { get; set; } = "";
    public string Password { get; set; } = "";
}

public class AppConfig
{
    public SmtpConfig Smtp { get; set; } = new();
    public AdminConfig Admin { get; set; } = new();

    public static AppConfig Load()
    {
        var baseDir = GetAppBaseDirectory();
        var builder = new ConfigurationBuilder()
            .SetBasePath(baseDir);

        var envPath = FindEnvFile(baseDir);
        if (envPath != null)
            builder.Add(new EnvFileConfigurationSource(envPath));

        var settingsPath = Path.Combine(baseDir, "appsettings.json");
        builder.AddJsonFile(settingsPath, optional: true, reloadOnChange: false);

        var config = builder.Build();
        var app = new AppConfig();
        config.Bind(app);

        if (string.IsNullOrWhiteSpace(app.Smtp.From))
            app.Smtp.From = app.Smtp.User;

        return app;
    }

    private static string GetAppBaseDirectory()
    {
        var exePath = Environment.ProcessPath;
        if (!string.IsNullOrWhiteSpace(exePath))
        {
            var dir = Path.GetDirectoryName(exePath);
            if (!string.IsNullOrWhiteSpace(dir) && Directory.Exists(dir))
                return dir;
        }
        return AppContext.BaseDirectory;
    }

    private static string? FindEnvFile(string startDir)
    {
        var dir = new DirectoryInfo(startDir);
        for (var i = 0; i < 6 && dir != null; i++)
        {
            var candidate = Path.Combine(dir.FullName, ".env");
            if (File.Exists(candidate)) return candidate;
            dir = dir.Parent;
        }
        return null;
    }
}

internal sealed class EnvFileConfigurationSource(string path) : IConfigurationSource
{
    public IConfigurationProvider Build(IConfigurationBuilder builder) => new EnvFileConfigurationProvider(path);
}

internal sealed class EnvFileConfigurationProvider(string path) : ConfigurationProvider
{
    public override void Load()
    {
        foreach (var line in File.ReadAllLines(path))
        {
            var trimmed = line.Trim();
            if (trimmed.Length == 0 || trimmed.StartsWith('#')) continue;
            var eq = trimmed.IndexOf('=');
            if (eq <= 0) continue;

            var key = trimmed[..eq].Trim();
            var value = trimmed[(eq + 1)..].Trim().Trim('"');
            Data[key] = value;
        }

        Map("EMAIL_HOST", "Smtp:Host");
        Map("EMAIL_PORT", "Smtp:Port");
        Map("EMAIL_HOST_USER", "Smtp:User");
        Map("EMAIL_HOST_PASSWORD", "Smtp:Password");
        Map("DEFAULT_FROM_EMAIL", "Smtp:From");
        Map("ADMIN_EMAIL", "Admin:Email");
        Map("ADMIN_PASSWORD", "Admin:Password");
    }

    private void Map(string envKey, string configKey)
    {
        if (!Data.TryGetValue(envKey, out var value) || string.IsNullOrWhiteSpace(value)) return;
        Data[configKey] = value;
    }
}
