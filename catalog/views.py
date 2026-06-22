import logging

from django.contrib import messages
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from .forms import ContactLeadForm
from .models import Category, ContactMessage, Product, StockNotification

logger = logging.getLogger(__name__)


SORT_OPTIONS = {
    "yeni": ("-created_at", "En yeniler"),
    "fiyat_artan": ("price", "Fiyat: düşükten yükseğe"),
    "fiyat_azalan": ("-price", "Fiyat: yüksekten düşüğe"),
    "isim": ("name", "İsme göre (A-Z)"),
}
DEFAULT_SORT = "yeni"


def _parse_price(value):
    """'1.234,50' / '1234.50' gibi girdileri Decimal'e çevirir; geçersizse None."""
    if not value:
        return None
    cleaned = value.strip().replace(" ", "").replace(",", ".")
    try:
        from decimal import Decimal

        price = Decimal(cleaned)
    except Exception:
        return None
    return price if price >= 0 else None


def home(request):
    featured = Product.objects.filter(is_active=True).select_related("category")[:6]
    categories = Category.objects.all()[:8]
    categories_all = Category.objects.all()
    qs = Product.objects.filter(is_active=True).select_related("category")
    category_slug = request.GET.get("kategori")
    if category_slug:
        qs = qs.filter(category__slug=category_slug)
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(description__icontains=q))

    # Fiyat aralığı filtresi
    min_price_raw = request.GET.get("min", "").strip()
    max_price_raw = request.GET.get("max", "").strip()
    min_price = _parse_price(min_price_raw)
    max_price = _parse_price(max_price_raw)
    if min_price is not None:
        qs = qs.filter(price__gte=min_price)
    if max_price is not None:
        qs = qs.filter(price__lte=max_price)

    # Sıralama
    sort = request.GET.get("sirala", "").strip()
    if sort not in SORT_OPTIONS:
        sort = DEFAULT_SORT
    qs = qs.order_by(SORT_OPTIONS[sort][0])

    contact_flash = request.session.pop("contact_form_flash", None)
    favorite_ids = _user_favorite_ids(request)
    return render(
        request,
        "catalog/home.html",
        {
            "featured_products": featured,
            "categories": categories,
            "products": qs,
            "categories_all": categories_all,
            "current_category": category_slug,
            "search_query": q,
            "sort_options": SORT_OPTIONS,
            "current_sort": sort,
            "min_price": min_price_raw,
            "max_price": max_price_raw,
            "favorite_ids": favorite_ids,
            "contact_flash": contact_flash,
        },
    )


def _user_favorite_ids(request):
    """Giriş yapmış kullanıcının favori ürün id'leri (kümesi); değilse boş küme."""
    if not request.user.is_authenticated:
        return set()
    from accounts.models import Favorite

    return set(
        Favorite.objects.filter(user=request.user).values_list("product_id", flat=True)
    )


def product_list(request):
    query = request.GET.urlencode()
    url = reverse("catalog:home")
    if query:
        url += "?" + query
    return HttpResponseRedirect(f"{url}#spa-urunler")


def about(request):
    return HttpResponseRedirect(reverse("catalog:home") + "#spa-hakkimizda")


def contact(request):
    return HttpResponseRedirect(reverse("catalog:home") + "#spa-iletisim")


@require_http_methods(["POST"])
def contact_submit(request):
    next_url = f"{reverse('catalog:home')}?iletisim_scroll=1#spa-iletisim"
    form = ContactLeadForm(request.POST)
    if form.is_valid():
        data = form.cleaned_data
        ip = request.META.get("HTTP_X_FORWARDED_FOR")
        if ip:
            ip = ip.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR")
        try:
            ContactMessage.objects.create(
                ad_soyad=data["ad_soyad"],
                email=data["email"],
                telefon=data["telefon"],
                mesaj=data["mesaj"],
                aydinlatma_onay=data["aydinlatma_onay"],
                ip_address=ip or "",
            )
        except Exception:
            logger.exception("İletişim mesajı veritabanına yazılamadı")
            messages.error(
                request,
                "Mesajınız şu anda kaydedilemedi. Lütfen bir süre sonra yeniden deneyin.",
            )
            return HttpResponseRedirect(next_url)

        logger.info(
            "İletişim formu kaydedildi: ad_soyad=%r email=%r telefon=%r mesaj_len=%s",
            data["ad_soyad"],
            data["email"],
            data["telefon"],
            len(data["mesaj"]),
        )
        messages.success(
            request,
            "Mesajınız alınmıştır. En kısa sürede sizinle iletişime geçeceğiz.",
        )
        return HttpResponseRedirect(next_url)

    field_errors = {field: errs[0] for field, errs in form.errors.items()}
    request.session["contact_form_flash"] = {
        "field_errors": field_errors,
        "values": {
            "ad_soyad": request.POST.get("ad_soyad", "").strip(),
            "email": request.POST.get("email", "").strip(),
            "telefon": request.POST.get("telefon", "").strip(),
            "mesaj": request.POST.get("mesaj", "").strip(),
        },
    }
    messages.error(
        request,
        "Formu gönderemedik. Lütfen alanları kontrol edin ve aydınlatma metnini onaylayın.",
    )
    return HttpResponseRedirect(next_url)


@require_POST
def stock_notify(request, product_id):
    """'Stok gelince haber ver' aboneliği (AJAX). Stoksuz ürün için e-posta kaydeder."""
    product = get_object_or_404(Product, pk=product_id, is_active=True)

    if product.in_stock:
        return JsonResponse(
            {
                "ok": False,
                "level": "info",
                "message": "Bu ürün şu an zaten stokta. Hemen sipariş verebilirsiniz.",
            }
        )

    if request.user.is_authenticated:
        email = (request.POST.get("email") or request.user.email or "").strip()
    else:
        email = (request.POST.get("email") or "").strip()

    try:
        validate_email(email)
    except ValidationError:
        return JsonResponse(
            {
                "ok": False,
                "level": "warning",
                "message": "Lütfen geçerli bir e-posta adresi girin.",
            }
        )

    obj, created = StockNotification.objects.get_or_create(
        product=product,
        email=email,
        defaults={
            "user": request.user if request.user.is_authenticated else None,
        },
    )
    if not created and obj.notified:
        # Daha önce bildirilmiş; tekrar bekleme durumuna al.
        obj.notified = False
        obj.notified_at = None
        if request.user.is_authenticated and obj.user_id is None:
            obj.user = request.user
        obj.save(update_fields=["notified", "notified_at", "user"])

    return JsonResponse(
        {
            "ok": True,
            "level": "success",
            "message": "Harika! Ürün stoğa girdiğinde size e-posta ile haber vereceğiz.",
        }
    )


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.select_related("category"),
        slug=slug,
        is_active=True,
    )
    related = (
        Product.objects.filter(is_active=True, category=product.category)
        .exclude(pk=product.pk)[:4]
    )
    return render(
        request,
        "catalog/product_detail.html",
        {
            "product": product,
            "related_products": related,
            "favorite_ids": _user_favorite_ids(request),
        },
    )
