using Microsoft.EntityFrameworkCore;
using StokYonetim.Data;
using StokYonetim.Models;

namespace StokYonetim.Services;

public class AuthService
{
    public bool ValidateCredentials(string email, string password, out AppUser? user, out string? error)
    {
        user = null;
        error = null;
        email = email.Trim();

        if (string.IsNullOrWhiteSpace(email) || string.IsNullOrWhiteSpace(password))
        {
            error = "E-posta ve şifre zorunludur.";
            return false;
        }

        using var db = new AppDbContext();
        var normalized = email.Trim().ToLowerInvariant();
        var found = db.AppUsers.AsNoTracking()
            .AsEnumerable()
            .FirstOrDefault(u => u.Email.Trim().ToLowerInvariant() == normalized);

        if (found == null || !PasswordHasher.Verify(password, found.PasswordHash))
        {
            error = "E-posta veya şifre hatalı.";
            return false;
        }

        if (!AuthorizationService.CanLogin(found.Role))
        {
            error = "Çalışan rolündeki kullanıcılar uygulamaya giriş yapamaz.";
            return false;
        }

        user = found;
        return true;
    }
}
