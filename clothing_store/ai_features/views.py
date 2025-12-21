from django.shortcuts import render, redirect
from django.conf import settings
from pathlib import Path
from .skin_tone.detector import detect_skin_tone
from .skin_tone.recommender import get_recommended_products
import os
import time
import random
from ai_features.virtual_tryon.pose_detect import detect_shoulders


def ai_home(request):
    return render(request, "ai/upload.html")


def ai_result(request):
    if request.method != "POST":
        return redirect("ai_home")

    image = request.FILES.get("image")
    if not image:
        return redirect("ai_home")

    # 📂 Save uploaded image
    upload_dir = os.path.join(settings.MEDIA_ROOT, "ai_uploads")
    os.makedirs(upload_dir, exist_ok=True)

    image_path = os.path.join(upload_dir, "temp.jpg")
    with open(image_path, "wb+") as f:
        for chunk in image.chunks():
            f.write(chunk)

    # ⏳ Fake AI thinking time (3–6 sec)
    time.sleep(random.randint(3, 6))

    # 🧠 AI detection
    skin_tone, boxed_image_path = detect_skin_tone(image_path)

    # 🎯 Product recommendations
    products, colors = get_recommended_products(skin_tone)

    # 🖼 Convert boxed image path → URL
    if boxed_image_path:
        boxed_image_path = Path(boxed_image_path)  # 🔑 FIX
        boxed_image_url = boxed_image_path.relative_to(
            settings.MEDIA_ROOT
        ).as_posix()
    else:
        boxed_image_url = None

    return render(request, "ai/result.html", {
        "skin_tone": skin_tone,
        "colors": colors,
        "products": products,
        "boxed_image": boxed_image_url
    })

def virtual_tryon_demo(request):
    """
    Concept-level Virtual Try-On demo page.
    No OpenCV runs here.
    This is for UI + future scope demonstration only.
    """
    return render(request, 'ai/virtual_tryon_demo.html')


def virtual_tryon_demo(request):
    pose_data = None

    if request.method == "POST" and request.FILES.get("image"):
        img = request.FILES["image"]
        path = f"media/tmp/{img.name}"

        with open(path, "wb+") as f:
            for chunk in img.chunks():
                f.write(chunk)

        pose_data = detect_shoulders(path)

    return render(request, "ai/virtual_tryon_demo.html", {
        "pose_data": pose_data
    })
