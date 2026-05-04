from products.models import Product
from orders.models import Order

def stock_alerts(request):
    """
    Context processor to inject low stock, out-of-stock products,
    and return requests into the admin dashboard templates.
    """
    if request.user.is_authenticated and request.user.is_staff:
        # 1. Fetch products with stock < 5
        alert_products = Product.objects.filter(stock__lt=5, is_active=True).order_by('stock')
        
        out_of_stock = []
        low_stock = []
        
        for p in alert_products:
            if p.stock == 0:
                out_of_stock.append(p)
            else:
                low_stock.append(p)
                
        # 2. Fetch return requests
        return_requests = Order.objects.filter(status='return_requested').order_by('-updated_at')
        
        total_alerts = len(out_of_stock) + len(low_stock) + len(return_requests)
        
        return {
            'out_of_stock_products': out_of_stock,
            'low_stock_products': low_stock,
            'return_requests': return_requests,
            'total_alerts': total_alerts,
        }
    return {}
