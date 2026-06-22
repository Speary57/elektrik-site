from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("yonetim/", admin.site.urls),
    path("hesap/", include("accounts.urls")),
    path("", include("catalog.urls")),
    path("sepet/", include("cart.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.site_header = "Kılağuz Elektrik ve Yapı Market"
admin.site.site_title = "Yönetim"
admin.site.index_title = "Site yönetimi"
