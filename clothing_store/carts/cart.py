from products.models import Product, ProductVariant
from decimal import Decimal


class Cart:
    def __init__(self, request):
        self.session = request.session
        self.cart = self.session.get('cart', {})
        self.session['cart'] = self.cart

    # -------------------------
    # ADD TO CART (VARIANT)
    # -------------------------
    def add(self, product, size, color, quantity=1):
        variant = ProductVariant.objects.get(
            product=product,
            size=size,
            color=color
        )

        if variant.stock < quantity:
            return False

        key = f"{product.id}-{size}-{color}"

        if key not in self.cart:
            self.cart[key] = {
                'quantity': 0,
                'price': str(product.price),  # ✅ STRING ONLY
                'size': size,
                'color': color,
                'product_id': product.id
            }

        self.cart[key]['quantity'] += quantity
        self.save()
        return True

    # -------------------------
    # REMOVE ITEM
    # -------------------------
    def remove(self, key):
        if key in self.cart:
            del self.cart[key]
            self.save()

    # -------------------------
    # ITERATE CART (🔥 FIXED)
    # -------------------------
    def __iter__(self):
        product_ids = [item['product_id'] for item in self.cart.values()]
        products = Product.objects.filter(id__in=product_ids)
        product_map = {p.id: p for p in products}

        for key, item in self.cart.items():
            item_copy = item.copy()  # 🔥 CRITICAL FIX
            item_copy['product'] = product_map[item['product_id']]
            item_copy['price'] = Decimal(item['price'])
            item_copy['total_price'] = (
                item_copy['price'] * item_copy['quantity']
            )
            yield item_copy

    # -------------------------
    # TOTAL PRICE
    # -------------------------
    def get_total_price(self):
        return sum(item['total_price'] for item in self)

    # -------------------------
    # TOTAL QUANTITY
    # -------------------------
    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())

    # -------------------------
    # CLEAR CART
    # -------------------------
    def clear(self):
        self.session['cart'] = {}
        self.save()

    def save(self):
        self.session.modified = True
