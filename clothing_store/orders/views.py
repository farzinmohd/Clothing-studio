import stripe
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from carts.cart import Cart
from .models import Order, OrderItem
from django.utils import timezone

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

        # ✅ Create Order FIRST
        order = Order.objects.create(
            user=request.user,
            total_amount=cart.get_total_price(),
            payment_method=payment_method,
            status='Pending'
        )

        # ✅ Create Order Items
        for item in cart:
            OrderItem.objects.create(
                order=order,
                product=item['product'],
                quantity=item['quantity'],
                price=item['price']
            )

        # -----------------------------
        # 🔥 STRIPE ONLINE PAYMENT
        # -----------------------------
        if payment_method == 'ONLINE':
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[
                    {
                        'price_data': {
                            'currency': 'inr',
                            'product_data': {
                                'name': f"Order #{order.id}",
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
                cancel_url=request.build_absolute_uri('/cart/')
            )

            return redirect(session.url)

        # -----------------------------
        # ✅ CASH ON DELIVERY
        # -----------------------------
        cart.clear()
        return redirect('order_success')

    return render(request, 'orders/checkout.html', {'cart': cart})


# ----------------------------------
# STRIPE SUCCESS CALLBACK
# ----------------------------------
@login_required
def stripe_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order.status = 'Paid'
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
# USER ORDERS
# ----------------------------------
@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'orders/my_orders.html', {'orders': orders})


# ----------------------------------
# ORDER DETAIL
# ----------------------------------
@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/order_detail.html', {'order': order})



@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if not order.can_cancel():
        return redirect('order_detail', order_id=order.id)

    if request.method == 'POST':
        reason = request.POST.get('reason')

        order.status = 'Cancelled'
        order.cancel_reason = reason
        order.cancelled_at = timezone.now()
        order.save()

        # 🔁 MOCK REFUND (if online payment)
        if order.payment_method == 'ONLINE':
            print("Refund initiated (mock)")

        return redirect('my_orders')

    return render(request, 'orders/cancel_order.html', {'order': order})
