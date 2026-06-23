using System.Globalization;

namespace StokYonetim.Views.Pages;

public class ProductPickerItem
{
    public int Id { get; set; }
    public string Name { get; set; } = "";
    public string CategoryName { get; set; } = "";
    public decimal UnitPrice { get; set; }
    public string DisplayName => $"{Name} ({CategoryName})";
}

public class OrderLineDraft
{
    public int ProductId { get; set; }
    public string ProductName { get; set; } = "";
    public string CategoryName { get; set; } = "";
    public int Quantity { get; set; }
    public decimal UnitPrice { get; set; }
    public decimal LineTotal => Quantity * UnitPrice;

    public string Display =>
        $"{ProductName} — {Quantity} adet × {UnitPrice.ToString("N2", CultureInfo.GetCultureInfo("tr-TR"))} ₺ = " +
        $"{LineTotal.ToString("N2", CultureInfo.GetCultureInfo("tr-TR"))} ₺";
}

public class OrderRow
{
    public int Id { get; set; }
    public string CustomerName { get; set; } = "";
    public string CustomerPhone { get; set; } = "";
    public string Notes { get; set; } = "";
    public DateTime CreatedAtUtc { get; set; }
    public int ItemCount { get; set; }
    public string ItemsSummary { get; set; } = "";
    public decimal TotalAmount { get; set; }

    public string CreatedAtDisplay =>
        CreatedAtUtc.ToLocalTime().ToString("dd.MM.yyyy HH:mm", CultureInfo.GetCultureInfo("tr-TR"));

    public string TotalAmountDisplay =>
        TotalAmount.ToString("N2", CultureInfo.GetCultureInfo("tr-TR")) + " ₺";
}

public class OrderDetailLine
{
    public string ProductName { get; set; } = "";
    public string CategoryName { get; set; } = "";
    public int Quantity { get; set; }
    public decimal UnitPrice { get; set; }
    public decimal LineTotal => Quantity * UnitPrice;

    public string UnitPriceDisplay =>
        UnitPrice.ToString("N2", CultureInfo.GetCultureInfo("tr-TR")) + " ₺";

    public string LineTotalDisplay =>
        LineTotal.ToString("N2", CultureInfo.GetCultureInfo("tr-TR")) + " ₺";
}
