using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using Microsoft.EntityFrameworkCore;
using StokYonetim.Data;
using StokYonetim.Services;
using StokYonetim.Views;

namespace StokYonetim.Views.Pages;

public partial class OrdersListPage : UserControl
{
    private List<OrderRow> _rows = [];
    private string _sortBy = "Date";
    private bool _sortAsc;

    public OrdersListPage()
    {
        InitializeComponent();
        _sortAsc = false;
        Loaded += (_, _) => Refresh();
    }

    public void Refresh()
    {
        ApplyAccessMode();
        LoadOrders();
    }

    public void ApplyAccessMode()
    {
        DeleteBtn.Visibility = AuthorizationService.CanManageOrders(CurrentUserService.Current?.Role)
            ? Visibility.Visible
            : Visibility.Collapsed;
    }

    private void LoadOrders()
    {
        using var db = new AppDbContext();
        var orders = db.Orders.AsNoTracking().ToList();
        var allItems = db.OrderItems.AsNoTracking().ToList();
        var productNames = db.Products.AsNoTracking().ToDictionary(p => p.Id, p => p.Name);

        _rows = orders.Select(o =>
        {
            var items = allItems.Where(i => i.OrderId == o.Id).ToList();
            return new OrderRow
            {
                Id = o.Id,
                CustomerName = string.IsNullOrWhiteSpace(o.CustomerName) ? "—" : o.CustomerName,
                CustomerPhone = string.IsNullOrWhiteSpace(o.CustomerPhone) ? "—" : o.CustomerPhone,
                Notes = o.Notes,
                CreatedAtUtc = o.CreatedAt,
                ItemCount = items.Count,
                TotalAmount = items.Sum(i => i.Quantity * i.UnitPrice),
                ItemsSummary = items.Count == 0
                    ? "—"
                    : string.Join(", ", items.Select(i =>
                        $"{productNames.GetValueOrDefault(i.ProductId, "?")} x{i.Quantity}"))
            };
        }).ToList();

        CountBadge.Text = $"{_rows.Count} sipariş";
        ApplySort();
        EmptyText.Visibility = _rows.Count == 0 ? Visibility.Visible : Visibility.Collapsed;
    }

    private void ApplySort()
    {
        IEnumerable<OrderRow> sorted = _sortBy switch
        {
            "Customer" => _sortAsc
                ? _rows.OrderBy(r => r.CustomerName).ThenByDescending(r => r.CreatedAtUtc)
                : _rows.OrderByDescending(r => r.CustomerName).ThenByDescending(r => r.CreatedAtUtc),
            "Phone" => _sortAsc
                ? _rows.OrderBy(r => r.CustomerPhone).ThenByDescending(r => r.CreatedAtUtc)
                : _rows.OrderByDescending(r => r.CustomerPhone).ThenByDescending(r => r.CreatedAtUtc),
            "Count" => _sortAsc
                ? _rows.OrderBy(r => r.ItemCount).ThenByDescending(r => r.CreatedAtUtc)
                : _rows.OrderByDescending(r => r.ItemCount).ThenByDescending(r => r.CreatedAtUtc),
            "Total" => _sortAsc
                ? _rows.OrderBy(r => r.TotalAmount).ThenByDescending(r => r.CreatedAtUtc)
                : _rows.OrderByDescending(r => r.TotalAmount).ThenByDescending(r => r.CreatedAtUtc),
            _ => _sortAsc
                ? _rows.OrderBy(r => r.CreatedAtUtc)
                : _rows.OrderByDescending(r => r.CreatedAtUtc)
        };

        OrdersList.ItemsSource = sorted.ToList();
        UpdateSortArrows();
    }

    private void UpdateSortArrows()
    {
        DateSortArrow.Visibility = _sortBy == "Date" ? Visibility.Visible : Visibility.Collapsed;
        CustomerSortArrow.Visibility = _sortBy == "Customer" ? Visibility.Visible : Visibility.Collapsed;
        PhoneSortArrow.Visibility = _sortBy == "Phone" ? Visibility.Visible : Visibility.Collapsed;
        CountSortArrow.Visibility = _sortBy == "Count" ? Visibility.Visible : Visibility.Collapsed;
        TotalSortArrow.Visibility = _sortBy == "Total" ? Visibility.Visible : Visibility.Collapsed;

        DateSortArrow.Text = _sortBy == "Date" ? (_sortAsc ? "▲" : "▼") : "";
        CustomerSortArrow.Text = _sortBy == "Customer" ? (_sortAsc ? "▲" : "▼") : "";
        PhoneSortArrow.Text = _sortBy == "Phone" ? (_sortAsc ? "▲" : "▼") : "";
        CountSortArrow.Text = _sortBy == "Count" ? (_sortAsc ? "▲" : "▼") : "";
        TotalSortArrow.Text = _sortBy == "Total" ? (_sortAsc ? "▲" : "▼") : "";
    }

    private void SortHeader_Click(object sender, RoutedEventArgs e)
    {
        if (sender is not Button btn || btn.Tag is not string column) return;
        if (_sortBy == column) _sortAsc = !_sortAsc;
        else { _sortBy = column; _sortAsc = column is "Customer" or "Phone"; }
        ApplySort();
    }

    private void OrdersList_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        DeleteBtn.IsEnabled = OrdersList.SelectedItem != null;
        if (OrdersList.SelectedItem is OrderRow row)
            FooterHint.Text = $"Seçili: {row.CustomerName} — detay için çift tıklayın";
        else
            FooterHint.Text = "Detay için siparişe çift tıklayın.";
    }

    private void OrdersList_MouseDoubleClick(object sender, MouseButtonEventArgs e)
    {
        if (OrdersList.SelectedItem is not OrderRow row) return;

        var window = new OrderDetailWindow(row.Id) { Owner = Window.GetWindow(this) };
        window.ShowDialog();
    }

    private void Delete_Click(object sender, RoutedEventArgs e)
    {
        if (!AuthorizationService.CanManageOrders(CurrentUserService.Current?.Role))
            return;

        if (OrdersList.SelectedItem is not OrderRow row) return;

        if (MessageBox.Show(
                $"'{row.CustomerName}' siparişini silmek istediğinize emin misiniz?\nSiparişteki ürün miktarları stoka geri eklenecektir.",
                "Sipariş sil", MessageBoxButton.YesNo, MessageBoxImage.Question) != MessageBoxResult.Yes)
            return;

        using var db = new AppDbContext();
        using var transaction = db.Database.BeginTransaction();

        try
        {
            var order = db.Orders.Include(o => o.Items).FirstOrDefault(o => o.Id == row.Id);
            if (order == null) return;

            var now = DateTime.UtcNow;
            var productIds = order.Items.Select(i => i.ProductId).Distinct().ToList();
            var products = db.Products
                .Where(p => productIds.Contains(p.Id))
                .ToDictionary(p => p.Id);

            foreach (var item in order.Items)
            {
                if (!products.TryGetValue(item.ProductId, out var product)) continue;
                product.StockQuantity += item.Quantity;
                product.UpdatedAt = now;
            }

            var orderTotal = order.Items.Sum(i => i.Quantity * i.UnitPrice);
            var customerLabel = string.IsNullOrWhiteSpace(order.CustomerName) ? "—" : order.CustomerName;
            FinanceLedgerService.RecordOrderCancellation(db, order.Id, orderTotal, customerLabel);

            db.Orders.Remove(order);
            db.SaveChanges();
            transaction.Commit();
        }
        catch (Exception ex)
        {
            transaction.Rollback();
            MessageBox.Show($"Sipariş silinemedi: {ex.Message}", "Hata",
                MessageBoxButton.OK, MessageBoxImage.Error);
            return;
        }

        LoadOrders();
    }
}
