from collections import Counter
from products.models import Product, Wishlist
from orders.models import OrderItem


def get_personalized_recommendations(user, limit=8):
    """
    Recommend products based on:
    - Wishlist history
    - Purchase history
    - Category & color preference
    """

    # -------------------------
    # 1. Collect user behavior
    # -------------------------

    wishlisted_products = Wishlist.objects.filter(
        user=user
    ).select_related('product')

    ordered_items = OrderItem.objects.filter(
        order__user=user
    ).select_related('product')

    if not wishlisted_products.exists() and not ordered_items.exists():
        # Fallback: latest products
        return Product.objects.filter(is_active=True).order_by('-created_at')[:limit]

    # -------------------------
    # 2. Extract preferences
    # -------------------------

    category_counter = Counter()
    color_counter = Counter()
    excluded_product_ids = set()

    for item in wishlisted_products:
        product = item.product
        excluded_product_ids.add(product.id)

        if product.category:
            category_counter[product.category_id] += 2  # wishlist = strong signal
        if product.color:
            color_counter[product.color] += 2

    for item in ordered_items:
        product = item.product
        excluded_product_ids.add(product.id)

        if product.category:
            category_counter[product.category_id] += 3  # purchase = stronger signal
        if product.color:
            color_counter[product.color] += 3

    # -------------------------
    # 3. Determine top preferences
    # -------------------------

    top_categories = [
        cat_id for cat_id, _ in category_counter.most_common(3)
    ]

    top_colors = [
        color for color, _ in color_counter.most_common(3)
    ]

    # -------------------------
    # 4. Recommend products
    # -------------------------

    recommendations = Product.objects.filter(
        is_active=True,
        category_id__in=top_categories
    ).exclude(
        id__in=excluded_product_ids
    )

    if top_colors:
        recommendations = recommendations.filter(
            color__in=top_colors
        )

    return recommendations.order_by('-created_at')[:limit]

