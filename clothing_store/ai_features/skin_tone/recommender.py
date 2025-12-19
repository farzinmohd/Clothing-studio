from products.models import Product

# ==================================================
# CANONICAL COLOR MAP (single source of truth)
# ==================================================
COLOR_CANONICAL = {
    "beige": ["beige", "tan", "cream", "sand"],
    "blue": ["blue", "light blue", "sky blue", "navy", "royal", "cobalt"],
    "green": ["green", "olive", "dark green"],
    "maroon": ["maroon", "burgundy", "wine"],
    "white": ["white", "off white"],
    "black": ["black"],
    "brown": ["brown", "chocolate"],
    "yellow": ["yellow", "mustard"],
    "pink": ["pink", "peach"],
    "mint": ["mint"],
}

# ==================================================
# SKIN TONE → ALLOWED BASE COLORS
# ==================================================
SKIN_TONE_COLOR_MAP = {
    "Very Fair": ["blue", "pink", "white"],
    "Fair": ["beige", "blue", "mint", "pink"],
    "Medium": ["green", "blue", "maroon", "white"],
    "Olive": ["mustard", "brown", "black", "green"],
    "Dark": ["yellow", "red", "blue", "white"],
}

# ==================================================
# NORMALIZE ANY COLOR STRING → BASE COLOR
# ==================================================
def normalize_color(value):
    if not value:
        return None

    value = value.lower().strip()

    for base_color, variants in COLOR_CANONICAL.items():
        if value in variants:
            return base_color

    return None

# ==================================================
# DETECT COLOR FROM PRODUCT NAME (fallback NLP)
# ==================================================
def detect_color_from_name(name):
    name = name.lower()
    for base_color, variants in COLOR_CANONICAL.items():
        for v in variants:
            if v in name:
                return base_color
    return None

# ==================================================
# MAIN AI RECOMMENDER (HYBRID RULE-BASED)
# ==================================================
def get_recommended_products(skin_tone, limit=6):
    allowed_base_colors = SKIN_TONE_COLOR_MAP.get(skin_tone, [])
    matched_products = []

    products = (
        Product.objects
        .filter(is_active=True)
        .prefetch_related("images", "variants")
    )

    for product in products:
        detected_colors = set()

        # 1️⃣ Product main color (admin selected)
        if product.color:
            c = normalize_color(product.color)
            if c:
                detected_colors.add(c)

        # 2️⃣ Variant colors
        for variant in product.variants.all():
            c = normalize_color(variant.color)
            if c:
                detected_colors.add(c)

        # 3️⃣ Name-based fallback
        name_color = detect_color_from_name(product.name)
        if name_color:
            detected_colors.add(name_color)

        # 4️⃣ Match against allowed colors
        if detected_colors.intersection(allowed_base_colors):
            matched_products.append(product)

        if len(matched_products) >= limit:
            break

    return matched_products, allowed_base_colors
