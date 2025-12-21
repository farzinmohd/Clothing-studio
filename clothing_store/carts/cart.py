from decimal import Decimal
from products.models import Product, ProductVariant


class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get('cart')

        if not cart:
            cart = self.session['cart'] = {}

        self.cart = cart

    def add(self, product, size, color=None):
        # Build key
        if color:
            key = f"{product.id}-{size}-{color}"
        else:
            key = f"{product.id}-{size}"

        # Check stock
        try:
            if color:
                variant = ProductVariant.objects.get(
                    product=product,
                    size=size,
                    color=color
                )
            else:
                variant = ProductVariant.objects.get(
                    product=product,
                    size=size
                )

            if variant.stock <= 0:
                return False

        except ProductVariant.DoesNotExist:
            return False

        # Add to cart
        if key not in self.cart:
            self.cart[key] = {
                'product_id': product.id,
                'size': size,
                'color': color,
                'quantity': 1,
                'price': str(product.price),
            }
        else:
            self.cart[key]['quantity'] += 1

        self.save()
        return True

    def save(self):
        self.session.modified = True

    def remove(self, key):
        if key in self.cart:
            del self.cart[key]
            self.save()

    def __iter__(self):
        product_ids = [item['product_id'] for item in self.cart.values()]
        products = Product.objects.filter(id__in=product_ids)

        product_map = {product.id: product for product in products}

        for key, item in self.cart.items():
            product = product_map.get(item['product_id'])

            item_copy = item.copy()
            item_copy['product'] = product
            item_copy['price'] = Decimal(item['price'])
            item_copy['total_price'] = item_copy['price'] * item_copy['quantity']
            item_copy['key'] = key

            yield item_copy

    def __len__(self):
        return len(self.cart)

    def get_total_price(self):
        return sum(
            Decimal(item['price']) * item['quantity']
            for item in self.cart.values()
        )

    def clear(self):
        self.session['cart'] = {}
        self.save()
