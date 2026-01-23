from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from products.models import Product
from .cart import Cart


def cart_detail(request):
    cart = Cart(request)
    return render(request, 'cart/cart_detail.html', {'cart': cart})


def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    size = request.POST.get('size')

    if not size:
        messages.error(request, 'Please select a size')
        return redirect('product_detail', product_id=product.id)

    cart = Cart(request)
    success = cart.add(product, size=size)

    if success:
        # ✅ TRACK CART ADDS (For Dynamic Pricing)
        product.cart_add_count += 1
        product.save()
    else:
        messages.error(request, 'Selected size is out of stock')

    return redirect('cart_detail')



def remove_from_cart(request, key):
    cart = Cart(request)
    cart.remove(key)
    return redirect('cart_detail')


def update_cart(request, key):
    cart = Cart(request)
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        success = cart.update(key, quantity)
        
        if not success:
            # Get existing messages
            existing_messages = messages.get_messages(request)
            error_msg = 'Cannot add more items than available in stock!'
            
            # Check if this message already exists
            has_error = False
            for msg in existing_messages:
                if str(msg) == error_msg:
                    has_error = True
                    break
            
            # Only add if not already present
            if not has_error:
                messages.error(request, error_msg)
    
    return redirect('cart_detail')
