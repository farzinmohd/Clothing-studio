from .models import Cart

def cart_count(request):
    """
    Returns the number of items in the cart (Session or DB).
    """
    count = 0
    if request.user.is_authenticated:
        try:
            # We filter by user directly to avoid creating a cart just for a page load if none exists
            # Optimized: Cart -> CartItem count
            cart = Cart.objects.filter(user=request.user).first()
            if cart:
                count = cart.items.count()
        except Exception:
            pass
    else:
        # Session Cart
        cart = request.session.get('cart')
        if cart:
            count = len(cart)
    
    return {'cart_count': count}
