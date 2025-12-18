from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.shortcuts import render

from orders.models import Order


@staff_member_required
def admin_dashboard(request):
    # ================= SUMMARY =================
    total_users = User.objects.count()
    total_orders = Order.objects.count()

    total_revenue = (
        Order.objects
        .filter(status__in=['paid', 'shipped', 'delivered'])
        .aggregate(total=Sum('total_amount'))['total'] or 0
    )

    # ================= ORDERS BY STATUS =================
    status_data = (
        Order.objects
        .values('status')
        .annotate(count=Count('id'))
    )

    # ================= MONTHLY SALES =================
    monthly_sales = (
        Order.objects
        .filter(status__in=['paid', 'shipped', 'delivered'])
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(total=Sum('total_amount'))
        .order_by('month')
    )

    # Convert queryset → JS friendly lists
    months = [m['month'].strftime('%b %Y') for m in monthly_sales]
    totals = [float(m['total']) for m in monthly_sales]

    context = {
        'total_users': total_users,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'status_data': status_data,   # ✅ MATCHES TEMPLATE
        'months': months,             # ✅ MATCHES TEMPLATE
        'totals': totals,             # ✅ MATCHES TEMPLATE
    }

    return render(request, 'dashboard/admin_dashboard.html', context)
