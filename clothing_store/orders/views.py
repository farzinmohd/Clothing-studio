import stripe
from decimal import Decimal

from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from django.http import HttpResponse


from carts.cart import Cart
from accounts.models import Address
from .models import Order, OrderItem, Coupon   # 🔥 Coupon added

# ✅ Stripe key
stripe.api_key = settings.STRIPE_SECRET_KEY


# ----------------------------------
# CHECKOUT + PLACE ORDER (WITH COUPON)
# ----------------------------------
@login_required
def checkout(request):
    cart = Cart(request)
    addresses = Address.objects.filter(user=request.user)

    if len(cart) == 0:
        return redirect('product_list')

    discount_amount = Decimal('0')
    applied_coupon = None

    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        address_id = request.POST.get('address')
        coupon_code = request.POST.get('coupon_code')

        # ❌ Address not selected
        if not address_id:
            messages.error(request, 'Please select a delivery address')
            return redirect('checkout')

        selected_address = get_object_or_404(
            Address,
            id=address_id,
            user=request.user
        )

        if payment_method not in ['COD', 'ONLINE']:
            messages.error(request, 'Invalid payment method')
            return redirect('checkout')

        cart_total = cart.get_total_price()

        # -----------------------------
        # 🔥 COUPON LOGIC
        # -----------------------------
        if coupon_code:
            try:
                coupon = Coupon.objects.get(code__iexact=coupon_code)
                if coupon.is_valid(cart_total):
                    if coupon.discount_type == 'percent':
                        discount_amount = (cart_total * coupon.discount_value) / 100
                    else:
                        discount_amount = coupon.discount_value
                    applied_coupon = coupon
                else:
                    messages.error(request, 'Coupon is not valid')
            except Coupon.DoesNotExist:
                messages.error(request, 'Invalid coupon code')

        final_amount = cart_total - discount_amount
        if final_amount < 0:
            final_amount = Decimal('0')

        # -----------------------------
        # ✅ CREATE ORDER
        # -----------------------------
        order = Order.objects.create(
            user=request.user,
            address=selected_address,
            total_amount=cart_total,
            discount_amount=discount_amount,
            final_amount=final_amount,
            coupon=applied_coupon,
            payment_method=payment_method,
            status='pending'
        )

        # -----------------------------
        # ✅ CREATE ORDER ITEMS
        # -----------------------------
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
        # 🔥 STRIPE PAYMENT
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
                                'unit_amount': int(final_amount * 100),
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
    messages.success(request, 'Payment successful!')
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


# ----------------------------------
# CANCEL ORDER
# ----------------------------------
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

@login_required
def download_invoice(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{order.id}.pdf"'

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    y = height - 50

    # ================= HEADER BAR =================
    p.setFillColorRGB(0.2, 0.4, 0.8)  # Blue
    p.rect(0, height - 80, width, 80, fill=1)

    p.setFillColorRGB(1, 1, 1)
    p.setFont("Helvetica-Bold", 20)
    p.drawString(50, height - 55, "CLOTHING STORE")

    p.setFont("Helvetica", 10)
    p.drawString(50, height - 70, "Invoice")

    y -= 60
    p.setFillColorRGB(0, 0, 0)

    # ================= ORDER INFO =================
    p.setFont("Helvetica-Bold", 11)
    p.drawString(50, y, "Order Details")
    p.line(50, y - 2, width - 50, y - 2)
    y -= 20

    p.setFont("Helvetica", 10)
    p.drawString(50, y, f"Order ID: #{order.id}")
    p.drawString(300, y, f"Date: {order.created_at.strftime('%d-%m-%Y')}")
    y -= 15
    p.drawString(50, y, f"Payment Method: {order.payment_method}")
    p.drawString(300, y, f"Status: {order.status.title()}")
    y -= 30

    # ================= ADDRESS =================
    p.setFont("Helvetica-Bold", 11)
    p.drawString(50, y, "Billing Address")
    p.line(50, y - 2, width - 50, y - 2)
    y -= 20

    p.setFont("Helvetica", 10)
    p.drawString(50, y, order.address.full_name)
    y -= 15
    p.drawString(50, y, order.address.address_line)
    y -= 15
    p.drawString(
        50, y,
        f"{order.address.city}, {order.address.state} - {order.address.postal_code}"
    )
    y -= 15
    p.drawString(50, y, f"Phone: {order.address.phone}")
    y -= 30

    # ================= TABLE HEADER =================
    p.setFillColorRGB(0.9, 0.9, 0.9)
    p.rect(50, y, width - 100, 20, fill=1)

    p.setFillColorRGB(0, 0, 0)
    p.setFont("Helvetica-Bold", 10)
    p.drawString(55, y + 6, "Product")
    p.drawString(260, y + 6, "Variant")
    p.drawString(360, y + 6, "Qty")
    p.drawString(420, y + 6, "Price")

    y -= 25
    p.setFont("Helvetica", 10)

    # ================= ITEMS =================
    for item in order.items.all():
        p.drawString(55, y, item.product.name)
        p.drawString(260, y, f"{item.size} / {item.color}")
        p.drawString(365, y, str(item.quantity))
        p.drawString(420, y, f"₹{item.price}")
        y -= 18

        if y < 120:
            p.showPage()
            y = height - 100

    y -= 10
    p.line(50, y, width - 50, y)
    y -= 20

    # ================= TOTALS =================
    p.setFont("Helvetica-Bold", 10)
    p.drawString(330, y, "Subtotal:")
    p.drawString(450, y, f"₹{order.total_amount}")
    y -= 15

    if order.discount_amount > 0:
        p.setFillColorRGB(0.8, 0, 0)
        p.drawString(330, y, "Discount:")
        p.drawString(450, y, f"- ₹{order.discount_amount}")
        p.setFillColorRGB(0, 0, 0)
        y -= 15

    p.setFont("Helvetica-Bold", 11)
    p.drawString(330, y, "Final Amount:")
    p.drawString(450, y, f"₹{order.final_amount}")
    y -= 30

    # ================= FOOTER =================
    p.setFont("Helvetica-Oblique", 9)
    p.setFillColorRGB(0.3, 0.3, 0.3)
    p.drawString(50, y, "Thank you for shopping with Clothing Store!")
    p.drawString(50, y - 12, "This is a system generated invoice.")

    p.showPage()
    p.save()

    return response
