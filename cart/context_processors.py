from . import cart as cart_service


def cart_summary(request):
    return {
        "sepet_adet": cart_service.cart_item_count(request),
    }
