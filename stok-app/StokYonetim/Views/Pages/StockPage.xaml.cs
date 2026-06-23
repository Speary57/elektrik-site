using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Runtime.CompilerServices;
using System.Text.RegularExpressions;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using Microsoft.EntityFrameworkCore;
using StokYonetim.Data;
using StokYonetim.Services;

namespace StokYonetim.Views.Pages;

public class StockRow : INotifyPropertyChanged
{
    public int Id { get; set; }
    public string Name { get; set; } = "";
    public string CategoryName { get; set; } = "";

    private int _stockQuantity;
    public int StockQuantity
    {
        get => _stockQuantity;
        set { _stockQuantity = value; OnPropertyChanged(); }
    }

    private string _inputStock = "";
    public string InputStock
    {
        get => _inputStock;
        set { _inputStock = value; OnPropertyChanged(); }
    }

    public bool CanEdit { get; set; } = true;

    public event PropertyChangedEventHandler? PropertyChanged;
    private void OnPropertyChanged([CallerMemberName] string? name = null) =>
        PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(name));
}

public partial class StockPage : UserControl
{
    private readonly ObservableCollection<StockRow> _rows = new();
    private List<StockRow> _allRows = [];

    public StockPage()
    {
        InitializeComponent();
        StockList.ItemsSource = _rows;
        Loaded += (_, _) => Refresh();
    }

    public void ApplyAccessMode()
    {
        var canModify = AuthorizationService.CanModifyStock(CurrentUserService.Current?.Role);
        PageSubtitle.Text = canModify
            ? "Ürün stoklarını hızlı tuşlarla veya klavyeden sayı girerek düzenleyin."
            : "Ürün stoklarını görüntüleyin. Bu rol ile stok değişikliği yapılamaz.";
    }

    public void Refresh()
    {
        ApplyAccessMode();
        var canEdit = AuthorizationService.CanModifyStock(CurrentUserService.Current?.Role);

        using var db = new AppDbContext();
        _allRows = db.Products.AsNoTracking()
            .Include(p => p.Category)
            .OrderBy(p => p.Category!.Name)
            .ThenBy(p => p.Name)
            .Select(p => new StockRow
            {
                Id = p.Id,
                Name = p.Name,
                CategoryName = p.Category!.Name,
                StockQuantity = p.StockQuantity,
                InputStock = p.StockQuantity.ToString(),
                CanEdit = canEdit
            })
            .ToList();

        ApplyFilter();
    }

    private void ApplyFilter()
    {
        var q = SearchBox?.Text?.Trim() ?? "";
        var filtered = string.IsNullOrEmpty(q)
            ? _allRows
            : _allRows.Where(r =>
                r.Name.Contains(q, StringComparison.OrdinalIgnoreCase) ||
                r.CategoryName.Contains(q, StringComparison.OrdinalIgnoreCase)).ToList();

        _rows.Clear();
        foreach (var row in filtered)
            _rows.Add(row);

        EmptyText.Visibility = _allRows.Count == 0 ? Visibility.Visible : Visibility.Collapsed;
        SummaryText.Visibility = Visibility.Collapsed;
        SummaryBadge.Text = _allRows.Count == 0 ? "0 ürün" : $"{filtered.Count} / {_allRows.Count} ürün";
    }

    private void SearchBox_TextChanged(object sender, TextChangedEventArgs e) => ApplyFilter();

    private void Adjust_Click(object sender, RoutedEventArgs e)
    {
        if (!AuthorizationService.CanModifyStock(CurrentUserService.Current?.Role))
            return;

        if (sender is not Button btn || btn.Tag is not int id) return;
        if (!int.TryParse(btn.CommandParameter?.ToString(), out var delta)) return;
        ChangeStock(id, delta);
    }

    private void SaveInput_Click(object sender, RoutedEventArgs e)
    {
        if (!AuthorizationService.CanModifyStock(CurrentUserService.Current?.Role))
            return;

        if (sender is not Button btn || btn.Tag is not int id) return;
        var row = _rows.FirstOrDefault(r => r.Id == id);
        if (row == null) return;

        if (!int.TryParse(row.InputStock, out var value) || value < 0)
        {
            MessageBox.Show("Geçerli bir stok miktarı girin (0 veya üzeri).", "Uyarı",
                MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        SetStock(id, value);
    }

    private void StockInput_KeyDown(object sender, KeyEventArgs e)
    {
        if (!AuthorizationService.CanModifyStock(CurrentUserService.Current?.Role))
            return;

        if (e.Key != Key.Enter || sender is not TextBox box || box.Tag is not int id) return;
        var row = _rows.FirstOrDefault(r => r.Id == id);
        if (row == null) return;

        if (!int.TryParse(row.InputStock, out var value) || value < 0)
        {
            MessageBox.Show("Geçerli bir stok miktarı girin (0 veya üzeri).", "Uyarı",
                MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        SetStock(id, value);
    }

    private void StockInput_PreviewTextInput(object sender, TextCompositionEventArgs e)
    {
        e.Handled = !Regex.IsMatch(e.Text, @"^\d$");
    }

    private void ChangeStock(int productId, int delta)
    {
        using var db = new AppDbContext();
        var product = db.Products.FirstOrDefault(p => p.Id == productId);
        if (product == null) return;

        product.StockQuantity = Math.Max(0, product.StockQuantity + delta);
        product.UpdatedAt = DateTime.UtcNow;
        db.SaveChanges();

        UpdateRow(product.Id, product.StockQuantity);
    }

    private void SetStock(int productId, int value)
    {
        using var db = new AppDbContext();
        var product = db.Products.FirstOrDefault(p => p.Id == productId);
        if (product == null) return;

        product.StockQuantity = value;
        product.UpdatedAt = DateTime.UtcNow;
        db.SaveChanges();

        UpdateRow(product.Id, product.StockQuantity);
    }

    private void UpdateRow(int id, int stock)
    {
        var master = _allRows.FirstOrDefault(r => r.Id == id);
        if (master != null)
        {
            master.StockQuantity = stock;
            master.InputStock = stock.ToString();
        }

        var visible = _rows.FirstOrDefault(r => r.Id == id);
        if (visible != null)
        {
            visible.StockQuantity = stock;
            visible.InputStock = stock.ToString();
        }
    }
}
