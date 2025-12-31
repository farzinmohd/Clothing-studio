from django.shortcuts import render, redirect
from django.conf import settings
from pathlib import Path
from .skin_tone.detector import detect_skin_tone
from .skin_tone.recommender import get_recommended_products
import os
import time
import random
from ai_features.virtual_tryon.pose_detect import detect_shoulders
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .size_recommendation.model import predict_size
from accounts.models import UserMeasurements

def ai_home(request):
    return render(request, "ai/ai_home.html")


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
    pose_data = None

    if request.method == "POST" and request.FILES.get("image"):
        img = request.FILES["image"]
        path = f"media/tmp/{img.name}"
        
        # Ensure dir exists
        os.makedirs(os.path.dirname(path), exist_ok=True)

        with open(path, "wb+") as f:
            for chunk in img.chunks():
                f.write(chunk)

        pose_data = detect_shoulders(path)

    return render(request, "ai/virtual_tryon_demo.html", {
        "pose_data": pose_data
    })

# -------------------------
# 📏 SIZE RECOMMENDATION API
# -------------------------
@csrf_exempt
def predict_size_api(request):
    """
    API: POST /ai/predict-size/
    JSON Body: { "height": 180, "weight": 75, "age": 25, "gender": "M" }
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            
            height = float(data.get("height"))
            weight = float(data.get("weight"))
            age = int(data.get("age"))
            gender = data.get("gender") # 'M' or 'F'
            
            if gender not in ['M', 'F']:
                gender = 'M' # Default fallback
            
            size, confidence = predict_size(height, weight, age, gender)
            
            # Save to user profile if logged in
            if request.user.is_authenticated:
                UserMeasurements.objects.update_or_create(
                    user=request.user,
                    defaults={
                        'height_cm': height,
                        'weight_kg': weight,
                        'age': age,
                        'gender': gender
                    }
                )

            return JsonResponse({
                "status": "success",
                "recommended_size": size,
                "confidence": confidence
            })

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

    return JsonResponse({"status": "error", "message": "Invalid method"}, status=405)
