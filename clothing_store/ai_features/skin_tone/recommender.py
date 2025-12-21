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
    "mint": ["mint", "aqua"],
}

# ==================================================
# SKIN TONE → ALLOWED BASE COLORS
# (expanded & realistic)
# ==================================================
SKIN_TONE_COLOR_MAP = {
    "Very Fair": ["blue", "pink", "white"],
    "Fair": ["beige", "blue", "mint", "pink"],
    "Medium": ["green", "blue", "maroon", "white"],
    "Olive": ["green", "brown", "black", "mustard"],
    "Dark": ["yellow", "red", "blue", "white"],
}

# ==================================================
# NORMALIZE ANY COLOR STRING → BASE COLOR
# (SOFT MATCHING, NOT STRICT)
# ==================================================
def normalize_color(value):
    if not value:
        return None

    value = value.lower()

    for base_color, variants in COLOR_CANONICAL.items():
        for v in variants:
            if v in value:      # 🔥 CONTAINS match
                return base_color

    return None

# ==================================================
# DETECT COLOR FROM TEXT (NAME / DESCRIPTION)
# ==================================================
def detect_color_from_text(text):
    if not text:
        return None

    text = text.lower()

    for base_color, variants in COLOR_CANONICAL.items():
        for v in variants:
            if v in text:
                return base_color

    return None

# ==================================================
# MAIN AI RECOMMENDER (SAFE + FLEXIBLE)
# ==================================================
def get_recommended_products(skin_tone):
    allowed_base_colors = SKIN_TONE_COLOR_MAP.get(skin_tone, [])

    matched_products = []

    products = (
        Product.objects
        .filter(is_active=True)
        .prefetch_related("images", "variants")
    )

    for product in products:
        detected_colors = set()

        # 1️⃣ Admin-selected product color
        if product.color:
            c = normalize_color(product.color)
            if c:
                detected_colors.add(c)

        # 2️⃣ Variant colors (SAFE)
        for variant in product.variants.all():
            color_value = getattr(variant, "color", None)
            if color_value:
                c = normalize_color(color_value)
                if c:
                    detected_colors.add(c)

        # 3️⃣ Product name scan
        name_color = detect_color_from_text(product.name)
        if name_color:
            detected_colors.add(name_color)

        # 4️⃣ Product description scan
        desc_color = detect_color_from_text(product.description)
        if desc_color:
            detected_colors.add(desc_color)

        # 5️⃣ Final soft match
        for color in detected_colors:
            if color in allowed_base_colors:
                matched_products.append(product)
                break

    return matched_products, allowed_base_colors

