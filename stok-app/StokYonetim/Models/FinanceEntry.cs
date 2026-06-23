namespace StokYonetim.Models;

public class FinanceEntry
{
    public int Id { get; set; }
    public string EntryType { get; set; } = "";
    public string Category { get; set; } = "";
    public string Description { get; set; } = "";
    public decimal Amount { get; set; }
    public string? ReferenceType { get; set; }
    public int? ReferenceId { get; set; }
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
}

public static class FinanceEntryTypes
{
    public const string Income = "Gelir";
    public const string Expense = "Gider";
}

public static class FinanceCategories
{
    public const string Order = "Sipariş";
    public const string OrderCancellation = "Sipariş İptali";
    public const string Salary = "Maaş";
    public const string Bonus = "Prim";
    public const string Deduction = "Kesinti";
}
