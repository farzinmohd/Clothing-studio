import stripe
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from carts.cart import Cart
from products.models import Product
from .models import Order, OrderItem

stripe.api_key = settings.STRIPE_SECRET_KEY


# ----------------------------------
# CHECKOUT + PLACE ORDER
# ----------------------------------
@login_required
def checkout(request):
    cart = Cart(request)

    if len(cart) == 0:
        return redirect('product_list')

    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')

        if payment_method not in ['COD', 'ONLINE']:
            return redirect('checkout')

        # ✅ Create Order
        order = Order.objects.create(
            user=request.user,
            total_amount=cart.get_total_price(),
            payment_method=payment_method,
            status='pending'
        )

        # ✅ Create Order Items + Reduce Stock
        for item in cart:
            product = item['product']
            quantity = item['quantity']

            if product.stock < quantity:
                return redirect('cart_detail')

            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price=item['price']
            )

            product.stock -= quantity
            product.save()

        # -----------------------------
        # 🔥 STRIPE PAYMENT
        # -----------------------------
        if payment_method == 'ONLINE':
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[
                    {
                        'price_data': {
                            'currency': 'inr',
                            'product_data': {
                                'name': f'Order #{order.id}',
                            },
                            'unit_amount': int(order.total_amount * 100),
                        },
                        'quantity': 1,
                    }
                ],
                mode='payment',
                success_url=request.build_absolute_uri(
                    f'/orders/stripe-success/{order.id}/'
                ),
                cancel_url=request.build_absolute_uri('/orders/checkout/')
            )
            return redirect(session.url)

        # -----------------------------
        # ✅ CASH ON DELIVERY
        # -----------------------------
        cart.clear()
        return redirect('order_success')

    return render(request, 'orders/checkout.html', {
        'cart': cart
    })


# ----------------------------------
# STRIPE SUCCESS CALLBACK
# ----------------------------------
@login_required
def stripe_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    order.status = 'paid'
    order.save()

    Cart(request).clear()
    return redirect('order_success')


# ----------------------------------
# ORDER SUCCESS PAGE
# ----------------------------------
@login_required
def order_success(request):
    return render(request, 'orders/order_success.html')


# ----------------------------------
# USER ORDERS LIST
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
# ORDER DETAIL PAGE (IMPORTANT)
# ----------------------------------
@login_required
def order_detail(request, order_id):
    order = get_object_or_404(
        Order,
        id=order_id,
        user=request.user
    )

    return render(request, 'orders/order_detail.html', {
        'order': order
    })
