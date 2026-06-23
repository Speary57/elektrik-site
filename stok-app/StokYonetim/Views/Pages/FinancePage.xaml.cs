using System.Globalization;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using Microsoft.EntityFrameworkCore;
using StokYonetim.Data;
using StokYonetim.Models;

namespace StokYonetim.Views.Pages;

public class FinanceRow
{
    public int Id { get; set; }
    public string EntryType { get; set; } = "";
    public string Category { get; set; } = "";
    public string Description { get; set; } = "";
    public decimal Amount { get; set; }
    public DateTime CreatedAtUtc { get; set; }

    public string CreatedAtDisplay =>
        CreatedAtUtc.ToLocalTime().ToString("dd.MM.yyyy HH:mm", CultureInfo.GetCultureInfo("tr-TR"));

    public string AmountDisplay =>
        Amount.ToString("N2", CultureInfo.GetCultureInfo("tr-TR")) + " ₺";

    public Brush TypeBrush => EntryType == FinanceEntryTypes.Income
        ? new SolidColorBrush((Color)ColorConverter.ConvertFromString("#16A34A")!)
        : new SolidColorBrush((Color)ColorConverter.ConvertFromString("#DC2626")!);
}

public partial class FinancePage : UserControl
{
    private List<FinanceRow> _rows = [];
    private string _sortBy = "Date";
    private bool _sortAsc;
    private static readonly CultureInfo TrCulture = CultureInfo.GetCultureInfo("tr-TR");

    public FinancePage()
    {
        InitializeComponent();
        _sortAsc = false;
        Loaded += (_, _) => Refresh();
    }

    public void Refresh() => LoadEntries();

    private void LoadEntries()
    {
        using var db = new AppDbContext();
        _rows = db.FinanceEntries.AsNoTracking()
            .Select(e => new FinanceRow
            {
                Id = e.Id,
                EntryType = e.EntryType,
                Category = e.Category,
                Description = e.Description,
                Amount = e.Amount,
                CreatedAtUtc = e.CreatedAt
            })
            .ToList();

        var totalIncome = _rows.Where(r => r.EntryType == FinanceEntryTypes.Income).Sum(r => r.Amount);
        var totalExpense = _rows.Where(r => r.EntryType == FinanceEntryTypes.Expense).Sum(r => r.Amount);
        var net = totalIncome - totalExpense;

        TotalIncomeText.Text = totalIncome.ToString("N2", TrCulture) + " ₺";
        TotalExpenseText.Text = totalExpense.ToString("N2", TrCulture) + " ₺";
        NetTotalText.Text = net.ToString("N2", TrCulture) + " ₺";
        CountBadge.Text = $"{_rows.Count} kayıt";

        ApplySort();
        EmptyText.Visibility = _rows.Count == 0 ? Visibility.Visible : Visibility.Collapsed;
    }

    private void ApplySort()
    {
        IEnumerable<FinanceRow> sorted = _sortBy switch
        {
            "Type" => _sortAsc
                ? _rows.OrderBy(r => r.EntryType).ThenByDescending(r => r.CreatedAtUtc)
                : _rows.OrderByDescending(r => r.EntryType).ThenByDescending(r => r.CreatedAtUtc),
            "Category" => _sortAsc
                ? _rows.OrderBy(r => r.Category).ThenByDescending(r => r.CreatedAtUtc)
                : _rows.OrderByDescending(r => r.Category).ThenByDescending(r => r.CreatedAtUtc),
            "Description" => _sortAsc
                ? _rows.OrderBy(r => r.Description).ThenByDescending(r => r.CreatedAtUtc)
                : _rows.OrderByDescending(r => r.Description).ThenByDescending(r => r.CreatedAtUtc),
            "Amount" => _sortAsc
                ? _rows.OrderBy(r => r.Amount).ThenByDescending(r => r.CreatedAtUtc)
                : _rows.OrderByDescending(r => r.Amount).ThenByDescending(r => r.CreatedAtUtc),
            _ => _sortAsc
                ? _rows.OrderBy(r => r.CreatedAtUtc)
                : _rows.OrderByDescending(r => r.CreatedAtUtc)
        };

        EntriesList.ItemsSource = sorted.ToList();
        UpdateSortArrows();
    }

    private void UpdateSortArrows()
    {
        DateSortArrow.Visibility = _sortBy == "Date" ? Visibility.Visible : Visibility.Collapsed;
        TypeSortArrow.Visibility = _sortBy == "Type" ? Visibility.Visible : Visibility.Collapsed;
        CategorySortArrow.Visibility = _sortBy == "Category" ? Visibility.Visible : Visibility.Collapsed;
        DescriptionSortArrow.Visibility = _sortBy == "Description" ? Visibility.Visible : Visibility.Collapsed;
        AmountSortArrow.Visibility = _sortBy == "Amount" ? Visibility.Visible : Visibility.Collapsed;

        DateSortArrow.Text = _sortBy == "Date" ? (_sortAsc ? "▲" : "▼") : "";
        TypeSortArrow.Text = _sortBy == "Type" ? (_sortAsc ? "▲" : "▼") : "";
        CategorySortArrow.Text = _sortBy == "Category" ? (_sortAsc ? "▲" : "▼") : "";
        DescriptionSortArrow.Text = _sortBy == "Description" ? (_sortAsc ? "▲" : "▼") : "";
        AmountSortArrow.Text = _sortBy == "Amount" ? (_sortAsc ? "▲" : "▼") : "";
    }

    private void SortHeader_Click(object sender, RoutedEventArgs e)
    {
        if (sender is not Button btn || btn.Tag is not string column) return;
        if (_sortBy == column) _sortAsc = !_sortAsc;
        else { _sortBy = column; _sortAsc = column is "Category" or "Description"; }
        ApplySort();
    }

    private void EntriesList_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (EntriesList.SelectedItem is FinanceRow row)
            FooterHint.Text = $"{row.EntryType} — {row.Category}: {row.AmountDisplay}";
        else
            FooterHint.Text = "Kayıtlar otomatik oluşturulur.";
    }
}
