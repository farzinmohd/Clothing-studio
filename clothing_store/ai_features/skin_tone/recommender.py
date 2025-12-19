from products.models import Product

<<<<<<< HEAD
# ==========================================
# CANONICAL COLOR MAP (single source of truth)
# ==========================================
COLOR_CANONICAL = {
    "beige": ["beige", "tan", "cream", "sand"],
    "blue": ["blue", "light blue", "sky blue", "navy", "royal"],
    "green": ["green", "olive", "dark green"],
    "maroon": ["maroon", "burgundy", "wine"],
    "white": ["white", "off white"],
    "black": ["black"],
    "brown": ["brown", "chocolate"],
    "yellow": ["yellow", "mustard"],
    "pink": ["pink", "peach"],
    "mint": ["mint"],
}

# ==========================================
# SKIN TONE → BASE COLORS
# ==========================================
SKIN_TONE_COLOR_MAP = {
    "Very Fair": ["blue", "pink", "grey"],
    "Fair": ["beige", "blue", "mint", "pink"],
    "Medium": ["green", "blue", "maroon", "white"],
    "Olive": ["mustard", "brown", "black", "green"],
    "Dark": ["yellow", "red", "blue", "white"],
}

# ==========================================
# NORMALIZE ANY COLOR STRING
# ==========================================
def normalize_color(value):
    if not value:
        return None

    value = value.lower().strip()

    for base, variants in COLOR_CANONICAL.items():
        if value in variants:
            return base

    return None

# ==========================================
# DETECT COLOR FROM NAME
# ==========================================
def detect_color_from_name(name):
    name = name.lower()
    for base, variants in COLOR_CANONICAL.items():
        for v in variants:
            if v in name:
                return base
    return None

# ==========================================
# MAIN RECOMMENDER
# ==========================================
def get_recommended_products(skin_tone, limit=6):
    allowed_base_colors = SKIN_TONE_COLOR_MAP.get(skin_tone, [])

    matched_products = []

    products = Product.objects.filter(is_active=True).prefetch_related(
        "images", "variants"
=======
# ===============================
# SKIN TONE → ALLOWED COLORS
# ===============================
SKIN_TONE_COLOR_MAP = {
    "Very Fair": ["blue", "lavender", "pink", "grey"],
    "Fair": ["peach", "beige", "light blue", "mint"],
    "Medium": ["green", "royal blue", "maroon", "white"],
    "Olive": ["mustard", "brown", "black", "olive"],
    "Dark": ["yellow", "red", "cobalt blue", "white"],
}

# ===============================
# COLOR NORMALIZATION MAP
# ===============================
COLOR_SYNONYMS = {
    "maroon": ["maroon", "burgundy", "wine"],
    "green": ["green", "olive", "dark green"],
    "blue": ["blue", "navy", "royal"],
    "white": ["white", "off white"],
    "black": ["black"],
    "brown": ["brown", "beige", "tan"],
    "yellow": ["yellow", "mustard"],
    "red": ["red"],
}

# ===============================
# NORMALIZE COLOR STRING
# ===============================
def normalize_color(color_value):
    if not color_value:
        return None

    color_value = color_value.lower().strip()

    for base_color, synonyms in COLOR_SYNONYMS.items():
        if color_value in synonyms:
            return base_color

    return None

# ===============================
# DETECT COLOR FROM NAME (fallback)
# ===============================
def detect_color_from_name(product_name):
    name = product_name.lower()
    for base_color, synonyms in COLOR_SYNONYMS.items():
        for word in synonyms:
            if word in name:
                return base_color
    return None

# ===============================
# MAIN AI RECOMMENDER
# ===============================
def get_recommended_products(skin_tone, limit=6):
    allowed_colors = SKIN_TONE_COLOR_MAP.get(skin_tone, [])
    allowed_colors = [c.lower() for c in allowed_colors]

    matched_products = []

    products = (
        Product.objects
        .filter(is_active=True)
        .prefetch_related("images", "variants")
>>>>>>> 701249c1ca4f61b7efe4b78928edbb12918f5117
    )

    for product in products:
        detected_colors = set()

        # 1️⃣ Product main color
        if product.color:
<<<<<<< HEAD
            c = normalize_color(product.color)
            if c:
                detected_colors.add(c)

        # 2️⃣ Variant colors
        for variant in product.variants.all():
            c = normalize_color(variant.color)
            if c:
                detected_colors.add(c)
=======
            normalized = normalize_color(product.color)
            if normalized:
                detected_colors.add(normalized)

        # 2️⃣ Variant colors
        for variant in product.variants.all():
            normalized = normalize_color(variant.color)
            if normalized:
                detected_colors.add(normalized)
>>>>>>> 701249c1ca4f61b7efe4b78928edbb12918f5117

        # 3️⃣ Name fallback
        name_color = detect_color_from_name(product.name)
        if name_color:
            detected_colors.add(name_color)

<<<<<<< HEAD
        # 4️⃣ Match
        if detected_colors.intersection(allowed_base_colors):
=======
        # 4️⃣ Match against allowed colors
        if detected_colors.intersection(allowed_colors):
>>>>>>> 701249c1ca4f61b7efe4b78928edbb12918f5117
            matched_products.append(product)

        if len(matched_products) >= limit:
            break

    return matched_products, allowed_base_colors
