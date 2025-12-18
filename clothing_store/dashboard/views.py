from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum
from orders.models import Order
from django.db.models.functions import TruncMonth


@staff_member_required
def admin_dashboard(request):
    total_orders = Order.objects.count()
    total_revenue = Order.objects.filter(
        status__in=['paid', 'delivered']
    ).aggregate(total=Sum('total_amount'))['total'] or 0

    monthly_sales = (
        Order.objects
        .filter(status__in=['paid', 'delivered'])
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(total=Sum('total_amount'))
        .order_by('month')
    )

    months = [m['month'].strftime('%b %Y') for m in monthly_sales]
    totals = [float(m['total']) for m in monthly_sales]

    return render(request, 'dashboard/admin_dashboard.html', {
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'months': months,
        'totals': totals,
    })
