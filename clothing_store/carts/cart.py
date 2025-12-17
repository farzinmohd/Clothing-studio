from products.models import Product
from decimal import Decimal


class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get('cart')

        if not cart:
            cart = self.session['cart'] = {}

        self.cart = cart

    # -------------------------
    # ADD PRODUCT
    # -------------------------
    def add(self, product, quantity=1):
        product_id = str(product.id)

        if product_id not in self.cart:
            self.cart[product_id] = {
                'quantity': 0,
                'price': str(product.price)
            }

        self.cart[product_id]['quantity'] += quantity

        if self.cart[product_id]['quantity'] <= 0:
            del self.cart[product_id]

        self.save()

    # -------------------------
    # REMOVE PRODUCT
    # -------------------------
    def remove(self, product):
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    # -------------------------
    # ITERATE CART
    # -------------------------
    def __iter__(self):
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)

        for product in products:
            item = self.cart[str(product.id)]
            item['product'] = product
            item['price'] = Decimal(item['price'])
            item['total_price'] = item['price'] * item['quantity']
            yield item

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
