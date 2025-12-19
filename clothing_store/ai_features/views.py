from django.shortcuts import render, redirect
from .skin_tone.detector import detect_skin_tone
from .skin_tone.recommender import get_recommended_products

def ai_home(request):
    return render(request, "ai/upload.html")

def ai_result(request):
    if request.method == "POST":
        image = request.FILES.get("image")
        if not image:
            return redirect("ai_home")

        # Temporary save
        image_path = "media/temp.jpg"
        with open(image_path, "wb+") as f:
            for chunk in image.chunks():
                f.write(chunk)

        skin_tone = detect_skin_tone(image_path)

        products, colors = get_recommended_products(skin_tone)

        return render(request, "ai/result.html", {
            "skin_tone": skin_tone,
            "colors": colors,
            "products": products
        })

    return redirect("ai_home")
