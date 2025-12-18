import stripe
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from carts.cart import Cart
from products.models import Product
from accounts.models import Address
from .models import Order, OrderItem

# ✅ Stripe key
stripe.api_key = settings.STRIPE_SECRET_KEY


# ----------------------------------
# CHECKOUT + PLACE ORDER
# ----------------------------------
@login_required
def checkout(request):
    cart = Cart(request)
    addresses = Address.objects.filter(user=request.user)

    if len(cart) == 0:
        return redirect('product_list')

    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        address_id = request.POST.get('address')

        # ❌ Address not selected
        if not address_id:
            messages.error(request, 'Please select a delivery address')
            return redirect('checkout')

        try:
            selected_address = Address.objects.get(
                id=address_id,
                user=request.user
            )
        except Address.DoesNotExist:
            messages.error(request, 'Invalid address selected')
            return redirect('checkout')

        if payment_method not in ['COD', 'ONLINE']:
            messages.error(request, 'Invalid payment method')
            return redirect('checkout')

        # ✅ Create Order
        order = Order.objects.create(
            user=request.user,
            address=selected_address,
            total_amount=cart.get_total_price(),
            payment_method=payment_method,
            status='pending'
        )

        # ✅ Create Order Items + Reduce Stock
        for item in cart:
            product = item['product']
            quantity = item['quantity']

            if product.stock < quantity:
                messages.error(request, 'Insufficient stock')
                return redirect('cart_detail')

            OrderItem.objects.create(
    order=order,
    product=product,
    size=item['size'],
    color=item['color'],
    quantity=item['quantity'],
    price=item['price']
)


            product.stock -= quantity
            product.save()

        # -----------------------------
        # 🔥 STRIPE PAYMENT (FIXED)
        # -----------------------------
        if payment_method == 'ONLINE':
            try:
                session = stripe.checkout.Session.create(
                    payment_method_types=['card'],
                    line_items=[
                        {
                            'price_data': {
                                'currency': 'inr',
                                'product_data': {
                                    'name': f'Order #{order.id}',
                                },
                                # 🔴 MUST be int
                                'unit_amount': int(order.total_amount * 100),
                            },
                            'quantity': 1,
                        }
                    ],
                    mode='payment',
                    success_url=request.build_absolute_uri(
                        f'/orders/stripe-success/{order.id}/'
                    ),
                    cancel_url=request.build_absolute_uri('/orders/checkout/'),
                )

                # 🔥 IMPORTANT: 303 redirect
                return redirect(session.url, code=303)

            except Exception as e:
                messages.error(request, f"Stripe error: {str(e)}")
                return redirect('checkout')

        # -----------------------------
        # ✅ CASH ON DELIVERY
        # -----------------------------
        cart.clear()
        messages.success(request, 'Order placed successfully')
        return redirect('order_success')

    return render(request, 'orders/checkout.html', {
        'cart': cart,
        'addresses': addresses
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
# ORDER DETAIL PAGE
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




@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if order.status in ['shipped', 'delivered']:
        messages.error(request, 'Order cannot be cancelled now.')
        return redirect('order_detail', order_id=order.id)

    order.status = 'cancelled'
    order.save()
    messages.success(request, 'Order cancelled successfully.')
    return redirect('my_orders')
