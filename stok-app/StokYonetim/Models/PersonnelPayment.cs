namespace StokYonetim.Models;

public class PersonnelPayment
{
    public int Id { get; set; }
    public int PersonnelId { get; set; }
    public Personnel? Personnel { get; set; }
    public string PaymentType { get; set; } = "";
    public decimal Amount { get; set; }
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
}

public static class PersonnelPaymentTypes
{
    public const string Salary = "Maaş";
    public const string Bonus = "Prim";
    public const string Deduction = "Kesinti";

    public static readonly string[] All = [Salary, Bonus, Deduction];
}
