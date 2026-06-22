"""Gmail SMTP — Windows / MSYS2 Python SSL sertifika sorununu giderir."""

import ssl

from django.core.mail.backends.smtp import EmailBackend as DjangoEmailBackend
from django.utils.functional import cached_property

try:
    import certifi
except ImportError as exc:
    raise ImportError(
        "E-posta göndermek için certifi gerekli. Terminalde çalıştırın: pip install certifi"
    ) from exc


class EmailBackend(DjangoEmailBackend):
    @cached_property
    def ssl_context(self):
        return ssl.create_default_context(cafile=certifi.where())
