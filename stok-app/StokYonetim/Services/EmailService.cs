using System.Net;
using System.Net.Mail;

namespace StokYonetim.Services;

public class EmailService(SmtpConfig smtp)
{
    public bool IsConfigured =>
        !string.IsNullOrWhiteSpace(smtp.Host) &&
        !string.IsNullOrWhiteSpace(smtp.User) &&
        !string.IsNullOrWhiteSpace(smtp.Password);

    public async Task<bool> SendAsync(string to, string subject, string htmlBody)
    {
        if (!IsConfigured) return false;

        try
        {
            using var client = new SmtpClient(smtp.Host, smtp.Port)
            {
                EnableSsl = true,
                Credentials = new NetworkCredential(smtp.User, smtp.Password),
                Timeout = 12_000
            };

            var from = string.IsNullOrWhiteSpace(smtp.From) ? smtp.User : smtp.From;
            using var msg = new MailMessage(from, to, subject, htmlBody) { IsBodyHtml = true };
            await client.SendMailAsync(msg);
            return true;
        }
        catch
        {
            return false;
        }
    }
}
