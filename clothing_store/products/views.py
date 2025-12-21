from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Q
from django.contrib import messages
from django.http import JsonResponse

from .models import (
    Product, Category, ProductVariant,
    Review, Wishlist
)
from orders.models import OrderItem

# ✅ SAFE AI IMPORTS (READ-ONLY)
from ai_features.recommendations.personalized import (
    get_personalized_recommendations
)
from ai_features.reviews.sentiment import (
    analyze_review_sentiment
)
from ai_features.reviews.fake_detector import (
    detect_fake_review
)


# -------------------------
# PRODUCT LIST
# -------------------------
def product_list(request):
    category_id = request.GET.get('category')
    query = request.GET.get('q')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    products = (
        Product.objects
        .filter(is_active=True)
        .prefetch_related('images')
    )

    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(category__name__icontains=query)
        )

    if category_id:
        products = products.filter(category_id=category_id)

    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)

    categories = Category.objects.filter(is_active=True)

    return render(request, 'products/product_list.html', {
        'products': products,
        'categories': categories,
        'selected_category': category_id,
        'min_price': min_price,
        'max_price': max_price,
    })


# -------------------------
# PRODUCT DETAIL
# -------------------------
def product_detail(request, product_id):
    product = get_object_or_404(
        Product,
        id=product_id,
        is_active=True
    )

    images = product.images.all()
    variants = product.variants.all()
    reviews = product.reviews.select_related('user')

    # ⭐ Average Rating
    avg_rating = (
        reviews.aggregate(avg=Avg('rating'))['avg'] or 0
    )

    # -------------------------
    # 🔍 Review AI Enrichment
    # -------------------------
    enriched_reviews = []
    for review in reviews:
        # Sentiment analysis
        try:
            sentiment = analyze_review_sentiment(review.comment)
        except Exception:
            sentiment = {'label': 'Neutral', 'polarity': 0.0}

        # Fake review detection (rule-based)
        try:
            user_reviews = Review.objects.filter(user=review.user)
            fake_result = detect_fake_review(review, user_reviews)
        except Exception:
            fake_result = {
                'is_suspicious': False,
                'score': 0.0,
                'reasons': []
            }

        review.sentiment = sentiment
        review.fake = fake_result
        enriched_reviews.append(review)

    # -------------------------
    # Wishlist check
    # -------------------------
    in_wishlist = False
    if request.user.is_authenticated:
        in_wishlist = Wishlist.objects.filter(
            user=request.user,
            product=product
        ).exists()

    # -------------------------
    # Review eligibility
    # -------------------------
    can_review = False
    if request.user.is_authenticated:
        can_review = OrderItem.objects.filter(
            order__user=request.user,
            product=product
        ).exists()

    # -------------------------
    # 🔥 Personalized Recommendations
    # -------------------------
    personalized_products = []
    if request.user.is_authenticated:
        try:
            personalized_products = get_personalized_recommendations(
                request.user,
                limit=8
            )
        except Exception:
            personalized_products = []

    return render(request, 'products/product_detail.html', {
        'product': product,
        'images': images,
        'variants': variants,
        'reviews': enriched_reviews,
        'avg_rating': round(avg_rating, 1),
        'in_wishlist': in_wishlist,
        'can_review': can_review,
        'personalized_products': personalized_products,
    })


# -------------------------
# ADD REVIEW
# -------------------------
@login_required
def add_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if Review.objects.filter(
        user=request.user,
        product=product
    ).exists():
        messages.error(
            request,
            'You already reviewed this product.'
        )
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
    items = (
        Wishlist.objects
        .filter(user=request.user)
        .select_related('product')
    )

    return render(
        request,
        'products/wishlist.html',
        {'items': items}
    )


# -------------------------
# SEARCH SUGGESTIONS
# -------------------------
def search_suggestions(request):
    query = request.GET.get('q', '').strip()
    results = []

    if query:
        products = (
            Product.objects
            .filter(is_active=True)
            .filter(
                Q(name__icontains=query) |
                Q(category__name__icontains=query)
            )
            .prefetch_related('images', 'category')[:8]
        )

        for product in products:
            image_url = ""
            if product.images.first():
                image_url = product.images.first().image.url

            results.append({
                'id': product.id,
                'name': product.name,
                'category': product.category.name,
                'image': image_url
            })

    return JsonResponse({'results': results})
