"""Resend HTTP API — Render gibi SMTP engelli sunucularda e-posta gönderimi."""

import json
import logging
import ssl
import urllib.error
import urllib.request

from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail.message import EmailMultiAlternatives

try:
    import certifi
except ImportError as exc:
    raise ImportError("Resend e-posta için certifi gerekli.") from exc

logger = logging.getLogger("cart.emails")


class ResendEmailBackend(BaseEmailBackend):
    def send_messages(self, email_messages):
        if not email_messages:
            return 0
        api_key = getattr(settings, "RESEND_API_KEY", "")
        if not api_key:
            if not self.fail_silently:
                raise ValueError("RESEND_API_KEY tanımlı değil.")
            return 0

        sent = 0
        for message in email_messages:
            try:
                self._send_one(message, api_key)
                sent += 1
            except Exception:
                logger.exception("Resend e-posta gönderilemedi: %s", message.subject)
                if not self.fail_silently:
                    raise
        return sent

    def _send_one(self, message, api_key):
        html_body = None
        if isinstance(message, EmailMultiAlternatives):
            for content, mimetype in message.alternatives:
                if mimetype == "text/html":
                    html_body = content
                    break

        payload = {
            "from": message.from_email or settings.DEFAULT_FROM_EMAIL,
            "to": list(message.to),
            "subject": message.subject,
            "text": message.body,
        }
        if html_body:
            payload["html"] = html_body
        if message.cc:
            payload["cc"] = list(message.cc)
        if message.bcc:
            payload["bcc"] = list(message.bcc)

        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            "https://api.resend.com/emails",
            data=data,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        context = ssl.create_default_context(cafile=certifi.where())
        with urllib.request.urlopen(request, timeout=15, context=context) as response:
            if response.status >= 300:
                raise urllib.error.HTTPError(
                    request.full_url,
                    response.status,
                    response.read().decode("utf-8", errors="replace"),
                    response.headers,
                    None,
                )
        logger.info("Resend e-posta gönderildi -> %s | %s", message.to, message.subject)
