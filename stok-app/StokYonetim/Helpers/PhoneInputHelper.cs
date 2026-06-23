using System.Runtime.CompilerServices;
using System.Text;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;

namespace StokYonetim.Helpers;

public static class PhoneInputHelper
{
    private static readonly ConditionalWeakTable<TextBox, FormatState> States = new();

    public static void Attach(TextBox box)
    {
        box.MaxLength = 14;
        States.Add(box, new FormatState());

        box.PreviewTextInput += (_, e) => e.Handled = !e.Text.All(char.IsDigit);
        DataObject.AddPastingHandler(box, (_, e) =>
        {
            if (!e.DataObject.GetDataPresent(typeof(string))) return;
            var text = e.DataObject.GetData(typeof(string)) as string ?? "";
            if (text.Any(c => !char.IsDigit(c))) e.CancelCommand();
        });
        box.TextChanged += (_, _) => ApplyFormat(box);
    }

    public static string ExtractDigits(string text) => new(text.Where(char.IsDigit).ToArray());

    public static string Format(string digits)
    {
        if (string.IsNullOrEmpty(digits)) return "";
        if (digits.Length > 11) digits = digits[..11];

        var sb = new StringBuilder();
        for (var i = 0; i < digits.Length; i++)
        {
            if (i is 4 or 7 or 9) sb.Append(' ');
            sb.Append(digits[i]);
        }

        return sb.ToString();
    }

    public static void SetText(TextBox box, string? phone)
    {
        if (!States.TryGetValue(box, out var state)) return;
        state.Formatting = true;
        box.Text = Format(ExtractDigits(phone ?? ""));
        state.Formatting = false;
    }

    private static void ApplyFormat(TextBox box)
    {
        if (!States.TryGetValue(box, out var state) || state.Formatting) return;
        state.Formatting = true;

        var digits = ExtractDigits(box.Text);
        var formatted = Format(digits);
        if (box.Text != formatted)
        {
            box.Text = formatted;
            box.CaretIndex = formatted.Length;
        }

        state.Formatting = false;
    }

    private sealed class FormatState
    {
        public bool Formatting;
    }
}
