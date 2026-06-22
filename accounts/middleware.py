"""Yönetim paneli için e-posta tabanlı iki adımlı doğrulama (2FA).

Personel (is_staff) bir kullanıcı /yonetim/ altındaki bir adrese eriştiğinde,
oturumda geçerli bir doğrulama yoksa e-posta doğrulama sayfasına yönlendirilir.
Doğrulama başarılı olduktan sonra erişim, ADMIN_OTP_SESSION_TTL süresince geçerlidir.
"""

import time

from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse

SESSION_VERIFIED_AT = "admin_otp_verified_at"
SESSION_VERIFIED_UID = "admin_otp_verified_uid"


class AdminEmailOTPMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        prefix = getattr(settings, "ADMIN_URL_PREFIX", "/yonetim/")
        path = request.path

        if path.startswith(prefix) and not self._is_exempt(path, prefix):
            user = getattr(request, "user", None)
            if user is not None and user.is_authenticated and user.is_staff:
                if not self._is_verified(request, user):
                    verify_url = reverse("accounts:admin_verify")
                    return redirect(f"{verify_url}?next={path}")

        return self.get_response(request)

    @staticmethod
    def _is_exempt(path, prefix):
        # Çıkış ve oturum açma adımları doğrulama gerektirmez (kilitlenmeyi önler).
        for tail in ("logout/", "login/"):
            if path == prefix + tail or path.startswith(prefix + tail):
                return True
        return False

    @staticmethod
    def _is_verified(request, user):
        verified_at = request.session.get(SESSION_VERIFIED_AT)
        verified_uid = request.session.get(SESSION_VERIFIED_UID)
        if not verified_at or verified_uid != user.pk:
            return False
        ttl = getattr(settings, "ADMIN_OTP_SESSION_TTL", 8 * 60 * 60)
        return (time.time() - float(verified_at)) < ttl
