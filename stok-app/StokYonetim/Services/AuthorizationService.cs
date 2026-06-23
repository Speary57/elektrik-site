using StokYonetim.Models;

namespace StokYonetim.Services;

public static class AuthorizationService
{
    public static bool CanLogin(string? role) =>
        role is UserRoles.Yonetici or PersonnelRoles.Depo or PersonnelRoles.Muhasebeci;

    public static bool CanAccessCategories(string? role) => role == UserRoles.Yonetici;

    public static bool CanAccessProducts(string? role) =>
        role is UserRoles.Yonetici or PersonnelRoles.Depo;

    public static bool CanAccessStock(string? role) =>
        role is UserRoles.Yonetici or PersonnelRoles.Depo or PersonnelRoles.Muhasebeci;

    public static bool CanAccessPersonnel(string? role) =>
        role is UserRoles.Yonetici or PersonnelRoles.Muhasebeci;

    public static bool CanManagePersonnel(string? role) => role == UserRoles.Yonetici;

    public static bool CanPayPersonnelSalary(string? role) =>
        role is UserRoles.Yonetici or PersonnelRoles.Muhasebeci;

    public static bool CanAccessUsers(string? role) => role == UserRoles.Yonetici;

    public static bool CanAccessOrderAdd(string? role) => role == UserRoles.Yonetici;

    public static bool CanAccessOrdersList(string? role) =>
        role is UserRoles.Yonetici or PersonnelRoles.Muhasebeci;

    public static bool CanManageOrders(string? role) => role == UserRoles.Yonetici;

    public static bool CanAccessFinance(string? role) =>
        role is UserRoles.Yonetici or PersonnelRoles.Muhasebeci;

    public static bool CanManageProducts(string? role) =>
        role is UserRoles.Yonetici or PersonnelRoles.Depo;

    public static bool CanModifyStock(string? role) =>
        role is UserRoles.Yonetici or PersonnelRoles.Depo;

    public static string DefaultPageForRole(string? role) => role switch
    {
        PersonnelRoles.Muhasebeci => "finance",
        PersonnelRoles.Depo => "products",
        _ => "categories"
    };
}
