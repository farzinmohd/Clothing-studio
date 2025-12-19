from django.shortcuts import render, redirect
from django.core.files.storage import FileSystemStorage

from .skin_tone.detector import detect_skin_tone
from .skin_tone.recommender import get_recommended_products

def ai_home(request):
    return render(request, "ai/ai_home.html")


def ai_result(request):
    if request.method != "POST":
        return redirect("ai_home")

    image_file = request.FILES.get("image")
    if not image_file:
        return redirect("ai_home")

    # Save image
    fs = FileSystemStorage()
    filename = fs.save(image_file.name, image_file)
    image_path = fs.path(filename)

    # 🔥 REAL AI STEP
    skin_tone = detect_skin_tone(image_path)

    # Product recommendation
    products, colors = get_recommended_products(skin_tone)

    return render(request, "ai/result.html", {
        "image_url": fs.url(filename),
        "skin_tone": skin_tone,
        "colors": colors,
        "products": products
    })
