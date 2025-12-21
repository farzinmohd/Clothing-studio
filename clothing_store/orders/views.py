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
from products.models import ProductVariant
from .models import Order, OrderItem, Coupon

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

        if not address_id:
            messages.error(request, 'Please select a delivery address')
            return redirect('checkout')

        selected_address = get_object_or_404(
            Address, id=address_id, user=request.user
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
        # ✅ CREATE ORDER ITEMS + REDUCE VARIANT STOCK
        # -----------------------------
        for item in cart:
            try:
                variant = ProductVariant.objects.get(
                    product=item['product'],
                    size=item['size']
                )
            except ProductVariant.DoesNotExist:
                messages.error(request, 'Selected size is no longer available')
                return redirect('cart_detail')

            if variant.stock < item['quantity']:
                messages.error(request, 'Insufficient stock for selected size')
                return redirect('cart_detail')

            OrderItem.objects.create(
                order=order,
                product=item['product'],
                size=item['size'],
                color=None,  # ✅ color is optional (backward safe)
                quantity=item['quantity'],
                price=item['price']
            )

            # 🔥 Reduce variant stock (CORRECT WAY)
            variant.stock -= item['quantity']
            variant.save()

        # -----------------------------
        # 🔥 STRIPE PAYMENT
        # -----------------------------
        if payment_method == 'ONLINE':
            try:
                session = stripe.checkout.Session.create(
                    payment_method_types=['card'],
                    line_items=[{
                        'price_data': {
                            'currency': 'inr',
                            'product_data': {
                                'name': f'Order #{order.id}',
                            },
                            'unit_amount': int(final_amount * 100),
                        },
                        'quantity': 1,
                    }],
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
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'orders/my_orders.html', {'orders': orders})


# ----------------------------------
# ORDER DETAIL PAGE
# ----------------------------------
@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/order_detail.html', {'order': order})


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


# ----------------------------------
# DOWNLOAD INVOICE (PDF)
# ----------------------------------
@login_required
def download_invoice(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{order.id}.pdf"'

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    y = height - 40

    # ================= HEADER =================
    p.setFillColorRGB(0.15, 0.35, 0.75)
    p.rect(0, height - 90, width, 90, fill=1)

    p.setFillColorRGB(1, 1, 1)
    p.setFont("Helvetica-Bold", 22)
    p.drawString(40, height - 55, "CLOTHING STORE")

    p.setFont("Helvetica", 10)
    p.drawRightString(width - 40, height - 50, "INVOICE")

    p.setFont("Helvetica", 9)
    p.drawRightString(width - 40, height - 70, f"Order ID: #{order.id}")
    p.drawRightString(
        width - 40, height - 85,
        f"Date: {order.created_at.strftime('%d %b %Y')}"
    )

    y -= 110
    p.setFillColorRGB(0, 0, 0)

    # ================= CUSTOMER INFO =================
    p.setFont("Helvetica-Bold", 11)
    p.drawString(40, y, "BILL TO")
    p.line(40, y - 2, 250, y - 2)

    y -= 18
    p.setFont("Helvetica", 10)
    p.drawString(40, y, order.address.full_name)
    y -= 14
    p.drawString(40, y, order.address.address_line)
    y -= 14
    p.drawString(
        40, y,
        f"{order.address.city}, {order.address.state} - {order.address.postal_code}"
    )
    y -= 14
    p.drawString(40, y, f"Phone: {order.address.phone}")

    # ================= ORDER INFO =================
    right_x = width - 250
    p.setFont("Helvetica-Bold", 11)
    p.drawString(right_x, height - 200, "ORDER INFO")
    p.line(right_x, height - 202, width - 40, height - 202)

    p.setFont("Helvetica", 10)
    p.drawString(right_x, height - 220, f"Payment: {order.payment_method}")
    p.drawString(
        right_x, height - 235,
        f"Status: {order.status.title()}"
    )

    y -= 40

    # ================= TABLE HEADER =================
    p.setFillColorRGB(0.93, 0.93, 0.93)
    p.rect(40, y, width - 80, 22, fill=1)

    p.setFillColorRGB(0, 0, 0)
    p.setFont("Helvetica-Bold", 10)
    p.drawString(45, y + 7, "Product")
    p.drawString(260, y + 7, "Variant")
    p.drawString(360, y + 7, "Qty")
    p.drawString(420, y + 7, "Price")

    y -= 25
    p.setFont("Helvetica", 10)

    # ================= ORDER ITEMS =================
    for item in order.items.all():
        if y < 120:
            p.showPage()
            y = height - 80

        p.drawString(45, y, item.product.name)

        variant_text = item.size
        if item.color:
            variant_text += f" / {item.color}"

        p.drawString(260, y, variant_text)
        p.drawRightString(385, y, str(item.quantity))
        p.drawRightString(480, y, f"₹{item.price}")

        y -= 18

    # ================= TOTALS =================
    y -= 10
    p.line(260, y, width - 40, y)
    y -= 18

    p.setFont("Helvetica", 10)
    p.drawString(300, y, "Subtotal:")
    p.drawRightString(480, y, f"₹{order.total_amount}")
    y -= 14

    if order.discount_amount > 0:
        p.setFillColorRGB(0.75, 0, 0)
        p.drawString(300, y, "Discount:")
        p.drawRightString(480, y, f"- ₹{order.discount_amount}")
        p.setFillColorRGB(0, 0, 0)
        y -= 14

    p.setFont("Helvetica-Bold", 11)
    p.drawString(300, y, "Final Amount:")
    p.drawRightString(480, y, f"₹{order.final_amount}")

    # ================= FOOTER =================
    y -= 40
    p.setFont("Helvetica-Oblique", 9)
    p.setFillColorRGB(0.35, 0.35, 0.35)
    p.drawCentredString(
        width / 2, y,
        "Thank you for shopping with Clothing Store"
    )
    p.drawCentredString(
        width / 2, y - 12,
        "This is a system generated invoice"
    )

    p.showPage()
    p.save()
    return response
