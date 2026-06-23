using StokYonetim.Data;
using StokYonetim.Models;

namespace StokYonetim.Services;

public static class FinanceLedgerService
{
    public static void RecordOrderIncome(AppDbContext db, int orderId, decimal amount, string customerName)
    {
        if (amount <= 0) return;

        db.FinanceEntries.Add(new FinanceEntry
        {
            EntryType = FinanceEntryTypes.Income,
            Category = FinanceCategories.Order,
            Amount = amount,
            Description = $"Sipariş geliri — {customerName} (#{orderId})",
            ReferenceType = "Order",
            ReferenceId = orderId,
            CreatedAt = DateTime.UtcNow
        });
    }

    public static void RecordOrderCancellation(AppDbContext db, int orderId, decimal amount, string customerName)
    {
        if (amount <= 0) return;

        db.FinanceEntries.Add(new FinanceEntry
        {
            EntryType = FinanceEntryTypes.Expense,
            Category = FinanceCategories.OrderCancellation,
            Amount = amount,
            Description = $"Sipariş iptali — {customerName} (#{orderId})",
            ReferenceType = "Order",
            ReferenceId = orderId,
            CreatedAt = DateTime.UtcNow
        });
    }

    public static void RecordPersonnelPayment(
        AppDbContext db,
        int paymentId,
        string paymentType,
        decimal amount,
        string personnelName)
    {
        if (amount <= 0) return;

        var category = paymentType switch
        {
            PersonnelPaymentTypes.Salary => FinanceCategories.Salary,
            PersonnelPaymentTypes.Bonus => FinanceCategories.Bonus,
            PersonnelPaymentTypes.Deduction => FinanceCategories.Deduction,
            _ => FinanceCategories.Salary
        };

        var entryType = paymentType == PersonnelPaymentTypes.Deduction
            ? FinanceEntryTypes.Income
            : FinanceEntryTypes.Expense;

        db.FinanceEntries.Add(new FinanceEntry
        {
            EntryType = entryType,
            Category = category,
            Amount = amount,
            Description = paymentType == PersonnelPaymentTypes.Deduction
                ? $"Personel kesintisi — {personnelName}"
                : $"Personel {paymentType.ToLower()} — {personnelName}",
            ReferenceType = "PersonnelPayment",
            ReferenceId = paymentId,
            CreatedAt = DateTime.UtcNow
        });
    }
}
