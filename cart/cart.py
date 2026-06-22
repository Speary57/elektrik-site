from decimal import Decimal

from catalog.models import Product

CART_SESSION_KEY = "sepet"


def _get_raw_cart(request):
    return request.session.get(CART_SESSION_KEY, {})


def _save_raw_cart(request, cart):
    request.session[CART_SESSION_KEY] = cart
    request.session.modified = True


def get_line_quantity(request, product_id):
    cart = _get_raw_cart(request)
    return int(cart.get(str(product_id), 0))


def add_product(request, product_id, quantity=1):
    cart = _get_raw_cart(request)
    key = str(product_id)
    current = int(cart.get(key, 0))
    cart[key] = current + max(1, int(quantity))
    _save_raw_cart(request, cart)


def set_quantity(request, product_id, quantity):
    cart = _get_raw_cart(request)
    key = str(product_id)
    q = int(quantity)
    if q <= 0:
        cart.pop(key, None)
    else:
        cart[key] = q
    _save_raw_cart(request, cart)


def normalize_cart_stocks(request):
    """Sepetteki adetleri güncel stokla sınırlar; stoksuz satırları siler. Değişiklik olduysa True."""
    raw = _get_raw_cart(request)
    if not raw:
        return False
    ids = [int(k) for k in raw.keys()]
    products = {p.id: p for p in Product.objects.filter(id__in=ids, is_active=True)}
    new_cart = dict(raw)
    changed = False
    for pid_str, qty in list(raw.items()):
        pid = int(pid_str)
        product = products.get(pid)
        if not product:
            new_cart.pop(pid_str, None)
            changed = True
            continue
        q = int(qty)
        cap = int(product.stock_quantity)
        if cap <= 0:
            new_cart.pop(pid_str, None)
            changed = True
        elif q > cap:
            new_cart[pid_str] = cap
            changed = True
    if changed:
        _save_raw_cart(request, new_cart)
    return changed


def remove_product(request, product_id):
    cart = _get_raw_cart(request)
    cart.pop(str(product_id), None)
    _save_raw_cart(request, cart)


def clear_cart(request):
    request.session[CART_SESSION_KEY] = {}
    request.session.modified = True


def get_cart_lines(request):
    raw = _get_raw_cart(request)
    if not raw:
        return [], Decimal("0.00")
    ids = [int(k) for k in raw.keys()]
    products = {p.id: p for p in Product.objects.filter(id__in=ids, is_active=True)}
    lines = []
    total = Decimal("0.00")
    for pid_str, qty in raw.items():
        pid = int(pid_str)
        product = products.get(pid)
        if not product:
            continue
        qty = int(qty)
        line_total = product.price * qty
        total += line_total
        lines.append(
            {
                "product": product,
                "quantity": qty,
                "line_total": line_total,
            }
        )
    return lines, total


def cart_item_count(request):
    raw = _get_raw_cart(request)
    return sum(int(v) for v in raw.values())
