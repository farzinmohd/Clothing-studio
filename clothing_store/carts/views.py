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
    color = request.POST.get('color')

    if not size or not color:
        messages.error(request, 'Please select size and color')
        return redirect('product_detail', product_id=product.id)

    cart = Cart(request)
    success = cart.add(product, size, color)

    if not success:
        messages.error(request, 'Selected variant is out of stock')

    return redirect('cart_detail')


def remove_from_cart(request, key):
    cart = Cart(request)
    cart.remove(key)
    return redirect('cart_detail')
