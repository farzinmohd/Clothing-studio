from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.shortcuts import render
from django.http import HttpResponse

import csv
from reportlab.pdfgen import canvas

from orders.models import Order, OrderItem


# ================= ADMIN DASHBOARD =================
@staff_member_required
def admin_dashboard(request):
    total_users = User.objects.count()
    total_orders = Order.objects.count()

    total_revenue = (
        Order.objects
        .filter(status__in=['paid', 'shipped', 'delivered'])
        .aggregate(total=Sum('total_amount'))['total'] or 0
    )

    # Orders by status
    status_data = (
        Order.objects
        .values('status')
        .annotate(count=Count('id'))
    )

    # Monthly sales
    monthly_sales = (
        Order.objects
        .filter(status__in=['paid', 'shipped', 'delivered'])
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(total=Sum('total_amount'))
        .order_by('month')
    )

    months = [m['month'].strftime('%b %Y') for m in monthly_sales]
    totals = [float(m['total']) for m in monthly_sales]

    # Top selling products
    top_products = (
        OrderItem.objects
        .values('product__name')
        .annotate(total_qty=Sum('quantity'))
        .order_by('-total_qty')[:5]
    )

    context = {
        'total_users': total_users,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'status_data': status_data,
        'months': months,
        'totals': totals,
        'top_products': top_products,
    }

    return render(request, 'dashboard/admin_dashboard.html', context)


# ================= PDF REPORT =================
@staff_member_required
def sales_report_pdf(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="sales_report.pdf"'

    p = canvas.Canvas(response)
    p.setFont("Helvetica", 12)

    y = 800
    p.drawString(200, y, "Sales Report")
    y -= 40

    orders = Order.objects.all()

    for order in orders:
        line = f"Order #{order.id} | {order.user} | ₹{order.total_amount} | {order.status}"
        p.drawString(50, y, line)
        y -= 20

        if y < 50:
            p.showPage()
            y = 800

    p.showPage()
    p.save()
    return response


# ================= EXCEL (CSV) REPORT =================
@staff_member_required
def sales_report_excel(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sales_report.csv"'

    writer = csv.writer(response)
    writer.writerow(['Order ID', 'User', 'Total Amount', 'Status', 'Date'])

    orders = Order.objects.all()
    for order in orders:
        writer.writerow([
            order.id,
            order.user.username,
            order.total_amount,
            order.status,
            order.created_at.strftime('%Y-%m-%d')
        ])

    return response
