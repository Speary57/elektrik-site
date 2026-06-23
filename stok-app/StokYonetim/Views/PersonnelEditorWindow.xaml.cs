using System.Globalization;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using Microsoft.EntityFrameworkCore;
using StokYonetim.Data;
using StokYonetim.Helpers;
using StokYonetim.Models;

namespace StokYonetim.Views;

public partial class PersonnelEditorWindow : Window
{
    private readonly int? _personnelId;
    private readonly InputFormattingState _formatting = new();

    public PersonnelEditorWindow(int? personnelId = null)
    {
        _personnelId = personnelId;
        InitializeComponent();
        RoleCombo.ItemsSource = PersonnelRoles.All;
        IsActivePanel.Visibility = personnelId.HasValue ? Visibility.Visible : Visibility.Collapsed;
        TitleText.Text = personnelId.HasValue ? "Personeli düzenle" : "Yeni personel";
        SaveBtn.Content = personnelId.HasValue ? "Güncelle" : "Personel ekle";
        Title = personnelId.HasValue ? "Personeli Düzenle" : "Personel Ekle";

        PersonnelFormHelper.AttachFullNameBox(FullNameBox);
        PersonnelFormHelper.AttachPhoneBox(PhoneBox, _formatting);
        PersonnelFormHelper.AttachBirthDateBox(BirthDateBox, BirthDateBorder, BirthDateHint, BirthDateErrorText, _formatting);
        PersonnelFormHelper.AttachSalaryBox(SalaryBox);
        FullNameBox.KeyDown += (_, e) => { if (e.Key == Key.Enter) Save_Click(this, new RoutedEventArgs()); };

        Loaded += (_, _) => LoadData();
    }

    private void LoadData()
    {
        if (!_personnelId.HasValue) return;

        using var db = new AppDbContext();
        var person = db.Personnel.AsNoTracking().FirstOrDefault(p => p.Id == _personnelId.Value);
        if (person == null)
        {
            MessageBox.Show("Personel bulunamadı.", "Uyarı", MessageBoxButton.OK, MessageBoxImage.Warning);
            Close();
            return;
        }

        FullNameBox.Text = person.FullName;
        EmailBox.Text = person.Email;
        PersonnelFormHelper.SetPhoneText(PhoneBox, _formatting, person.Phone);
        PersonnelFormHelper.SetBirthDateText(BirthDateBox, BirthDateHint, BirthDateErrorText, BirthDateBorder, _formatting, person.BirthDate);
        SalaryBox.Text = person.Salary.ToString("0.##", CultureInfo.InvariantCulture);
        SetSelectedRole(person.Role);
        IsActiveCheck.IsChecked = person.IsActive;
    }

    private string? GetSelectedRole()
    {
        if (RoleCombo.SelectedIndex >= 0 && RoleCombo.SelectedIndex < PersonnelRoles.All.Length)
            return PersonnelRoles.All[RoleCombo.SelectedIndex];
        if (RoleCombo.SelectedItem is string role && PersonnelRoles.All.Contains(role))
            return role;
        return null;
    }

    private void SetSelectedRole(string? role)
    {
        if (string.IsNullOrWhiteSpace(role))
        {
            RoleCombo.SelectedIndex = -1;
            return;
        }
        var index = Array.IndexOf(PersonnelRoles.All, role);
        RoleCombo.SelectedIndex = index >= 0 ? index : -1;
    }

    private void Save_Click(object sender, RoutedEventArgs e)
    {
        var fullName = FullNameBox.Text.Trim();
        var email = EmailBox.Text.Trim();
        var phone = PhoneBox.Text.Trim();

        if (string.IsNullOrWhiteSpace(fullName))
        {
            MessageBox.Show("Ad soyad zorunludur.", "Uyarı", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        if (GetSelectedRole() is not { } role)
        {
            MessageBox.Show("Lütfen bir rol seçin.", "Uyarı", MessageBoxButton.OK, MessageBoxImage.Warning);
            RoleCombo.Focus();
            return;
        }

        if (!string.IsNullOrWhiteSpace(email) && !email.Contains('@'))
        {
            MessageBox.Show("Geçerli bir e-posta adresi girin.", "Uyarı", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        if (!string.IsNullOrWhiteSpace(phone))
        {
            var phoneDigits = PersonnelFormHelper.ExtractDigits(phone);
            if (phoneDigits.Length > 0 && phoneDigits.Length != 11)
            {
                MessageBox.Show("Telefon numarası 0XXX XXX XX XX formatında 11 haneli olmalıdır.", "Uyarı",
                    MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }
        }

        if (!PersonnelFormHelper.ValidateBirthDate(BirthDateBox.Text.Trim(), out var birthDate, out _))
        {
            PersonnelFormHelper.UpdateBirthDateValidation(BirthDateBox, BirthDateBorder, BirthDateHint, BirthDateErrorText);
            BirthDateBox.Focus();
            return;
        }

        if (!PersonnelFormHelper.TryParseSalary(SalaryBox.Text.Trim(), out var salary))
        {
            MessageBox.Show("Maaş için geçerli bir sayı girin.", "Uyarı", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        if (salary < 0)
        {
            MessageBox.Show("Maaş negatif olamaz.", "Uyarı", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        using var db = new AppDbContext();
        var now = DateTime.UtcNow;

        if (_personnelId.HasValue)
        {
            var entity = db.Personnel.FirstOrDefault(p => p.Id == _personnelId.Value);
            if (entity == null) return;

            entity.FullName = fullName;
            entity.Email = email;
            entity.Phone = phone;
            entity.BirthDate = birthDate;
            entity.Salary = salary;
            entity.Role = role;
            entity.IsActive = IsActiveCheck.IsChecked == true;
            entity.UpdatedAt = now;
        }
        else
        {
            db.Personnel.Add(new Personnel
            {
                FullName = fullName,
                Email = email,
                Phone = phone,
                BirthDate = birthDate,
                Salary = salary,
                Role = role,
                IsActive = true,
                CreatedAt = now,
                UpdatedAt = now
            });
        }

        db.SaveChanges();
        DialogResult = true;
        Close();
    }

    private void Cancel_Click(object sender, RoutedEventArgs e)
    {
        DialogResult = false;
        Close();
    }
}
