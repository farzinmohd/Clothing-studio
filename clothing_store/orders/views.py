from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from carts.cart import Cart
from products.models import Product
from .models import Order, OrderItem


# ----------------------------------
# CHECKOUT + PLACE ORDER
# ----------------------------------
@login_required
def checkout(request):
    cart = Cart(request)

    # ❌ If cart is empty, redirect
    if len(cart) == 0:
        return redirect('product_list')

    if request.method == 'POST':
        # ✅ Create Order
        order = Order.objects.create(
            user=request.user,
            total_amount=cart.get_total_price(),
            status='Pending'
        )

        # ✅ Create Order Items + Reduce Stock
        for item in cart:
            product = item['product']
            quantity = item['quantity']

            # ❌ Block if not enough stock
            if product.stock < quantity:
                return redirect('cart_detail')

            # ✅ Create OrderItem
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price=item['price']
            )

            # ✅ Reduce stock
            product.stock -= quantity
            product.save()

        # ✅ Clear cart after order
        cart.clear()

        return redirect('order_success')

    return render(request, 'orders/checkout.html', {
        'cart': cart
    })


# ----------------------------------
# ORDER SUCCESS PAGE
# ----------------------------------
@login_required
def order_success(request):
    return render(request, 'orders/order_success.html')


# ----------------------------------
# USER ORDER LIST
# ----------------------------------
@login_required
def my_orders(request):
    orders = Order.objects.filter(
        user=request.user
    ).order_by('-created_at')

    return render(request, 'orders/my_orders.html', {
        'orders': orders
    })


# ----------------------------------
# ORDER DETAIL PAGE
# ----------------------------------
@login_required
def order_detail(request, order_id):
    order = get_object_or_404(
        Order,
        id=order_id,
        user=request.user
    )

    items = OrderItem.objects.filter(order=order)

    return render(request, 'orders/order_detail.html', {
        'order': order,
        'items': items
    })
