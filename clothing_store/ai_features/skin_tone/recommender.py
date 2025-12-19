from products.models import Product

# ===============================
# SKIN TONE → ALLOWED COLORS
# (Normalized to PRODUCT COLORS)
# ===============================
SKIN_TONE_COLOR_MAP = {
    "Very Fair": ["Blue", "Pink", "Grey"],
    "Fair": ["Beige", "Blue", "Green"],
    "Medium": ["Green", "Blue", "Maroon", "White"],
    "Olive": ["Mustard", "Brown", "Black", "Green"],
    "Dark": ["Yellow", "Red", "Blue", "White"],
}

# ===============================
# NLP COLOR KEYWORDS
# ===============================
COLOR_KEYWORDS = {
    "Green": ["green", "olive"],
    "Blue": ["blue", "navy", "royal", "cobalt"],
    "Red": ["red", "maroon"],
    "White": ["white"],
    "Black": ["black"],
    "Yellow": ["yellow", "mustard"],
    "Brown": ["brown", "beige"],
    "Pink": ["pink"],
}

# ===============================
# NLP COLOR DETECTION
# ===============================
def detect_color_from_name(product_name):
    name = product_name.lower()
    for color, keywords in COLOR_KEYWORDS.items():
        for word in keywords:
            if word in name:
                return color
    return None

# ===============================
# FINAL AI RECOMMENDER
# ===============================
def get_recommended_products(skin_tone, limit=6):
    allowed_colors = SKIN_TONE_COLOR_MAP.get(skin_tone, [])

    matched_products = []

    products = Product.objects.filter(
        is_active=True
    ).prefetch_related("images")

    for product in products:
        # 1️⃣ Use admin-defined color
        product_color = product.color

        # 2️⃣ Validate admin color against AI rules
        if product_color in allowed_colors:
            matched_products.append(product)

        # 3️⃣ NLP fallback if admin color doesn't match
        else:
            detected_color = detect_color_from_name(product.name)
            if detected_color in allowed_colors:
                matched_products.append(product)

        if len(matched_products) >= limit:
            break

    return matched_products, allowed_colors
