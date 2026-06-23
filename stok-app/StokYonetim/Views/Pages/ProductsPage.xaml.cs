using System.Globalization;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using Microsoft.EntityFrameworkCore;
using StokYonetim.Data;
using StokYonetim.Services;
using StokYonetim.Views;

namespace StokYonetim.Views.Pages;

public class ProductRow
{
    public int Id { get; set; }
    public string Name { get; set; } = "";
    public string CategoryName { get; set; } = "";
    public decimal UnitPrice { get; set; }
    public int StockQuantity { get; set; }
    public DateTime CreatedAtUtc { get; set; }
    public string CreatedAtLocal { get; set; } = "";

    public string UnitPriceDisplay =>
        UnitPrice.ToString("N2", CultureInfo.GetCultureInfo("tr-TR")) + " ₺";
}

public partial class ProductsPage : UserControl
{
    private List<ProductRow> _rows = [];
    private string _sortBy = "Name";
    private bool _sortAsc = true;

    public ProductsPage()
    {
        InitializeComponent();
        Loaded += (_, _) => Refresh();
    }

    public void ApplyAccessMode()
    {
        var canManage = AuthorizationService.CanManageProducts(CurrentUserService.Current?.Role);
        ToolbarPanel.Visibility = canManage ? Visibility.Visible : Visibility.Collapsed;
        AddProductBtn.Visibility = canManage ? Visibility.Visible : Visibility.Collapsed;
        DeleteBtn.Visibility = canManage ? Visibility.Visible : Visibility.Collapsed;
    }

    public void Refresh()
    {
        ApplyAccessMode();
        LoadProducts();
    }

    private void LoadProducts()
    {
        using var db = new AppDbContext();
        _rows = db.Products.AsNoTracking()
            .Include(p => p.Category)
            .Select(p => new ProductRow
            {
                Id = p.Id,
                Name = p.Name,
                CategoryName = p.Category!.Name,
                UnitPrice = p.UnitPrice,
                StockQuantity = p.StockQuantity,
                CreatedAtUtc = p.CreatedAt,
                CreatedAtLocal = p.CreatedAt.ToLocalTime().ToString("dd.MM.yyyy HH:mm")
            })
            .ToList();

        CountBadge.Text = $"{_rows.Count} ürün";
        ApplySort();
        EmptyText.Visibility = _rows.Count == 0 ? Visibility.Visible : Visibility.Collapsed;
        DeleteBtn.IsEnabled = false;
        FooterHint.Text = "Sıralamak için sütun başlığına tıklayın. Düzenlemek için ürüne çift tıklayın.";
    }

    private void ApplySort()
    {
        IEnumerable<ProductRow> sorted = _sortBy switch
        {
            "Category" => _sortAsc
                ? _rows.OrderBy(r => r.CategoryName, StringComparer.CurrentCultureIgnoreCase).ThenBy(r => r.Name)
                : _rows.OrderByDescending(r => r.CategoryName, StringComparer.CurrentCultureIgnoreCase).ThenBy(r => r.Name),
            "Price" => _sortAsc
                ? _rows.OrderBy(r => r.UnitPrice).ThenBy(r => r.Name)
                : _rows.OrderByDescending(r => r.UnitPrice).ThenBy(r => r.Name),
            "Stock" => _sortAsc
                ? _rows.OrderBy(r => r.StockQuantity).ThenBy(r => r.Name)
                : _rows.OrderByDescending(r => r.StockQuantity).ThenBy(r => r.Name),
            "Created" => _sortAsc
                ? _rows.OrderBy(r => r.CreatedAtUtc)
                : _rows.OrderByDescending(r => r.CreatedAtUtc),
            _ => _sortAsc
                ? _rows.OrderBy(r => r.Name, StringComparer.CurrentCultureIgnoreCase)
                : _rows.OrderByDescending(r => r.Name, StringComparer.CurrentCultureIgnoreCase)
        };

        ProductList.ItemsSource = sorted.ToList();
        UpdateSortArrows();
    }

    private void UpdateSortArrows()
    {
        NameSortArrow.Text = _sortBy == "Name" ? (_sortAsc ? "▲" : "▼") : "";
        CategorySortArrow.Text = _sortBy == "Category" ? (_sortAsc ? "▲" : "▼") : "";
        PriceSortArrow.Text = _sortBy == "Price" ? (_sortAsc ? "▲" : "▼") : "";
        StockSortArrow.Text = _sortBy == "Stock" ? (_sortAsc ? "▲" : "▼") : "";
        CreatedSortArrow.Text = _sortBy == "Created" ? (_sortAsc ? "▲" : "▼") : "";

        NameSortArrow.Visibility = _sortBy == "Name" ? Visibility.Visible : Visibility.Collapsed;
        CategorySortArrow.Visibility = _sortBy == "Category" ? Visibility.Visible : Visibility.Collapsed;
        PriceSortArrow.Visibility = _sortBy == "Price" ? Visibility.Visible : Visibility.Collapsed;
        StockSortArrow.Visibility = _sortBy == "Stock" ? Visibility.Visible : Visibility.Collapsed;
        CreatedSortArrow.Visibility = _sortBy == "Created" ? Visibility.Visible : Visibility.Collapsed;
    }

    private void SortHeader_Click(object sender, RoutedEventArgs e)
    {
        if (sender is not Button btn || btn.Tag is not string column) return;
        if (_sortBy == column) _sortAsc = !_sortAsc;
        else { _sortBy = column; _sortAsc = column == "Name"; }
        ApplySort();
    }

    private void ProductList_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        DeleteBtn.IsEnabled = ProductList.SelectedItem != null;
        if (ProductList.SelectedItem is ProductRow row)
            FooterHint.Text = $"Seçili: {row.Name} — {row.UnitPriceDisplay} — Stok: {row.StockQuantity} — düzenlemek için çift tıklayın";
    }

    private void ProductList_MouseDoubleClick(object sender, MouseButtonEventArgs e)
    {
        if (!AuthorizationService.CanManageProducts(CurrentUserService.Current?.Role))
            return;

        if (ProductList.SelectedItem is not ProductRow row) return;

        var owner = Window.GetWindow(this);
        var dialog = new EditProductWindow(row.Id) { Owner = owner };
        if (dialog.ShowDialog() == true)
            LoadProducts();
    }

    private void AddProduct_Click(object sender, RoutedEventArgs e)
    {
        if (!AuthorizationService.CanManageProducts(CurrentUserService.Current?.Role))
            return;

        var owner = Window.GetWindow(this);
        var dialog = new AddProductWindow { Owner = owner };
        if (dialog.ShowDialog() == true)
            LoadProducts();
    }

    private void Delete_Click(object sender, RoutedEventArgs e)
    {
        if (!AuthorizationService.CanManageProducts(CurrentUserService.Current?.Role))
            return;

        if (ProductList.SelectedItem is not ProductRow row) return;

        if (MessageBox.Show($"'{row.Name}' ürününü silmek istediğinize emin misiniz?",
                "Ürün sil", MessageBoxButton.YesNo, MessageBoxImage.Question) != MessageBoxResult.Yes)
            return;

        using var db = new AppDbContext();
        var entity = db.Products.FirstOrDefault(p => p.Id == row.Id);
        if (entity == null) return;
        db.Products.Remove(entity);
        db.SaveChanges();
        LoadProducts();
    }
}
