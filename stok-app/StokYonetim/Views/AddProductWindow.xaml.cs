using System.Globalization;
using System.Text.RegularExpressions;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using Microsoft.EntityFrameworkCore;
using StokYonetim.Data;
using StokYonetim.Models;

namespace StokYonetim.Views;

public partial class AddProductWindow : Window
{
    public AddProductWindow()
    {
        InitializeComponent();
        Loaded += (_, _) => LoadCategories();
        PriceBox.PreviewTextInput += Price_PreviewTextInput;
        DataObject.AddPastingHandler(PriceBox, Price_OnPaste);
        StockBox.PreviewTextInput += DigitsOnly_PreviewTextInput;
        DataObject.AddPastingHandler(StockBox, DigitsOnly_OnPaste);
        NameBox.KeyDown += (_, e) => { if (e.Key == Key.Enter) Save_Click(this, new RoutedEventArgs()); };
    }

    private void LoadCategories()
    {
        using var db = new AppDbContext();
        var categories = db.Categories.AsNoTracking().OrderBy(c => c.Name).ToList();
        CategoryCombo.ItemsSource = categories;
        if (categories.Count > 0)
            CategoryCombo.SelectedIndex = 0;
        else
            ShowError("Ürün eklemek için önce bir kategori oluşturun.");
    }

    private void Save_Click(object sender, RoutedEventArgs e)
    {
        HideError();

        if (CategoryCombo.SelectedItem is not Category cat)
        {
            ShowError("Lütfen bir kategori seçin.");
            return;
        }

        var name = NameBox.Text.Trim();
        if (string.IsNullOrWhiteSpace(name))
        {
            ShowError("Ürün adı boş olamaz.");
            NameBox.Focus();
            return;
        }

        if (!TryParsePrice(PriceBox.Text.Trim(), out var unitPrice) || unitPrice < 0)
        {
            ShowError("Geçerli bir birim fiyat girin.");
            PriceBox.Focus();
            return;
        }

        if (!int.TryParse(StockBox.Text.Trim(), out var stock) || stock < 0)
        {
            ShowError("Stok adedi 0 veya üzeri bir tam sayı olmalıdır.");
            StockBox.Focus();
            return;
        }

        using var db = new AppDbContext();
        if (db.Products.Any(p => p.CategoryId == cat.Id && p.Name == name))
        {
            ShowError("Bu kategoride aynı isimde ürün zaten var.");
            return;
        }

        var now = DateTime.UtcNow;
        db.Products.Add(new Product
        {
            Name = name,
            CategoryId = cat.Id,
            UnitPrice = unitPrice,
            StockQuantity = stock,
            CreatedAt = now,
            UpdatedAt = now
        });
        db.SaveChanges();

        DialogResult = true;
        Close();
    }

    private void Cancel_Click(object sender, RoutedEventArgs e)
    {
        DialogResult = false;
        Close();
    }

    private void ShowError(string message)
    {
        ErrorText.Text = message;
        ErrorText.Visibility = Visibility.Visible;
    }

    private void HideError() => ErrorText.Visibility = Visibility.Collapsed;

    private static bool TryParsePrice(string input, out decimal price)
    {
        price = 0;
        if (string.IsNullOrWhiteSpace(input)) return false;
        var normalized = input.Replace("₺", "").Trim().Replace(',', '.');
        return decimal.TryParse(normalized, NumberStyles.Number, CultureInfo.InvariantCulture, out price);
    }

    private static void DigitsOnly_PreviewTextInput(object sender, TextCompositionEventArgs e) =>
        e.Handled = !Regex.IsMatch(e.Text, @"^\d$");

    private static void DigitsOnly_OnPaste(object sender, DataObjectPastingEventArgs e)
    {
        if (!e.DataObject.GetDataPresent(typeof(string))) return;
        var text = e.DataObject.GetData(typeof(string)) as string ?? "";
        if (text.Any(c => !char.IsDigit(c))) e.CancelCommand();
    }

    private static void Price_PreviewTextInput(object sender, TextCompositionEventArgs e) =>
        e.Handled = !Regex.IsMatch(e.Text, @"^[\d,.\s]$");

    private static void Price_OnPaste(object sender, DataObjectPastingEventArgs e)
    {
        if (!e.DataObject.GetDataPresent(typeof(string))) return;
        var text = e.DataObject.GetData(typeof(string)) as string ?? "";
        if (text.Any(c => !char.IsDigit(c) && c is not ',' and not '.' and not ' ')) e.CancelCommand();
    }
}
