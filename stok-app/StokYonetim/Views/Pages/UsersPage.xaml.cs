using System.Globalization;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using Microsoft.EntityFrameworkCore;
using StokYonetim.Data;
using StokYonetim.Models;
using StokYonetim.Services;

namespace StokYonetim.Views.Pages;

public class UserRow
{
    public int Id { get; set; }
    public string Email { get; set; } = "";
    public string Role { get; set; } = "";
    public DateTime CreatedAtUtc { get; set; }
    public string CreatedAtDisplay => CreatedAtUtc.ToLocalTime().ToString("dd.MM.yyyy HH:mm", CultureInfo.GetCultureInfo("tr-TR"));
}

public partial class UsersPage : UserControl
{
    private List<UserRow> _rows = [];
    private string _sortBy = "Email";
    private bool _sortAsc = true;
    private int? _editingId;

    public UsersPage()
    {
        InitializeComponent();
        RoleCombo.ItemsSource = UserRoles.Assignable;
        Loaded += (_, _) => Refresh();
    }

    public void Refresh()
    {
        using var db = new AppDbContext();
        _rows = db.AppUsers.AsNoTracking()
            .Where(u => u.Role != UserRoles.Yonetici)
            .Select(u => new UserRow
            {
                Id = u.Id,
                Email = u.Email,
                Role = u.Role,
                CreatedAtUtc = u.CreatedAt
            })
            .ToList();

        CountBadge.Text = $"{_rows.Count} kullanıcı";
        ApplySort();
        EmptyText.Visibility = _rows.Count == 0 ? Visibility.Visible : Visibility.Collapsed;
    }

    private void ApplySort()
    {
        IEnumerable<UserRow> sorted = _sortBy switch
        {
            "Role" => _sortAsc
                ? _rows.OrderBy(r => r.Role).ThenBy(r => r.Email)
                : _rows.OrderByDescending(r => r.Role).ThenBy(r => r.Email),
            "Created" => _sortAsc
                ? _rows.OrderBy(r => r.CreatedAtUtc)
                : _rows.OrderByDescending(r => r.CreatedAtUtc),
            _ => _sortAsc
                ? _rows.OrderBy(r => r.Email, StringComparer.CurrentCultureIgnoreCase)
                : _rows.OrderByDescending(r => r.Email, StringComparer.CurrentCultureIgnoreCase)
        };

        UsersList.ItemsSource = sorted.ToList();
        UpdateSortArrows();
    }

    private void UpdateSortArrows()
    {
        EmailSortArrow.Visibility = _sortBy == "Email" ? Visibility.Visible : Visibility.Collapsed;
        RoleSortArrow.Visibility = _sortBy == "Role" ? Visibility.Visible : Visibility.Collapsed;
        CreatedSortArrow.Visibility = _sortBy == "Created" ? Visibility.Visible : Visibility.Collapsed;

        EmailSortArrow.Text = _sortBy == "Email" ? (_sortAsc ? "▲" : "▼") : "";
        RoleSortArrow.Text = _sortBy == "Role" ? (_sortAsc ? "▲" : "▼") : "";
        CreatedSortArrow.Text = _sortBy == "Created" ? (_sortAsc ? "▲" : "▼") : "";
    }

    private void SortHeader_Click(object sender, RoutedEventArgs e)
    {
        if (sender is not Button btn || btn.Tag is not string column) return;
        if (_sortBy == column) _sortAsc = !_sortAsc;
        else { _sortBy = column; _sortAsc = true; }
        ApplySort();
    }

    private void UsersList_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        DeleteBtn.IsEnabled = UsersList.SelectedItem != null;
        if (UsersList.SelectedItem is UserRow row)
            FooterHint.Text = $"Seçili: {row.Email}";
        else
            FooterHint.Text = "Düzenlemek için satıra çift tıklayın.";
    }

    private void UsersList_MouseDoubleClick(object sender, MouseButtonEventArgs e)
    {
        if (UsersList.SelectedItem is not UserRow row) return;
        LoadIntoForm(row);
    }

    private void LoadIntoForm(UserRow row)
    {
        _editingId = row.Id;
        FormTitle.Text = "Kullanıcıyı düzenle";
        SaveBtn.Content = "Güncelle";
        EmailBox.Text = row.Email;
        PasswordBox.Password = "";
        PasswordHint.Visibility = Visibility.Visible;
        RoleCombo.SelectedItem = UserRoles.Assignable.Contains(row.Role) ? row.Role : null;
    }

    private void Clear_Click(object sender, RoutedEventArgs e) => ResetForm();

    private void ResetForm()
    {
        _editingId = null;
        FormTitle.Text = "Yeni kullanıcı";
        SaveBtn.Content = "Kullanıcı ekle";
        EmailBox.Clear();
        PasswordBox.Password = "";
        PasswordHint.Visibility = Visibility.Collapsed;
        RoleCombo.SelectedIndex = -1;
        UsersList.SelectedItem = null;
    }

    private void Save_Click(object sender, RoutedEventArgs e)
    {
        var email = EmailBox.Text.Trim().ToLowerInvariant();
        var password = PasswordBox.Password;
        var role = RoleCombo.SelectedItem as string;

        if (string.IsNullOrWhiteSpace(email) || !email.Contains('@'))
        {
            MessageBox.Show("Geçerli bir e-posta adresi girin.", "Uyarı", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        if (string.IsNullOrWhiteSpace(role))
        {
            MessageBox.Show("Lütfen bir rol seçin.", "Uyarı", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        if (!_editingId.HasValue && string.IsNullOrWhiteSpace(password))
        {
            MessageBox.Show("Yeni kullanıcı için şifre zorunludur.", "Uyarı", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        using var db = new AppDbContext();
        var normalized = email.ToLowerInvariant();
        var duplicate = db.AppUsers.AsEnumerable()
            .Any(u => u.Id != (_editingId ?? -1) && u.Email.Trim().ToLowerInvariant() == normalized);

        if (duplicate)
        {
            MessageBox.Show("Bu e-posta adresi zaten kayıtlı.", "Uyarı", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        var now = DateTime.UtcNow;

        if (_editingId.HasValue)
        {
            var entity = db.AppUsers.FirstOrDefault(u => u.Id == _editingId.Value);
            if (entity == null || entity.Role == UserRoles.Yonetici) return;

            entity.Email = normalized;
            entity.Role = role;
            if (!string.IsNullOrWhiteSpace(password))
                entity.PasswordHash = PasswordHasher.Hash(password);
            entity.UpdatedAt = now;
        }
        else
        {
            db.AppUsers.Add(new AppUser
            {
                Email = normalized,
                PasswordHash = PasswordHasher.Hash(password),
                Role = role,
                CreatedAt = now,
                UpdatedAt = now
            });
        }

        db.SaveChanges();
        ResetForm();
        Refresh();
    }

    private void Delete_Click(object sender, RoutedEventArgs e)
    {
        if (UsersList.SelectedItem is not UserRow row) return;

        if (MessageBox.Show($"'{row.Email}' kullanıcısını silmek istediğinize emin misiniz?",
                "Kullanıcı sil", MessageBoxButton.YesNo, MessageBoxImage.Question) != MessageBoxResult.Yes)
            return;

        using var db = new AppDbContext();
        var entity = db.AppUsers.FirstOrDefault(u => u.Id == row.Id);
        if (entity == null || entity.Role == UserRoles.Yonetici) return;

        db.AppUsers.Remove(entity);
        db.SaveChanges();

        if (_editingId == row.Id) ResetForm();
        Refresh();
    }
}
