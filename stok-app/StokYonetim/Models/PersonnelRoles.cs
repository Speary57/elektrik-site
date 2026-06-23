namespace StokYonetim.Models;

public static class PersonnelRoles
{
    public const string Depo = "Depo";
    public const string Muhasebeci = "Muhasebeci";
    public const string Calisan = "Çalışan";

    public static readonly string[] All = [Depo, Muhasebeci, Calisan];
}
