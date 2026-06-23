using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using Microsoft.EntityFrameworkCore;
using StokYonetim.Data;
using StokYonetim.Models;

namespace StokYonetim.Views.Pages;

public class CategoryRow
{
    public int Id { get; set; }
    public string Name { get; set; } = "";
    public int ProductCount { get; set; }
}

public partial class CategoriesPage : UserControl
{
    private List<CategoryRow> _rows = [];
    private string _sortBy = "Name";
    private bool _sortAsc = true;

    public CategoriesPage()
    {
        InitializeComponent();
        Loaded += (_, _) => Refresh();
    }

    public void Refresh()
    {
        using var db = new AppDbContext();
        _rows = db.Categories.AsNoTracking()
            .Select(c => new CategoryRow
            {
                Id = c.Id,
                Name = c.Name,
                ProductCount = c.Products.Count
            })
            .ToList();

        CountBadge.Text = $"{_rows.Count} kategori";
        ApplySort();
        EmptyText.Visibility = _rows.Count == 0 ? Visibility.Visible : Visibility.Collapsed;
        DeleteBtn.IsEnabled = CategoryList.SelectedItem != null;
    }

    private void ApplySort()
    {
        IEnumerable<CategoryRow> sorted = _sortBy switch
        {
            "Count" => _sortAsc
                ? _rows.OrderBy(r => r.ProductCount).ThenBy(r => r.Name)
                : _rows.OrderByDescending(r => r.ProductCount).ThenBy(r => r.Name),
            _ => _sortAsc
                ? _rows.OrderBy(r => r.Name, StringComparer.CurrentCultureIgnoreCase)
                : _rows.OrderByDescending(r => r.Name, StringComparer.CurrentCultureIgnoreCase)
        };

        CategoryList.ItemsSource = sorted.ToList();
        UpdateSortArrows();
    }

    private void UpdateSortArrows()
    {
        NameSortArrow.Text = _sortBy == "Name" ? (_sortAsc ? "▲" : "▼") : "";
        CountSortArrow.Text = _sortBy == "Count" ? (_sortAsc ? "▲" : "▼") : "";
        NameSortArrow.Visibility = _sortBy == "Name" ? Visibility.Visible : Visibility.Collapsed;
        CountSortArrow.Visibility = _sortBy == "Count" ? Visibility.Visible : Visibility.Collapsed;
    }

    private void SortHeader_Click(object sender, RoutedEventArgs e)
    {
        if (sender is not Button btn || btn.Tag is not string column) return;
        if (_sortBy == column) _sortAsc = !_sortAsc;
        else { _sortBy = column; _sortAsc = true; }
        ApplySort();
    }

    private void Add_Click(object sender, RoutedEventArgs e) => TryAdd();

    private void NameBox_KeyDown(object sender, KeyEventArgs e)
    {
        if (e.Key == Key.Enter) TryAdd();
    }

    private void TryAdd()
    {
        var name = NameBox.Text.Trim();
        if (string.IsNullOrWhiteSpace(name))
        {
            MessageBox.Show("Kategori adı boş olamaz.", "Uyarı", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        using var db = new AppDbContext();
        if (db.Categories.Any(c => c.Name == name))
        {
            MessageBox.Show("Bu isimde bir kategori zaten var.", "Uyarı", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        db.Categories.Add(new Category { Name = name, CreatedAt = DateTime.UtcNow });
        db.SaveChanges();
        NameBox.Clear();
        Refresh();
    }

    private void CategoryList_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        DeleteBtn.IsEnabled = CategoryList.SelectedItem != null;
        if (CategoryList.SelectedItem is CategoryRow row)
            FooterHint.Text = $"Seçili: {row.Name} ({row.ProductCount} ürün)";
        else
            FooterHint.Text = "Sıralamak için sütun başlığına tıklayın.";
    }

    private void Delete_Click(object sender, RoutedEventArgs e)
    {
        if (CategoryList.SelectedItem is not CategoryRow cat) return;

        using var db = new AppDbContext();
        var entity = db.Categories.Include(c => c.Products).FirstOrDefault(c => c.Id == cat.Id);
        if (entity == null) return;

        var count = entity.Products.Count;
        var msg = count > 0
            ? $"'{entity.Name}' kategorisini silmek istediğinize emin misiniz?\n\nBu kategorideki {count} ürün de silinecek."
            : $"'{entity.Name}' kategorisini silmek istediğinize emin misiniz?";

        if (MessageBox.Show(msg, "Kategori sil", MessageBoxButton.YesNo, MessageBoxImage.Question) != MessageBoxResult.Yes)
            return;

        db.Categories.Remove(entity);
        db.SaveChanges();
        Refresh();
    }
}
