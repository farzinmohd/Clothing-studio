from products.models import Product

def stock_alerts(request):
    """
    Context processor to inject low stock and out-of-stock products
    into the admin dashboard templates.
    """
    if request.user.is_authenticated and request.user.is_staff:
        # Fetch products with stock < 5
        alert_products = Product.objects.filter(stock__lt=5, is_active=True).order_by('stock')
        
        out_of_stock = []
        low_stock = []
        
        for p in alert_products:
            if p.stock == 0:
                out_of_stock.append(p)
            else:
                low_stock.append(p)
                
        total_alerts = len(out_of_stock) + len(low_stock)
        
        return {
            'out_of_stock_products': out_of_stock,
            'low_stock_products': low_stock,
            'total_stock_alerts': total_alerts,
        }
    return {}
