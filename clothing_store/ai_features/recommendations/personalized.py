from collections import Counter
from products.models import Product, Wishlist
from orders.models import OrderItem


def get_personalized_recommendations(user, limit=8):
    """
    SAFE Personalized Recommendation Engine

    Signals used:
    - Wishlist (strong)
    - Purchase history (stronger)
    - Category preference
    - Color preference

    ⚠️ Does NOT modify data
    ⚠️ Does NOT affect cart / orders / admin
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

    # 🔁 Fallback: no behavior at all
    if not wishlisted_products.exists() and not ordered_items.exists():
        return Product.objects.filter(
            is_active=True
        ).order_by('-created_at')[:limit]

    # -------------------------
    # 2. Extract preferences
    # -------------------------

    category_counter = Counter()
    color_counter = Counter()
    excluded_product_ids = set()

    # ❤️ Wishlist signal
    for item in wishlisted_products:
        product = item.product
        excluded_product_ids.add(product.id)

        if product.category_id:
            category_counter[product.category_id] += 2

        if product.color:
            color_counter[product.color] += 2

    # 🛒 Purchase signal (stronger)
    for item in ordered_items:
        product = item.product
        excluded_product_ids.add(product.id)

        if product.category_id:
            category_counter[product.category_id] += 3

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
    # 4. Build recommendation query
    # -------------------------

    recommendations = Product.objects.filter(
        is_active=True
    ).exclude(
        id__in=excluded_product_ids
    )

    # Apply category preference if exists
    if top_categories:
        recommendations = recommendations.filter(
            category_id__in=top_categories
        )

    # Apply color preference if exists
    if top_colors:
        recommendations = recommendations.filter(
            color__in=top_colors
        )

    # -------------------------
    # 5. Final fallback safety
    # -------------------------

    if not recommendations.exists():
        recommendations = Product.objects.filter(
            is_active=True
        ).exclude(
            id__in=excluded_product_ids
        )

    return recommendations.order_by('-created_at')[:limit]
