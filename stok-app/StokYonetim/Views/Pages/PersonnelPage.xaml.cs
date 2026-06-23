using System.Globalization;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using Microsoft.EntityFrameworkCore;
using StokYonetim.Data;
using StokYonetim.Services;
using StokYonetim.Views;

namespace StokYonetim.Views.Pages;

public class PersonnelRow
{
    public int Id { get; set; }
    public string FullName { get; set; } = "";
    public string Email { get; set; } = "";
    public string Phone { get; set; } = "";
    public DateTime? BirthDate { get; set; }
    public decimal Salary { get; set; }
    public string Role { get; set; } = "";
    public bool IsActive { get; set; }

    public string BirthDateDisplay => BirthDate?.ToString("dd/MM/yyyy") ?? "—";
    public string SalaryDisplay => Salary.ToString("N2", CultureInfo.GetCultureInfo("tr-TR")) + " ₺";
    public string ActiveDisplay => IsActive ? "Aktif" : "Pasif";
    public Brush ActiveBrush => IsActive
        ? new SolidColorBrush((Color)ColorConverter.ConvertFromString("#16A34A")!)
        : new SolidColorBrush((Color)ColorConverter.ConvertFromString("#94A3B8")!);
}

public partial class PersonnelPage : UserControl
{
    private List<PersonnelRow> _rows = [];
    private string _sortBy = "Name";
    private bool _sortAsc = true;

    public PersonnelPage()
    {
        InitializeComponent();
        Loaded += (_, _) => Refresh();
    }

    public void Refresh()
    {
        ApplyAccessMode();
        LoadPersonnel();
        UpdateScheduleHint();
    }

    public void ApplyAccessMode()
    {
        var role = CurrentUserService.Current?.Role;
        var canManage = AuthorizationService.CanManagePersonnel(role);
        var canPay = AuthorizationService.CanPayPersonnelSalary(role);

        AddPersonnelBtn.Visibility = canManage ? Visibility.Visible : Visibility.Collapsed;
        SalaryScheduleBtn.Visibility = canManage ? Visibility.Visible : Visibility.Collapsed;
        ScheduleHintText.Visibility = canManage ? Visibility.Visible : Visibility.Collapsed;
        DeleteBtn.Visibility = canManage ? Visibility.Visible : Visibility.Collapsed;
        PaySalaryBtn.Visibility = canPay ? Visibility.Visible : Visibility.Collapsed;
    }

    private void UpdateScheduleHint()
    {
        if (!AuthorizationService.CanManagePersonnel(CurrentUserService.Current?.Role))
            return;
        using var db = new AppDbContext();
        var day = SalaryScheduleService.GetPaymentDay(db);
        ScheduleHintText.Text = SalaryScheduleService.FormatPaymentDayInfo(day);
    }

    private void LoadPersonnel()
    {
        using var db = new AppDbContext();
        _rows = db.Personnel.AsNoTracking()
            .Select(p => new PersonnelRow
            {
                Id = p.Id,
                FullName = p.FullName,
                Email = p.Email,
                Phone = p.Phone,
                BirthDate = p.BirthDate,
                Salary = p.Salary,
                Role = p.Role,
                IsActive = p.IsActive
            })
            .ToList();

        CountBadge.Text = $"{_rows.Count} personel";
        ApplySort();
        EmptyText.Visibility = _rows.Count == 0 ? Visibility.Visible : Visibility.Collapsed;
        DeleteBtn.IsEnabled = false;
    }

    private void ApplySort()
    {
        IEnumerable<PersonnelRow> sorted = _sortBy switch
        {
            "Email" => _sortAsc
                ? _rows.OrderBy(r => r.Email).ThenBy(r => r.FullName)
                : _rows.OrderByDescending(r => r.Email).ThenBy(r => r.FullName),
            "Role" => _sortAsc
                ? _rows.OrderBy(r => r.Role).ThenBy(r => r.FullName)
                : _rows.OrderByDescending(r => r.Role).ThenBy(r => r.FullName),
            "Active" => _sortAsc
                ? _rows.OrderBy(r => r.IsActive).ThenBy(r => r.FullName)
                : _rows.OrderByDescending(r => r.IsActive).ThenBy(r => r.FullName),
            "Phone" => _sortAsc
                ? _rows.OrderBy(r => r.Phone).ThenBy(r => r.FullName)
                : _rows.OrderByDescending(r => r.Phone).ThenBy(r => r.FullName),
            "Birth" => _sortAsc
                ? _rows.OrderBy(r => r.BirthDate ?? DateTime.MaxValue).ThenBy(r => r.FullName)
                : _rows.OrderByDescending(r => r.BirthDate ?? DateTime.MinValue).ThenBy(r => r.FullName),
            "Salary" => _sortAsc
                ? _rows.OrderBy(r => r.Salary).ThenBy(r => r.FullName)
                : _rows.OrderByDescending(r => r.Salary).ThenBy(r => r.FullName),
            _ => _sortAsc
                ? _rows.OrderBy(r => r.FullName, StringComparer.CurrentCultureIgnoreCase)
                : _rows.OrderByDescending(r => r.FullName, StringComparer.CurrentCultureIgnoreCase)
        };

        PersonnelList.ItemsSource = sorted.ToList();
        UpdateSortArrows();
    }

    private void UpdateSortArrows()
    {
        NameSortArrow.Visibility = _sortBy == "Name" ? Visibility.Visible : Visibility.Collapsed;
        EmailSortArrow.Visibility = _sortBy == "Email" ? Visibility.Visible : Visibility.Collapsed;
        RoleSortArrow.Visibility = _sortBy == "Role" ? Visibility.Visible : Visibility.Collapsed;
        ActiveSortArrow.Visibility = _sortBy == "Active" ? Visibility.Visible : Visibility.Collapsed;
        PhoneSortArrow.Visibility = _sortBy == "Phone" ? Visibility.Visible : Visibility.Collapsed;
        BirthSortArrow.Visibility = _sortBy == "Birth" ? Visibility.Visible : Visibility.Collapsed;
        SalarySortArrow.Visibility = _sortBy == "Salary" ? Visibility.Visible : Visibility.Collapsed;

        NameSortArrow.Text = _sortBy == "Name" ? (_sortAsc ? "▲" : "▼") : "";
        EmailSortArrow.Text = _sortBy == "Email" ? (_sortAsc ? "▲" : "▼") : "";
        RoleSortArrow.Text = _sortBy == "Role" ? (_sortAsc ? "▲" : "▼") : "";
        ActiveSortArrow.Text = _sortBy == "Active" ? (_sortAsc ? "▲" : "▼") : "";
        PhoneSortArrow.Text = _sortBy == "Phone" ? (_sortAsc ? "▲" : "▼") : "";
        BirthSortArrow.Text = _sortBy == "Birth" ? (_sortAsc ? "▲" : "▼") : "";
        SalarySortArrow.Text = _sortBy == "Salary" ? (_sortAsc ? "▲" : "▼") : "";
    }

    private void SortHeader_Click(object sender, RoutedEventArgs e)
    {
        if (sender is not Button btn || btn.Tag is not string column) return;
        if (_sortBy == column) _sortAsc = !_sortAsc;
        else { _sortBy = column; _sortAsc = true; }
        ApplySort();
    }

    private void PersonnelList_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        var canManage = AuthorizationService.CanManagePersonnel(CurrentUserService.Current?.Role);
        DeleteBtn.IsEnabled = canManage && PersonnelList.SelectedItem != null;
        if (PersonnelList.SelectedItem is PersonnelRow row)
        {
            FooterHint.Text = canManage
                ? $"Seçili: {row.FullName} ({row.ActiveDisplay}) — düzenlemek için çift tıklayın"
                : $"Seçili: {row.FullName} ({row.ActiveDisplay})";
        }
        else
        {
            FooterHint.Text = canManage
                ? "Düzenlemek için satıra çift tıklayın."
                : "Personel listesini görüntülüyorsunuz.";
        }
    }

    private void PersonnelList_MouseDoubleClick(object sender, MouseButtonEventArgs e)
    {
        if (!AuthorizationService.CanManagePersonnel(CurrentUserService.Current?.Role))
            return;

        if (PersonnelList.SelectedItem is not PersonnelRow row) return;

        var owner = Window.GetWindow(this);
        var dialog = new PersonnelEditorWindow(row.Id) { Owner = owner };
        if (dialog.ShowDialog() == true)
            LoadPersonnel();
    }

    private void AddPersonnel_Click(object sender, RoutedEventArgs e)
    {
        var owner = Window.GetWindow(this);
        var dialog = new PersonnelEditorWindow { Owner = owner };
        if (dialog.ShowDialog() == true)
            LoadPersonnel();
    }

    private void PaySalary_Click(object sender, RoutedEventArgs e)
    {
        var owner = Window.GetWindow(this);
        var dialog = new PersonnelPayWindow { Owner = owner };
        dialog.ShowDialog();
    }

    private void SalarySchedule_Click(object sender, RoutedEventArgs e)
    {
        var owner = Window.GetWindow(this);
        var dialog = new SalaryScheduleWindow { Owner = owner };
        if (dialog.ShowDialog() == true)
            UpdateScheduleHint();
    }

    private void Delete_Click(object sender, RoutedEventArgs e)
    {
        if (!AuthorizationService.CanManagePersonnel(CurrentUserService.Current?.Role))
            return;

        if (PersonnelList.SelectedItem is not PersonnelRow row) return;

        if (MessageBox.Show($"'{row.FullName}' personel kaydını silmek istediğinize emin misiniz?",
                "Personel sil", MessageBoxButton.YesNo, MessageBoxImage.Question) != MessageBoxResult.Yes)
            return;

        using var db = new AppDbContext();
        var entity = db.Personnel.FirstOrDefault(p => p.Id == row.Id);
        if (entity == null) return;

        db.Personnel.Remove(entity);
        db.SaveChanges();
        LoadPersonnel();
    }
}
