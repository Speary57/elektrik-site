from .models import SiteSettings


def site_settings(request):
    """Tüm şablonlarda `site_settings` olarak iletişim bilgilerini sağlar."""
    try:
        settings_obj = SiteSettings.load()
    except Exception:
        settings_obj = None
    return {"site_settings": settings_obj}
