import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Proje kökündeki .env dosyasından ayarları yükle (şifreler burada saklanır, git'e gitmez)
try:
    from dotenv import load_dotenv

    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass  # pip install python-dotenv

SECRET_KEY = os.environ.get(
    "SECRET_KEY", "dev-only-change-in-production-kilaguz-elektrik"
)

DEBUG = os.environ.get("DEBUG", "1") == "1"

ALLOWED_HOSTS = [
    h.strip()
    for h in os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if h.strip()
]

_csrf_origins = os.environ.get("CSRF_TRUSTED_ORIGINS", "")
CSRF_TRUSTED_ORIGINS = [o.strip() for o in _csrf_origins.split(",") if o.strip()]

# Render otomatik domain (ALLOWED_HOSTS unutulsa bile site açılır)
_render_host = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
if _render_host and _render_host not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(_render_host)
if _render_host:
    _render_origin = f"https://{_render_host}"
    if _render_origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(_render_origin)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "catalog",
    "cart",
    "accounts",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "accounts.middleware.AdminEmailOTPMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "cart.context_processors.cart_summary",
                "catalog.context_processors.site_settings",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
        "OPTIONS": {
            "timeout": 20,
        },
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "tr"
TIME_ZONE = "Europe/Istanbul"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SESSION_COOKIE_AGE = 60 * 60 * 24 * 7

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "catalog:home"
LOGOUT_REDIRECT_URL = "catalog:home"

# E-posta ayarları
# Gmail SMTP bilgileri ortam değişkenleriyle verilirse gerçek e-posta gönderilir.
# Verilmezse e-postalar konsola (sunucu terminaline) yazılır; böylece geliştirmede de çalışır.
EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "1") == "1"
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_TIMEOUT = int(os.environ.get("EMAIL_TIMEOUT", "10"))

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")

# Render ücretsiz planda SMTP (587) engellenir; Resend HTTP API kullanın.
if RESEND_API_KEY:
    EMAIL_BACKEND = "config.resend_backend.ResendEmailBackend"
elif EMAIL_HOST_USER and EMAIL_HOST_PASSWORD:
    EMAIL_BACKEND = "config.email_backend.EmailBackend"
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

DEFAULT_FROM_EMAIL = os.environ.get(
    "DEFAULT_FROM_EMAIL",
    EMAIL_HOST_USER or "onboarding@resend.dev",
)

# Sipariş bildirimlerinin gönderileceği adres
ORDER_NOTIFICATION_EMAIL = os.environ.get(
    "ORDER_NOTIFICATION_EMAIL", "kilaguzelektrik@gmail.com"
)

# E-postalardaki mutlak bağlantılar için site adresi (ör. https://kilaguzelektrik.com).
SITE_URL = os.environ.get("SITE_URL", "http://127.0.0.1:8000")

# Stok bu değerin altına düşünce işletmeye uyarı maili gönderilir (ör. 3 = 3'ten az).
LOW_STOCK_THRESHOLD = int(os.environ.get("LOW_STOCK_THRESHOLD", "3"))

# Yönetim paneli (personel) e-posta doğrulaması
ADMIN_URL_PREFIX = "/yonetim/"
ADMIN_OTP_CODE_TTL = 10 * 60          # Kodun geçerlilik süresi (saniye): 10 dk
ADMIN_OTP_SESSION_TTL = 8 * 60 * 60   # Doğrulamadan sonra panel erişimi: 8 saat
ADMIN_OTP_MAX_ATTEMPTS = 5            # Yanlış kod deneme sınırı

# Render / ters vekil (HTTPS) ayarları
if os.environ.get("RENDER") or os.environ.get("RENDER_EXTERNAL_HOSTNAME"):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# E-posta gönderimi arka planda olduğundan, sonuçların (başarı/hata) sunucu
# terminalinde görünmesi için loglama. Sorun ayıklamayı kolaylaştırır.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "cart.emails": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
