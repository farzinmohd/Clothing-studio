from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from django.contrib import messages

from .models import (
    Product, Category, ProductVariant,
    Review, Wishlist
)
from orders.models import OrderItem


# -------------------------
# PRODUCT LIST
# -------------------------
def product_list(request):
    category_id = request.GET.get('category')

    products = Product.objects.filter(is_active=True)
    if category_id:
        products = products.filter(category_id=category_id)

    categories = Category.objects.filter(is_active=True)

    return render(request, 'products/product_list.html', {
        'products': products,
        'categories': categories
    })


# -------------------------
# PRODUCT DETAIL
# -------------------------
def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)

    images = product.images.all()
    variants = product.variants.all()
    reviews = product.reviews.all()
    avg_rating = reviews.aggregate(avg=Avg('rating'))['avg'] or 0

    in_wishlist = False
    if request.user.is_authenticated:
        in_wishlist = Wishlist.objects.filter(
            user=request.user,
            product=product
        ).exists()

    can_review = False
    if request.user.is_authenticated:
        can_review = OrderItem.objects.filter(
            order__user=request.user,
            product=product
        ).exists()

    return render(request, 'products/product_detail.html', {
        'product': product,
        'images': images,
        'variants': variants,
        'reviews': reviews,
        'avg_rating': round(avg_rating, 1),
        'in_wishlist': in_wishlist,
        'can_review': can_review,
    })


# -------------------------
# ADD REVIEW
# -------------------------
@login_required
def add_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if Review.objects.filter(user=request.user, product=product).exists():
        messages.error(request, 'You already reviewed this product.')
        return redirect('product_detail', product_id=product.id)

    Review.objects.create(
        user=request.user,
        product=product,
        rating=request.POST.get('rating'),
        comment=request.POST.get('comment')
    )

    messages.success(request, 'Review added successfully.')
    return redirect('product_detail', product_id=product.id)


# -------------------------
# ADD TO WISHLIST
# -------------------------
@login_required
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    Wishlist.objects.get_or_create(
        user=request.user,
        product=product
    )

    messages.success(request, 'Added to wishlist ❤️')
    return redirect('product_detail', product_id=product.id)


# -------------------------
# REMOVE FROM WISHLIST
# -------------------------
@login_required
def remove_from_wishlist(request, product_id):
    Wishlist.objects.filter(
        user=request.user,
        product_id=product_id
    ).delete()

    messages.success(request, 'Removed from wishlist')
    return redirect('wishlist')


# -------------------------
# WISHLIST PAGE
# -------------------------
@login_required
def wishlist_view(request):
    items = Wishlist.objects.filter(user=request.user).select_related('product')

    return render(request, 'products/wishlist.html', {
        'items': items
    })
