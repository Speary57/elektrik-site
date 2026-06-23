using StokYonetim.Models;

namespace StokYonetim.Services;

public static class CurrentUserService
{
    public static AppUser? Current { get; private set; }

    public static void Set(AppUser user) => Current = user;

    public static void Clear() => Current = null;
}
