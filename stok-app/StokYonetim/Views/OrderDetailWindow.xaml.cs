using System.Globalization;
using System.Windows;
using Microsoft.EntityFrameworkCore;
using StokYonetim.Data;
using StokYonetim.Views.Pages;

namespace StokYonetim.Views;

public partial class OrderDetailWindow : Window
{
    public OrderDetailWindow(int orderId)
    {
        InitializeComponent();
        LoadOrder(orderId);
    }

    private void LoadOrder(int orderId)
    {
        using var db = new AppDbContext();
        var order = db.Orders.AsNoTracking().FirstOrDefault(o => o.Id == orderId);
        if (order == null)
        {
            MessageBox.Show("Sipariş bulunamadı.", "Hata", MessageBoxButton.OK, MessageBoxImage.Warning);
            Close();
            return;
        }

        var lines = db.OrderItems.AsNoTracking()
            .Where(i => i.OrderId == orderId)
            .Join(
                db.Products.AsNoTracking().Include(p => p.Category),
                i => i.ProductId,
                p => p.Id,
                (i, p) => new { i.Quantity, i.UnitPrice, p.Name, CategoryName = p.Category != null ? p.Category.Name : "" })
            .AsEnumerable()
            .Select(x => new OrderDetailLine
            {
                ProductName = x.Name,
                CategoryName = x.CategoryName,
                Quantity = x.Quantity,
                UnitPrice = x.UnitPrice
            })
            .ToList();

        var tr = CultureInfo.GetCultureInfo("tr-TR");
        var localDate = order.CreatedAt.ToLocalTime();

        CustomerTitle.Text = string.IsNullOrWhiteSpace(order.CustomerName) ? "Müşteri belirtilmedi" : order.CustomerName;
        OrderMetaText.Text = string.IsNullOrWhiteSpace(order.CustomerPhone)
            ? "Telefon belirtilmedi"
            : $"📞 {order.CustomerPhone}";
        OrderDateText.Text = localDate.ToString("dd.MM.yyyy HH:mm", tr);
        NotesText.Text = string.IsNullOrWhiteSpace(order.Notes) ? "—" : order.Notes;

        LinesList.ItemsSource = lines;

        var grandTotal = lines.Sum(l => l.LineTotal);
        GrandTotalText.Text = grandTotal.ToString("N2", tr) + " ₺";
    }

    private void Close_Click(object sender, RoutedEventArgs e) => Close();
}
