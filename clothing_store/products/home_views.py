from django.shortcuts import render
from django.db.models import Count
from .models import Product

def home(request):
    # ⭐ Recommended products (most wishlisted)
    recommended_products = Product.objects.filter(
        is_active=True
    ).annotate(
        wishlist_count=Count('wishlisted_products')
    ).order_by('-wishlist_count', '-created_at')[:8]

    # 🆕 Latest products
    latest_products = Product.objects.filter(
        is_active=True
    ).order_by('-created_at')[:8]

    return render(request, 'home.html', {
        'recommended_products': recommended_products,
        'latest_products': latest_products,
    })
