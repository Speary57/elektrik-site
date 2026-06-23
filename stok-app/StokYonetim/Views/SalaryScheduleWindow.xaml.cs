using System.Globalization;
using System.Windows;
using System.Windows.Controls;
using StokYonetim.Data;
using StokYonetim.Services;

namespace StokYonetim.Views;

public partial class SalaryScheduleWindow : Window
{
    private static readonly CultureInfo TrCulture = CultureInfo.GetCultureInfo("tr-TR");

    public SalaryScheduleWindow()
    {
        InitializeComponent();
        PaymentDayCombo.ItemsSource = Enumerable.Range(SalaryScheduleService.MinPaymentDay, SalaryScheduleService.MaxPaymentDay)
            .Select(d => d.ToString())
            .ToList();
        Loaded += (_, _) => LoadSettings();
    }

    private void LoadSettings()
    {
        using var db = new AppDbContext();
        var day = SalaryScheduleService.GetPaymentDay(db);
        PaymentDayCombo.SelectedItem = day.ToString();
        UpdateInfo(day);
    }

    private void PaymentDayCombo_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (!IsLoaded || PaymentDayCombo.SelectedItem is not string text) return;
        if (!int.TryParse(text, out var day)) return;
        UpdateInfo(day);
    }

    private void UpdateInfo(int day)
    {
        ScheduleInfoText.Text = SalaryScheduleService.FormatPaymentDayInfo(day);
        TodayHintText.Visibility = SalaryScheduleService.IsTodayPaymentDay(day)
            ? Visibility.Visible
            : Visibility.Collapsed;
        TodayHintText.Text = SalaryScheduleService.IsTodayPaymentDay(day)
            ? "Bugün belirlediğiniz maaş günü. \"Bu ay maaşları öde\" ile toplu ödeme yapabilirsiniz."
            : "";
    }

    private void Save_Click(object sender, RoutedEventArgs e)
    {
        if (PaymentDayCombo.SelectedItem is not string text || !int.TryParse(text, out var day))
        {
            MessageBox.Show("Lütfen geçerli bir gün seçin.", "Uyarı", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        using var db = new AppDbContext();
        SalaryScheduleService.SetPaymentDay(db, day);

        DialogResult = true;
        Close();
    }

    private void PayMonth_Click(object sender, RoutedEventArgs e)
    {
        if (MessageBox.Show(
                "Aktif personellerin bu ay maaşı ödenmemişse toplu olarak kaydedilecek.\nDevam edilsin mi?",
                "Toplu maaş ödemesi", MessageBoxButton.YesNo, MessageBoxImage.Question) != MessageBoxResult.Yes)
            return;

        using var db = new AppDbContext();
        var result = SalaryScheduleService.PayMonthlySalaries(db);

        if (result.PaidCount == 0 && result.SkippedCount == 0)
        {
            MessageBox.Show("Maaş ödenecek aktif personel bulunamadı.", "Bilgi",
                MessageBoxButton.OK, MessageBoxImage.Information);
            return;
        }

        MessageBox.Show(
            $"Ödenen: {result.PaidCount} personel\n" +
            $"Atlanan (bu ay zaten ödenmiş): {result.SkippedCount}\n" +
            $"Toplam: {result.TotalAmount.ToString("N2", TrCulture)} ₺",
            "Toplu maaş ödemesi", MessageBoxButton.OK, MessageBoxImage.Information);
    }

    private void Cancel_Click(object sender, RoutedEventArgs e)
    {
        DialogResult = false;
        Close();
    }
}
