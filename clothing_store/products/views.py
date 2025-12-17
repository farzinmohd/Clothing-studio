from django.shortcuts import render, get_object_or_404
from .models import Product, Category


# -------------------------
# PRODUCT LIST PAGE
# -------------------------
def product_list(request):
    category_id = request.GET.get('category')

    products = Product.objects.filter(is_active=True)

    if category_id:
        products = products.filter(category_id=category_id)

    categories = Category.objects.filter(is_active=True)

    context = {
        'products': products,
        'categories': categories
    }
    return render(request, 'products/product_list.html', context)


# -------------------------
# PRODUCT DETAIL PAGE
# -------------------------
def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    images = product.images.all()

    context = {
        'product': product,
        'images': images
    }
    return render(request, 'products/product_detail.html', context)
