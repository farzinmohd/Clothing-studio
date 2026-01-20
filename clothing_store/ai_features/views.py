from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from pathlib import Path
from .skin_tone.detector import detect_skin_tone
from .skin_tone.recommender import get_recommended_products
import os
import time
import random
# Virtual try-on imports moved to function level to avoid TensorFlow loading at startup
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .size_recommendation.model import predict_size
from accounts.models import UserMeasurements

# New Imports
from .recommendations.similarity import find_similar_products
from products.models import Product

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
    # time.sleep(random.randint(3, 6))

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
    Enhanced Virtual Try-On with Simple Overlay
    """
    result_image_url = None
    error_message = None
    products = Product.objects.filter(is_active=True)[:20]  # Get some products
    
    if request.method == "POST":
        person_image = request.FILES.get("person_image")
        product_id = request.POST.get("product_id")
        
        if not person_image:
            error_message = "Please upload your photo"
        elif not product_id:
            error_message = "Please select a product"
        else:
            try:
                # Lazy import to avoid loading TensorFlow at Django startup
                from ai_features.virtual_tryon.simple_overlay import virtual_tryon_simple
                
                # Save person image
                upload_dir = os.path.join(settings.MEDIA_ROOT, "virtual_tryon_uploads")
                os.makedirs(upload_dir, exist_ok=True)
                
                person_path = os.path.join(upload_dir, f"person_{time.time()}.jpg")
                with open(person_path, "wb+") as f:
                    for chunk in person_image.chunks():
                        f.write(chunk)
                
                # Get product garment image
                product = Product.objects.get(id=product_id)
                garment_path = product.images.first().image.path if product.images.exists() else None
                
                if not garment_path:
                    error_message = "Product image not found"
                else:
                    # Perform virtual try-on
                    result_dir = os.path.join(settings.MEDIA_ROOT, "virtual_tryon_results")
                    os.makedirs(result_dir, exist_ok=True)
                    
                    result_path = os.path.join(result_dir, f"result_{time.time()}.jpg")
                    
                    result_img, message = virtual_tryon_simple(
                        person_path, 
                        garment_path, 
                        output_path=result_path
                    )
                    
                    if result_img is not None:
                        # Convert path to URL
                        result_image_url = result_path.replace(settings.MEDIA_ROOT, settings.MEDIA_URL).replace("\\", "/")
                    else:
                        error_message = message
                        
            except Exception as e:
                error_message = f"Error: {str(e)}"
    
    return render(request, "ai/virtual_tryon_demo.html", {
        "products": products,
        "result_image_url": result_image_url,
        "error_message": error_message
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


# -------------------------
# 📸 VISUAL SEARCH
# -------------------------
def visual_search(request):
    if request.method == "POST" and request.FILES.get("image"):
        image = request.FILES["image"]
        
        # Save temp image
        upload_dir = os.path.join(settings.MEDIA_ROOT, "visual_search_tmp")
        os.makedirs(upload_dir, exist_ok=True)
        
        # Use a fixed name or unique name; here standardizing for simplicity in demos
        file_path = os.path.join(upload_dir, "query.jpg")
        
        with open(file_path, "wb+") as f:
            for chunk in image.chunks():
                f.write(chunk)
                
        # Run search
        try:
            # Get IDs of similar products
            product_ids = find_similar_products(file_path)
            
            # Fetch objects preserving order
            products = []
            for pid in product_ids:
                try:
                    products.append(Product.objects.get(id=pid))
                except Product.DoesNotExist:
                    pass
            
            return render(request, "ai/visual_search.html", {
                "products": products,
                "query_image_url": f"{settings.MEDIA_URL}visual_search_tmp/query.jpg?t={time.time()}" 
            })
            
        except Exception as e:
            # In production log this
            print(f"Visual Search Error: {e}")
            return render(request, "ai/visual_search.html", {
                "error": "Could not process image. Ensure AI models are built."
            })

    return render(request, "ai/visual_search.html")
