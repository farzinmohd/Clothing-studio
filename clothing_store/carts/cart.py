from decimal import Decimal
from django.conf import settings
from products.models import Product, ProductVariant
from .models import Cart as CartModel, CartItem

class Cart:
    def __init__(self, request):
        self.session = request.session
        self.request = request
        
        # 1. Session Cart Init
        cart = self.session.get('cart')
        if not cart:
            cart = self.session['cart'] = {}
        self.session_cart = cart

        # 2. DB Cart Init (if auth)
        self.db_cart = None
        if request.user.is_authenticated:
            self.db_cart, _ = CartModel.objects.get_or_create(user=request.user)

    def add(self, product, size, color=None):
        """
        Add product to cart (Session OR DB)
        """
        # Validate Stock First
        if not self._check_stock(product, size, color):
            return False

        if self.request.user.is_authenticated:
            self._add_to_db(product, size, color)
        else:
            self._add_to_session(product, size, color)
        
        return True

    def _check_stock(self, product, size, color):
        try:
            # Note: Assuming product.variants lookup logic matches
            if color:
                # If variant has color? Or product? The original code had confusing logic here.
                # Assuming standard variance based on Size for this project structure
                pass 
            
            # Simple check based on previous logic observation
            # Assuming Variant is just Size as per Products/Models
            variant = ProductVariant.objects.filter(product=product, size=size).first()
            if variant and variant.stock <= 0:
                return False
            return True
        except Exception:
            return False

    def _add_to_db(self, product, size, color):
        item, created = CartItem.objects.get_or_create(
            cart=self.db_cart,
            product=product,
            size=size,
            color=color,
            defaults={'quantity': 1}
        )
        if not created:
            item.quantity += 1
            item.save()

    def _add_to_session(self, product, size, color):
        key = self._get_session_key(product.id, size, color)
        if key not in self.session_cart:
            self.session_cart[key] = {
                'product_id': product.id,
                'size': size,
                'color': color,
                'quantity': 1,
                'price': str(product.price),
            }
        else:
            self.session_cart[key]['quantity'] += 1
        self.save_session()

    def save_session(self):
        self.session.modified = True

    def remove(self, key):
        """
        Remove item. 
        For DB: key is cart_item.id (as str) or similar unique identifier? 
        Actually, existing Views pass 'key' from session.
        We need to harmonize this. 
        Legacy Code passed "product_id-size-color" as key.
        For DB, we better use that same key format to find the item, OR change Views.
        Changing Views is risky. Let's support the key format for DB lookup too.
        """
        if self.request.user.is_authenticated:
            # Parse Key: productId-Size-Color
            try:
                parts = key.split('-')
                p_id = parts[0]
                size = parts[1]
                color = parts[2] if len(parts) > 2 else None
                
                CartItem.objects.filter(
                    cart=self.db_cart,
                    product_id=p_id,
                    size=size,
                    color=color
                ).delete()
            except:
                pass
        else:
            if key in self.session_cart:
                del self.session_cart[key]
                self.save_session()

    def update(self, key, quantity):
        if self.request.user.is_authenticated:
            try:
                parts = key.split('-')
                p_id = parts[0]
                size = parts[1]
                color = parts[2] if len(parts) > 2 else None
                
                item = CartItem.objects.filter(
                    cart=self.db_cart,
                    product_id=p_id,
                    size=size,
                    color=color
                ).first()
                
                if item:
                    if quantity > 0:
                        item.quantity = quantity
                        item.save()
                    else:
                        item.delete()
            except:
                pass
        else:
            if key in self.session_cart:
                if quantity > 0:
                    self.session_cart[key]['quantity'] = quantity
                else:
                    del self.session_cart[key]
                self.save_session()

    def __iter__(self):
        """
        Yields dicts with 'product', 'total_price', 'quantity', 'key'
        matching the template expectation.
        """
        if self.request.user.is_authenticated:
            items = self.db_cart.items.select_related('product').all()
            for item in items:
                # Generate key for Remove/Update links
                color_part = f"-{item.color}" if item.color else ""
                key = f"{item.product.id}-{item.size}{color_part}"
                
                yield {
                    'product': item.product,
                    'product_id': item.product.id,
                    'quantity': item.quantity,
                    'price': item.product.price,
                    'total_price': item.total_price,
                    'size': item.size,
                    'color': item.color,
                    'key': key 
                }
        else:
            # Session Iteration (Legacy + Product hydration)
            product_ids = [item['product_id'] for item in self.session_cart.values()]
            products = Product.objects.filter(id__in=product_ids)
            product_map = {p.id: p for p in products}

            for key, item in self.session_cart.items():
                product = product_map.get(item['product_id'])
                if not product:
                    continue # specific product deleted?
                    
                val = item.copy()
                val['product'] = product
                val['price'] = Decimal(val['price'])
                val['total_price'] = val['price'] * val['quantity']
                val['key'] = key
                yield val

    def __len__(self):
        if self.request.user.is_authenticated:
            return self.db_cart.items.count() # This counts unique items (rows), not sum of quantity. Standard for 'len'.
        return len(self.session_cart)

    def get_total_price(self):
        if self.request.user.is_authenticated:
            return sum(item.total_price for item in self.db_cart.items.all())
        return sum(Decimal(item['price']) * item['quantity'] for item in self.session_cart.values())

    def clear(self):
        if self.request.user.is_authenticated:
            self.db_cart.items.all().delete()
        else:
            self.session['cart'] = {}
            self.save_session()

    def _get_session_key(self, product_id, size, color):
        if color:
            return f"{product_id}-{size}-{color}"
        return f"{product_id}-{size}"
