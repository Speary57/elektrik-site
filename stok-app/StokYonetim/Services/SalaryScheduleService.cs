using System.Globalization;
using Microsoft.EntityFrameworkCore;
using StokYonetim.Data;
using StokYonetim.Models;

namespace StokYonetim.Services;

public static class SalaryScheduleService
{
    public const int MinPaymentDay = 1;
    public const int MaxPaymentDay = 28;

    public static int GetPaymentDay(AppDbContext db)
    {
        var settings = db.AppSettings.AsNoTracking().FirstOrDefault();
        if (settings == null) return 1;
        return ClampDay(settings.SalaryPaymentDay);
    }

    public static void SetPaymentDay(AppDbContext db, int day)
    {
        day = ClampDay(day);
        var settings = db.AppSettings.FirstOrDefault();
        if (settings == null)
        {
            db.AppSettings.Add(new AppSettings { Id = 1, SalaryPaymentDay = day });
        }
        else
        {
            settings.SalaryPaymentDay = day;
        }
        db.SaveChanges();
    }

    public static DateTime GetPaymentDateForMonth(int year, int month, int paymentDay)
    {
        paymentDay = ClampDay(paymentDay);
        var daysInMonth = DateTime.DaysInMonth(year, month);
        return new DateTime(year, month, Math.Min(paymentDay, daysInMonth));
    }

    public static DateTime GetNextPaymentDate(int paymentDay)
    {
        var today = DateTime.Today;
        var thisMonthDate = GetPaymentDateForMonth(today.Year, today.Month, paymentDay);
        if (today <= thisMonthDate) return thisMonthDate;

        var next = today.AddMonths(1);
        return GetPaymentDateForMonth(next.Year, next.Month, paymentDay);
    }

    public static bool IsTodayPaymentDay(int paymentDay) =>
        DateTime.Today == GetPaymentDateForMonth(DateTime.Today.Year, DateTime.Today.Month, paymentDay);

    public static string FormatPaymentDayInfo(int paymentDay)
    {
        var tr = CultureInfo.GetCultureInfo("tr-TR");
        var next = GetNextPaymentDate(paymentDay);
        var dayText = $"Her ayın {paymentDay}. günü";
        var nextText = $"Sonraki ödeme: {next.ToString("d MMMM yyyy", tr)}";
        if (IsTodayPaymentDay(paymentDay))
            return $"{dayText} — Bugün maaş günü. ({nextText})";
        return $"{dayText} — {nextText}";
    }

    public static bool HasSalaryPaidThisMonth(AppDbContext db, int personnelId)
    {
        var today = DateTime.Today;
        var monthStartUtc = new DateTime(today.Year, today.Month, 1).ToUniversalTime();
        var monthEndUtc = new DateTime(today.Year, today.Month, 1).AddMonths(1).ToUniversalTime();

        return db.PersonnelPayments.AsNoTracking().Any(p =>
            p.PersonnelId == personnelId &&
            p.PaymentType == PersonnelPaymentTypes.Salary &&
            p.CreatedAt >= monthStartUtc &&
            p.CreatedAt < monthEndUtc);
    }

    public static SalaryBatchResult PayMonthlySalaries(AppDbContext db, bool onlyActive = true)
    {
        var result = new SalaryBatchResult();
        var now = DateTime.UtcNow;
        var personnelQuery = db.Personnel.AsQueryable();
        if (onlyActive)
            personnelQuery = personnelQuery.Where(p => p.IsActive);

        var personnel = personnelQuery
            .Where(p => p.Salary > 0)
            .OrderBy(p => p.FullName)
            .ToList();

        foreach (var person in personnel)
        {
            if (HasSalaryPaidThisMonth(db, person.Id))
            {
                result.SkippedCount++;
                continue;
            }

            var payment = new PersonnelPayment
            {
                PersonnelId = person.Id,
                PaymentType = PersonnelPaymentTypes.Salary,
                Amount = person.Salary,
                CreatedAt = now
            };
            db.PersonnelPayments.Add(payment);
            db.SaveChanges();

            FinanceLedgerService.RecordPersonnelPayment(
                db, payment.Id, PersonnelPaymentTypes.Salary, person.Salary, person.FullName);
            db.SaveChanges();

            result.PaidCount++;
            result.TotalAmount += person.Salary;
        }

        return result;
    }

    private static int ClampDay(int day) => Math.Clamp(day, MinPaymentDay, MaxPaymentDay);
}

public class SalaryBatchResult
{
    public int PaidCount { get; set; }
    public int SkippedCount { get; set; }
    public decimal TotalAmount { get; set; }
}
