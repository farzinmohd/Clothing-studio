import os
import time
import random
from django.conf import settings
from django.shortcuts import render, redirect

from .skin_tone.detector import detect_skin_tone
from .skin_tone.recommender import get_recommended_products


def ai_home(request):
    """
    AI upload page
    """
    return render(request, "ai/upload.html")


def ai_result(request):
    """
    Handle image upload → AI processing → recommendations
    """
    if request.method != "POST":
        return redirect("ai_home")

    image = request.FILES.get("image")
    if not image:
        return redirect("ai_home")

    # ===============================
    # 1️⃣ SAVE IMAGE TEMPORARILY
    # ===============================
    ai_media_path = os.path.join(settings.MEDIA_ROOT, "ai_uploads")
    os.makedirs(ai_media_path, exist_ok=True)

    image_path = os.path.join(ai_media_path, image.name)

    with open(image_path, "wb+") as destination:
        for chunk in image.chunks():
            destination.write(chunk)

    # ===============================
    # 2️⃣ AI PROCESSING DELAY (REAL FEEL)
    # ===============================
    time.sleep(random.uniform(3, 6))  # ⏳ realistic AI wait

    # ===============================
    # 3️⃣ SKIN TONE DETECTION
    # ===============================
    skin_tone = detect_skin_tone(image_path)

    # ===============================
    # 4️⃣ PRODUCT RECOMMENDATION
    # ===============================
    products, colors = get_recommended_products(skin_tone)

    # ===============================
    # 5️⃣ RENDER RESULT PAGE
    # ===============================
    return render(request, "ai/result.html", {
        "skin_tone": skin_tone,
        "colors": colors,
        "products": products,
    })
