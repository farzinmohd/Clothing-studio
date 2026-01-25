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
from django.db.models import Q
from .recommendations.similarity import find_similar_products
from products.models import Product, Category

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
                
        # Run search with COLOR-FIRST approach
        try:
            # STEP 1: Detect dominant color from uploaded image
            from .recommendations.color_detector import detect_dominant_color
            detected_color, rgb_values = detect_dominant_color(file_path)
            
            print(f"🎨 Detected color: {detected_color} (RGB: {rgb_values})")
            
            # STEP 2: Filter products by detected color
            from products.models import Product
            
            # Get products matching the detected color
            color_filtered_products = Product.objects.filter(
                is_active=True,
                color__iexact=detected_color  # Case-insensitive exact match
            )
            
            # If no exact matches, try products with None color (will use image features)
            if not color_filtered_products.exists():
                print(f"⚠️ No products with color='{detected_color}', using all products")
                color_filtered_products = Product.objects.filter(is_active=True)
            else:
                print(f"✅ Found {color_filtered_products.count()} products with color='{detected_color}'")
            
            # STEP 3: Get IDs of color-filtered products
            allowed_product_ids = set(color_filtered_products.values_list('id', flat=True))
            
            # STEP 4: Run similarity search
            results = find_similar_products(file_path, return_scores=True, top_k=20)
            
            # STEP 5: Filter results to only include products with matching color
            products_with_scores = []
            for pid, confidence in results:
                if pid in allowed_product_ids:
                    try:
                        product = Product.objects.get(id=pid)
                        products_with_scores.append({
                            'product': product,
                            'confidence': confidence
                        })
                    except Product.DoesNotExist:
                        pass
            
            # If we have too few results, add more from similarity search (without color filter)
            if len(products_with_scores) < 6:
                print(f"⚠️ Only {len(products_with_scores)} color-matched products, adding more from similarity")
                for pid, confidence in results:
                    if pid not in allowed_product_ids:
                        try:
                            product = Product.objects.get(id=pid)
                            products_with_scores.append({
                                'product': product,
                                'confidence': confidence * 0.7  # Reduce confidence for non-color-matched
                            })
                            if len(products_with_scores) >= 6:
                                break
                        except Product.DoesNotExist:
                            pass
            
            return render(request, "ai/visual_search.html", {
                "products_with_scores": products_with_scores[:6],  # Top 6 results
                "query_image_url": f"{settings.MEDIA_URL}visual_search_tmp/query.jpg?t={time.time()}",
                "has_results": len(products_with_scores) > 0,
                "detected_color": detected_color  # Pass to template for display
            })
            
        except Exception as e:
            # In production log this
            print(f"Visual Search Error: {e}")
            import traceback
            traceback.print_exc()
            return render(request, "ai/visual_search.html", {
                "error": f"Could not process image: {str(e)}"
            })

    return render(request, "ai/visual_search.html")


from .models import FAQ
import re

@csrf_exempt
def chatbot_response(request):
    """
    Simple chatbot logic: keyword matching from FAQ database.
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_msg = data.get("message", "").lower().strip()
            
            if not user_msg:
                return JsonResponse({"response": "I didn't catch that. Could you please rephrase?"})

            user_msg_clean = re.sub(r'[^\w\s]', '', user_msg)
            user_words = set(user_msg_clean.split())
            
            if not user_words:
                return JsonResponse({"response": "I didn't catch that. Could you please rephrase?"})

            # 1. Stemming & Synonym Preparation
            synonyms = {
                'ai': 'stylist',
                'bot': 'stylist',
                'delivery': 'shipping',
                'cost': 'shipping',
                'price': 'shipping',
                'pay': 'payment',
                'money': 'payment',
                'card': 'payment',
                'return': 'returns',
                'policy': 'returns',
                'cancel': 'cancellation',
                'stop': 'cancellation',
                'discount': 'coupon',
                'promo': 'coupon',
                'code': 'coupon',
                'size': 'sizing',
                'fit': 'sizing',
                'large': 'sizing',
                'small': 'sizing',
            }
            
            def stem_word(w):
                if len(w) <= 3: return w
                if w.endswith('ing'): return w[:-3]
                if w.endswith('ed'): return w[:-2]
                if w.endswith('es') and not w.endswith('ss'): return w[:-2]
                if w.endswith('s') and not w.endswith('ss'): return w[:-1]
                return w

            stemmed_user_words = {stem_word(w) for w in user_words}
            expanded_user_intent = set(stemmed_user_words)
            for w in user_words:
                if w in synonyms:
                    expanded_user_intent.add(stem_word(synonyms[w]))

            # 2. Check for Product Discovery Intent (High Priority)
            discovery_keywords = {'show', 'find', 'search', 'buy', 'look', 'want', 'need', 'browse'}
            if any(w in expanded_user_intent for w in discovery_keywords):
                # Extract search terms using stemmed words for plural handling
                search_keywords = [stem_word(w) for w in user_words if w not in discovery_keywords and w not in {'me', 'for', 'the', 'a', 'an', 'some', 'any', 'i'}]
                
                if search_keywords:
                    query = Q()
                    for word in search_keywords:
                        word_query = (
                            Q(name__icontains=word) |
                            Q(description__icontains=word) |
                            Q(category__name__icontains=word) |
                            Q(tags__icontains=word) |
                            Q(color__icontains=word)
                        )
                        if query:
                            query &= word_query
                        else:
                            query = word_query
                    
                    products = Product.objects.filter(query, is_active=True).distinct()[:10]
                    
                    if products.exists():
                        product_list = []
                        for p in products:
                            image_url = ""
                            if p.images.exists():
                                image_url = p.images.first().image.url
                            
                            product_list.append({
                                "id": p.id,
                                "name": p.name,
                                "price": str(p.price),
                                "image": image_url,
                                "url": f"/products/{p.id}/" # Standard URL pattern
                            })
                        
                        return JsonResponse({
                            "response": f"I found some items you might like! Have a look at these:",
                            "products": product_list
                        })
                    else:
                        return JsonResponse({
                            "response": f"I couldn't find any products matching those keywords. Try searching for something else, like 'blue shirts' or 'linen'!"
                        })

            # 2. Check for Order Status Intent (High Priority)
            order_keywords = {'status', 'track', 'where', 'order'}
            if any(w in expanded_user_intent for w in order_keywords):
                if not request.user.is_authenticated:
                    return JsonResponse({"response": "I can certainly help with that! Please **Log In** to your account so I can look up your order status for you."})
                
                try:
                    from orders.models import Order
                    latest_order = Order.objects.filter(user=request.user).latest('created_at')
                    
                    status_colors = {
                        'pending': '⏳ Pending',
                        'paid': '💳 Paid',
                        'shipped': '🚚 Shipped',
                        'delivered': '✅ Delivered',
                        'cancelled': '❌ Cancelled'
                    }
                    display_status = status_colors.get(latest_order.status, latest_order.status.title())
                    
                    order_date = latest_order.created_at.strftime("%b %d, %Y")
                    
                    return JsonResponse({
                        "response": f"I found your latest order! \n\n**Order #{latest_order.id}**\nStatus: **{display_status}**\nPlaced on: **{order_date}**\n\nIs there anything else I can help you with?"
                    })
                except Exception:
                    # Fallback to general FAQ if no orders exist
                    pass

            # 3. Check for common greetings (High Priority)
            greetings = {'hi', 'hello', 'hey', 'greetings', 'namaste', 'morning', 'evening'}
            if any(greet in user_words for greet in greetings):
                return JsonResponse({"response": "Hello! I'm Elegance Bot. How can I help you today?"})

            # 4. Improved matching logic: Keyword overlap scoring
            faqs = FAQ.objects.all()
            
            matches = [] # To store all matches for "Did you mean?"
            stop_words = {'a', 'an', 'the', 'is', 'are', 'do', 'does', 'how', 'can', 'i', 'to', 'for', 'of', 'in', 'on', 'at', 'with', 'about', 'some', 'any', 'my', 'your'}
            
            for faq in faqs:
                faq_question_clean = re.sub(r'[^\w\s]', '', faq.question.lower())
                faq_words = set(faq_question_clean.split())
                stemmed_faq_words = {stem_word(w) for w in faq_words if w not in stop_words}
                
                score = 0
                # Check for stemmed meaningful word overlap
                meaningful_user_words = {w for w in expanded_user_intent if w not in stop_words}
                common_meaningful_stemmed = meaningful_user_words.intersection(stemmed_faq_words)
                
                score += len(common_meaningful_stemmed) * 4
                
                # Bonus for exact whole word match in clean user msg
                for f_word in faq_words:
                    if f_word in user_words and f_word not in stop_words:
                        score += 2
                
                # Bonus for phrase match
                if faq_question_clean in user_msg_clean or user_msg_clean in faq_question_clean:
                    score += 5

                if score > 0:
                    matches.append({
                        'answer': faq.answer,
                        'question': faq.question,
                        'score': score
                    })

            # Sort matches by highest score
            matches = sorted(matches, key=lambda x: x['score'], reverse=True)

            # High confidence threshold
            if matches and matches[0]['score'] >= 8:
                return JsonResponse({"response": matches[0]['answer']})
            
            # Low confidence threshold - "Did you mean?"
            if matches and matches[0]['score'] >= 3:
                return JsonResponse({
                    "response": f"I'm not 100% sure, but are you asking about: **{matches[0]['question']}**?",
                    "suggestion": matches[0]['question']
                })

            return JsonResponse({
                "response": "I'm sorry, I still can't quite understand that. Perhaps you could try asking about 'returns', 'shipping', or 'size guide'?",
                "is_fallback": True
            })

        except Exception as e:
            return JsonResponse({"response": f"Oops! I hit a snag: {str(e)}"})

    return JsonResponse({"response": "Invalid request method."}, status=405)
