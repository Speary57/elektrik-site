using System.Globalization;
using System.Windows;
using System.Windows.Controls;
using Microsoft.EntityFrameworkCore;
using StokYonetim.Data;
using StokYonetim.Helpers;
using StokYonetim.Models;
using StokYonetim.Services;

namespace StokYonetim.Views;

public class PersonnelPayPickerItem
{
    public int Id { get; set; }
    public string FullName { get; set; } = "";
    public decimal Salary { get; set; }

    public string DisplayName =>
        $"{FullName} — {Salary.ToString("N2", CultureInfo.GetCultureInfo("tr-TR"))} ₺";
}

public partial class PersonnelPayWindow : Window
{
    private static readonly CultureInfo TrCulture = CultureInfo.GetCultureInfo("tr-TR");

    public PersonnelPayWindow()
    {
        InitializeComponent();
        PaymentTypeCombo.ItemsSource = PersonnelPaymentTypes.All;
        PersonnelFormHelper.AttachSalaryBox(AmountBox);
        Loaded += (_, _) => LoadPersonnel();
    }

    private void LoadPersonnel()
    {
        using var db = new AppDbContext();
        var personnel = db.Personnel.AsNoTracking()
            .OrderBy(p => p.FullName)
            .Select(p => new PersonnelPayPickerItem
            {
                Id = p.Id,
                FullName = p.FullName,
                Salary = p.Salary
            })
            .ToList();

        PersonnelCombo.ItemsSource = personnel;
        if (personnel.Count > 0)
            PersonnelCombo.SelectedIndex = 0;
        else
            ShowError("Ödeme yapılacak personel bulunamadı.");

        PaymentTypeCombo.SelectedIndex = 0;
        UpdateAmountField();
    }

    private void PersonnelCombo_SelectionChanged(object sender, SelectionChangedEventArgs e) =>
        UpdateAmountField();

    private void PaymentTypeCombo_SelectionChanged(object sender, SelectionChangedEventArgs e) =>
        UpdateAmountField();

    private string? _lastPaymentType;

    private void UpdateAmountField()
    {
        HideError();
        var paymentType = PaymentTypeCombo.SelectedItem as string;

        if (paymentType == PersonnelPaymentTypes.Salary &&
            PersonnelCombo.SelectedItem is PersonnelPayPickerItem person)
        {
            AmountBox.Text = person.Salary.ToString("N2", TrCulture);
            AmountBox.IsReadOnly = true;
            AmountBox.Background = new System.Windows.Media.SolidColorBrush(
                (System.Windows.Media.Color)System.Windows.Media.ColorConverter.ConvertFromString("#F1F5F9")!);

            using var db = new AppDbContext();
            if (SalaryScheduleService.HasSalaryPaidThisMonth(db, person.Id))
                ShowError("Bu personelin maaşı bu ay zaten ödenmiş.");
        }
        else
        {
            AmountBox.IsReadOnly = false;
            AmountBox.Background = System.Windows.Media.Brushes.White;
            if (_lastPaymentType == PersonnelPaymentTypes.Salary)
                AmountBox.Clear();
        }

        _lastPaymentType = paymentType;
    }

    private void Save_Click(object sender, RoutedEventArgs e)
    {
        HideError();

        if (PersonnelCombo.SelectedItem is not PersonnelPayPickerItem person)
        {
            ShowError("Lütfen bir personel seçin.");
            return;
        }

        if (PaymentTypeCombo.SelectedItem is not string paymentType)
        {
            ShowError("Lütfen ödeme türü seçin.");
            return;
        }

        decimal amount;
        if (paymentType == PersonnelPaymentTypes.Salary)
        {
            amount = person.Salary;
            if (amount <= 0)
            {
                ShowError("Seçili personelin tanımlı maaşı yok veya geçersiz.");
                return;
            }

            using (var checkDb = new AppDbContext())
            {
                if (SalaryScheduleService.HasSalaryPaidThisMonth(checkDb, person.Id))
                {
                    ShowError("Bu personelin maaşı bu ay zaten ödenmiş.");
                    return;
                }
            }
        }
        else if (!PersonnelFormHelper.TryParseSalary(AmountBox.Text.Trim(), out amount) || amount <= 0)
        {
            ShowError("Geçerli bir miktar girin.");
            AmountBox.Focus();
            return;
        }

        using var db = new AppDbContext();
        var payment = new PersonnelPayment
        {
            PersonnelId = person.Id,
            PaymentType = paymentType,
            Amount = amount,
            CreatedAt = DateTime.UtcNow
        };
        db.PersonnelPayments.Add(payment);
        db.SaveChanges();
        FinanceLedgerService.RecordPersonnelPayment(db, payment.Id, paymentType, amount, person.FullName);
        db.SaveChanges();

        MessageBox.Show(
            $"{person.FullName} için {paymentType.ToLower(TrCulture)} kaydı oluşturuldu.\n" +
            $"Tutar: {amount.ToString("N2", TrCulture)} ₺",
            "Başarılı", MessageBoxButton.OK, MessageBoxImage.Information);

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
}
