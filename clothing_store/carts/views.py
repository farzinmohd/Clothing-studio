from django.shortcuts import render, redirect, get_object_or_404
from products.models import Product
from .cart import Cart


# -------------------------
# CART DETAIL
# -------------------------
def cart_detail(request):
    cart = Cart(request)
    return render(request, 'cart/cart_detail.html', {'cart': cart})


# -------------------------
# ADD TO CART
# -------------------------
def add_to_cart(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)

    cart.add(product=product, quantity=1)
    return redirect('cart_detail')


# -------------------------
# REMOVE FROM CART
# -------------------------
def remove_from_cart(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)

    cart.remove(product)
    return redirect('cart_detail')


# -------------------------
# INCREASE QUANTITY
# -------------------------
def increase_quantity(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)

    cart.add(product=product, quantity=1)
    return redirect('cart_detail')


# -------------------------
# DECREASE QUANTITY
# -------------------------
def decrease_quantity(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)

    cart.add(product=product, quantity=-1)
    return redirect('cart_detail')
    