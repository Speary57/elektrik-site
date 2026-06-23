using System.Globalization;
using System.Text.RegularExpressions;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using Microsoft.EntityFrameworkCore;
using StokYonetim.Data;
using StokYonetim.Helpers;
using StokYonetim.Models;
using StokYonetim.Services;

namespace StokYonetim.Views.Pages;

public partial class OrderAddPage : UserControl
{
    private readonly List<OrderLineDraft> _draftLines = [];
    private static readonly CultureInfo TrCulture = CultureInfo.GetCultureInfo("tr-TR");

    public OrderAddPage()
    {
        InitializeComponent();
        Loaded += (_, _) => Refresh();
        PhoneInputHelper.Attach(CustomerPhoneBox);
        QuantityBox.PreviewTextInput += DigitsOnly_PreviewTextInput;
    }

    public void Refresh()
    {
        LoadProducts();
        RefreshDraftList();
    }

    private void LoadProducts()
    {
        using var db = new AppDbContext();
        var products = db.Products.AsNoTracking()
            .Include(p => p.Category)
            .OrderBy(p => p.Category!.Name)
            .ThenBy(p => p.Name)
            .Select(p => new ProductPickerItem
            {
                Id = p.Id,
                Name = p.Name,
                CategoryName = p.Category!.Name,
                UnitPrice = p.UnitPrice
            })
            .ToList();

        ProductCombo.ItemsSource = products;
        if (products.Count > 0)
            ProductCombo.SelectedIndex = 0;
        else
            UnitPriceBox.Clear();

        UpdateUnitPriceFromSelection();
    }

    private void ProductCombo_SelectionChanged(object sender, SelectionChangedEventArgs e) =>
        UpdateUnitPriceFromSelection();

    private void UpdateUnitPriceFromSelection()
    {
        if (ProductCombo.SelectedItem is ProductPickerItem product)
            UnitPriceBox.Text = product.UnitPrice.ToString("N2", TrCulture);
        else
            UnitPriceBox.Clear();
    }

    private void AddLine_Click(object sender, RoutedEventArgs e)
    {
        if (ProductCombo.SelectedItem is not ProductPickerItem product)
        {
            MessageBox.Show("Lütfen bir ürün seçin.", "Uyarı", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        if (!int.TryParse(QuantityBox.Text.Trim(), out var quantity) || quantity < 1)
        {
            MessageBox.Show("Geçerli bir miktar girin (1 veya üzeri).", "Uyarı", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        var unitPrice = product.UnitPrice;

        var existing = _draftLines.FirstOrDefault(l => l.ProductId == product.Id);
        if (existing != null)
        {
            existing.Quantity += quantity;
            existing.UnitPrice = unitPrice;
        }
        else
        {
            _draftLines.Add(new OrderLineDraft
            {
                ProductId = product.Id,
                ProductName = product.Name,
                CategoryName = product.CategoryName,
                Quantity = quantity,
                UnitPrice = unitPrice
            });
        }

        QuantityBox.Text = "1";
        RefreshDraftList();
    }

    private void RemoveLine_Click(object sender, RoutedEventArgs e)
    {
        if (sender is not Button btn || btn.Tag is not int productId) return;
        _draftLines.RemoveAll(l => l.ProductId == productId);
        RefreshDraftList();
    }

    private void RefreshDraftList()
    {
        DraftLinesList.ItemsSource = null;
        DraftLinesList.ItemsSource = _draftLines.ToList();
        DraftEmptyText.Visibility = _draftLines.Count == 0 ? Visibility.Visible : Visibility.Collapsed;

        var total = _draftLines.Sum(l => l.LineTotal);
        DraftTotalText.Text = total.ToString("N2", TrCulture) + " ₺";
    }

    private void Clear_Click(object sender, RoutedEventArgs e) => ResetForm();

    private void ResetForm()
    {
        CustomerNameBox.Clear();
        CustomerPhoneBox.Clear();
        NotesBox.Clear();
        QuantityBox.Text = "1";
        _draftLines.Clear();
        LoadProducts();
        RefreshDraftList();
    }

    private void Save_Click(object sender, RoutedEventArgs e)
    {
        if (_draftLines.Count == 0)
        {
            MessageBox.Show("Siparişe en az bir ürün ekleyin.", "Uyarı", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        var phone = CustomerPhoneBox.Text.Trim();
        if (!string.IsNullOrWhiteSpace(phone))
        {
            var digits = PhoneInputHelper.ExtractDigits(phone);
            if (digits.Length > 0 && digits.Length != 11)
            {
                MessageBox.Show("Telefon numarası 0XXX XXX XX XX formatında 11 haneli olmalıdır.", "Uyarı",
                    MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }
        }

        var now = DateTime.UtcNow;
        using var db = new AppDbContext();
        using var transaction = db.Database.BeginTransaction();

        try
        {
            var productIds = _draftLines.Select(l => l.ProductId).Distinct().ToList();
            var products = db.Products
                .Where(p => productIds.Contains(p.Id))
                .ToDictionary(p => p.Id);

            foreach (var line in _draftLines)
            {
                if (!products.TryGetValue(line.ProductId, out var product))
                {
                    MessageBox.Show($"'{line.ProductName}' ürünü bulunamadı.", "Uyarı",
                        MessageBoxButton.OK, MessageBoxImage.Warning);
                    return;
                }

                if (product.StockQuantity < line.Quantity)
                {
                    MessageBox.Show(
                        $"'{line.ProductName}' için yeterli stok yok.\nMevcut: {product.StockQuantity} adet, sipariş: {line.Quantity} adet.",
                        "Stok yetersiz", MessageBoxButton.OK, MessageBoxImage.Warning);
                    return;
                }
            }

            var order = new Order
            {
                CustomerName = CustomerNameBox.Text.Trim(),
                CustomerPhone = phone,
                Notes = NotesBox.Text.Trim(),
                CreatedAt = now,
                UpdatedAt = now
            };

            db.Orders.Add(order);
            db.SaveChanges();

            foreach (var line in _draftLines)
            {
                db.OrderItems.Add(new OrderItem
                {
                    OrderId = order.Id,
                    ProductId = line.ProductId,
                    Quantity = line.Quantity,
                    UnitPrice = line.UnitPrice
                });

                var product = products[line.ProductId];
                product.StockQuantity -= line.Quantity;
                product.UpdatedAt = now;
            }

            var orderTotal = _draftLines.Sum(l => l.LineTotal);
            var customerLabel = string.IsNullOrWhiteSpace(order.CustomerName) ? "Müşteri belirtilmedi" : order.CustomerName;
            FinanceLedgerService.RecordOrderIncome(db, order.Id, orderTotal, customerLabel);

            db.SaveChanges();
            transaction.Commit();
        }
        catch (Exception ex)
        {
            transaction.Rollback();
            MessageBox.Show($"Sipariş kaydedilemedi: {ex.Message}", "Hata",
                MessageBoxButton.OK, MessageBoxImage.Error);
            return;
        }

        ResetForm();
        MessageBox.Show("Sipariş kaydedildi. Siparişler bölümünden görüntüleyebilirsiniz.",
            "Başarılı", MessageBoxButton.OK, MessageBoxImage.Information);
    }

    private static void DigitsOnly_PreviewTextInput(object sender, TextCompositionEventArgs e) =>
        e.Handled = !Regex.IsMatch(e.Text, @"^\d$");
}
