using System.Globalization;
using System.Text;
using System.Text.RegularExpressions;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;

namespace StokYonetim.Helpers;

public sealed class InputFormattingState
{
    public bool IsFormatting { get; set; }
}

public static class PersonnelFormHelper
{
    public static bool TryParseSalary(string input, out decimal salary)
    {
        salary = 0;
        if (string.IsNullOrWhiteSpace(input)) return true;

        var cleaned = input.Replace("₺", "").Trim();

        if (decimal.TryParse(cleaned, NumberStyles.Number, CultureInfo.GetCultureInfo("tr-TR"), out salary))
            return true;

        var normalized = cleaned.Replace(" ", "").Replace(',', '.');
        return decimal.TryParse(normalized, NumberStyles.Number, CultureInfo.InvariantCulture, out salary);
    }

    public static bool ValidateBirthDate(string input, out DateTime? date, out string errorMessage)
    {
        date = null;
        errorMessage = "";

        if (string.IsNullOrWhiteSpace(input)) return true;

        if (input.Length != 10 || ExtractDigits(input).Length != 8)
        {
            errorMessage = "Doğum tarihi GG/AA/YYYY formatında eksiksiz girilmelidir.";
            return false;
        }

        if (!DateTime.TryParseExact(input, "dd/MM/yyyy", CultureInfo.InvariantCulture, DateTimeStyles.None, out var parsed))
        {
            errorMessage = "Girdiğiniz doğum tarihi geçerli değil. Lütfen kontrol edin.";
            return false;
        }

        if (parsed.Date > DateTime.Today)
        {
            errorMessage = "Doğum tarihi bugünden ileri olamaz.";
            return false;
        }

        if (parsed.Date > DateTime.Today.AddYears(-18))
        {
            errorMessage = "Girdiğiniz tarihteki kullanıcı 18 yaşından küçük olamaz!";
            return false;
        }

        date = parsed.Date;
        return true;
    }

    public static string ExtractDigits(string text) => new(text.Where(char.IsDigit).ToArray());

    public static bool IsNameChar(char c) => char.IsLetter(c) || c == ' ';

    public static string FormatPhone(string digits)
    {
        if (string.IsNullOrEmpty(digits)) return "";
        var sb = new StringBuilder();
        for (var i = 0; i < digits.Length; i++)
        {
            if (i is 4 or 7 or 9) sb.Append(' ');
            sb.Append(digits[i]);
        }
        return sb.ToString();
    }

    public static string FormatBirthDate(string digits)
    {
        if (string.IsNullOrEmpty(digits)) return "";
        var sb = new StringBuilder();
        for (var i = 0; i < digits.Length; i++)
        {
            if (i is 2 or 4) sb.Append('/');
            sb.Append(digits[i]);
        }
        return sb.ToString();
    }

    public static void AttachFullNameBox(TextBox box)
    {
        box.PreviewTextInput += (_, e) => e.Handled = e.Text.Any(c => !IsNameChar(c));
        DataObject.AddPastingHandler(box, (_, e) =>
        {
            if (!e.DataObject.GetDataPresent(typeof(string))) return;
            var text = e.DataObject.GetData(typeof(string)) as string ?? "";
            if (text.Any(c => !IsNameChar(c))) e.CancelCommand();
        });
    }

    public static void AttachPhoneBox(TextBox box, InputFormattingState state)
    {
        box.PreviewTextInput += (_, e) => e.Handled = !e.Text.All(char.IsDigit);
        DataObject.AddPastingHandler(box, (_, e) =>
        {
            if (!e.DataObject.GetDataPresent(typeof(string))) return;
            var text = e.DataObject.GetData(typeof(string)) as string ?? "";
            if (text.Any(c => !char.IsDigit(c))) e.CancelCommand();
        });
        box.TextChanged += (_, _) =>
        {
            if (state.IsFormatting) return;
            state.IsFormatting = true;
            var digits = ExtractDigits(box.Text);
            if (digits.Length > 11) digits = digits[..11];
            var formatted = FormatPhone(digits);
            if (box.Text != formatted)
            {
                box.Text = formatted;
                box.CaretIndex = formatted.Length;
            }
            state.IsFormatting = false;
        };
    }

    public static void SetPhoneText(TextBox box, InputFormattingState state, string phone)
    {
        state.IsFormatting = true;
        box.Text = FormatPhone(ExtractDigits(phone));
        state.IsFormatting = false;
    }

    public static void AttachBirthDateBox(
        TextBox box,
        Border border,
        TextBlock hint,
        TextBlock errorText,
        InputFormattingState state)
    {
        box.PreviewTextInput += (_, e) => e.Handled = !e.Text.All(char.IsDigit);
        DataObject.AddPastingHandler(box, (_, e) =>
        {
            if (!e.DataObject.GetDataPresent(typeof(string))) return;
            var text = e.DataObject.GetData(typeof(string)) as string ?? "";
            if (text.Any(c => !char.IsDigit(c))) e.CancelCommand();
        });
        box.TextChanged += (_, _) =>
        {
            if (state.IsFormatting) return;
            state.IsFormatting = true;
            var digits = ExtractDigits(box.Text);
            if (digits.Length > 8) digits = digits[..8];
            var formatted = FormatBirthDate(digits);
            if (box.Text != formatted)
            {
                box.Text = formatted;
                box.CaretIndex = formatted.Length;
            }
            state.IsFormatting = false;
            UpdateBirthDateValidation(box, border, hint, errorText);
        };
        box.GotFocus += (_, _) =>
        {
            border.BorderBrush = errorText.Visibility == Visibility.Visible
                ? new SolidColorBrush((Color)ColorConverter.ConvertFromString("#DC2626")!)
                : (Brush)box.FindResource("PrimaryBrush");
            border.BorderThickness = new Thickness(1.5);
        };
        box.LostFocus += (_, _) => UpdateBirthDateValidation(box, border, hint, errorText);
    }

    public static void SetBirthDateText(TextBox box, TextBlock hint, TextBlock errorText, Border border, InputFormattingState state, DateTime? date)
    {
        state.IsFormatting = true;
        box.Text = date?.ToString("dd/MM/yyyy") ?? "";
        state.IsFormatting = false;
        ClearBirthDateError(border, hint, errorText, box);
    }

    public static void UpdateBirthDateValidation(TextBox box, Border border, TextBlock hint, TextBlock errorText)
    {
        var text = box.Text.Trim();
        if (string.IsNullOrWhiteSpace(text))
        {
            ClearBirthDateError(border, hint, errorText, box);
            return;
        }

        if (!ValidateBirthDate(text, out _, out var errorMessage))
            ShowBirthDateError(border, hint, errorText, box, errorMessage);
        else
            ClearBirthDateError(border, hint, errorText, box);
    }

    public static void ShowBirthDateError(Border border, TextBlock hint, TextBlock errorText, TextBox box, string message)
    {
        errorText.Text = message;
        errorText.Visibility = Visibility.Visible;
        hint.Visibility = Visibility.Collapsed;
        border.BorderBrush = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#DC2626")!);
        border.BorderThickness = new Thickness(1.5);
    }

    public static void ClearBirthDateError(Border border, TextBlock hint, TextBlock errorText, TextBox box)
    {
        errorText.Text = "";
        errorText.Visibility = Visibility.Collapsed;
        hint.Visibility = Visibility.Visible;
        if (!box.IsFocused)
        {
            border.BorderBrush = (Brush)box.FindResource("BorderBrush");
            border.BorderThickness = new Thickness(1);
        }
    }

    public static void AttachSalaryBox(TextBox box)
    {
        box.PreviewTextInput += (_, e) => e.Handled = !Regex.IsMatch(e.Text, @"^[\d,.\s]$");
        DataObject.AddPastingHandler(box, (_, e) =>
        {
            if (!e.DataObject.GetDataPresent(typeof(string))) return;
            var text = e.DataObject.GetData(typeof(string)) as string ?? "";
            if (text.Any(c => !char.IsDigit(c) && c is not ',' and not '.' and not ' ')) e.CancelCommand();
        });
    }
}
