from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from .models import Cart, CartItem
from products.models import Product

@receiver(user_logged_in)
def merge_cart_on_login(sender, user, request, **kwargs):
    """
    When user logs in:
    1. Get their Session Cart.
    2. Move items to their Database Cart.
    3. Clear Session Cart.
    """
    session_cart = request.session.get('cart', {})
    
    if not session_cart:
        return

    # Get or Create DB Cart
    db_cart, _ = Cart.objects.get_or_create(user=user)

    for key, item_data in session_cart.items():
        try:
            product = Product.objects.get(id=item_data['product_id'])
            size = item_data['size']
            color = item_data.get('color')
            qty = item_data['quantity']

            # Check if item exists in DB cart
            cart_item, created = CartItem.objects.get_or_create(
                cart=db_cart,
                product=product,
                size=size,
                color=color,
                defaults={'quantity': qty}
            )

            if not created:
                # Merge quantities
                cart_item.quantity += qty
                cart_item.save()
        
        except Product.DoesNotExist:
            continue
        except Exception as e:
            print(f"Error merging cart item: {e}")

    # Clear Session Cart
    request.session['cart'] = {}
    request.session.modified = True
