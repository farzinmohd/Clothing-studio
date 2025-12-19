from django.shortcuts import render, redirect
from django.core.files.storage import default_storage
import random

# -------------------------
# AI HOME (UPLOAD PAGE)
# -------------------------
def ai_home(request):
    if request.method == "POST":
        image = request.FILES.get('image')

        if image:
            # Save image temporarily
            image_path = default_storage.save(
                f"ai_uploads/{image.name}", image
            )

            # 🎯 TEMP SKIN TONE LOGIC (AI will come later)
            skin_tones = ['Fair', 'Medium', 'Dark']
            detected_tone = random.choice(skin_tones)

            # Store results in session
            request.session['uploaded_image'] = image_path
            request.session['skin_tone'] = detected_tone

            return redirect('ai_result')

    return render(request, 'ai/upload.html')


# -------------------------
# AI RESULT PAGE
# -------------------------
def ai_result(request):
    image_path = request.session.get('uploaded_image')
    skin_tone = request.session.get('skin_tone')

    color_map = {
        'Fair': ['Blue', 'Black', 'Pink'],
        'Medium': ['White', 'Green', 'Beige'],
        'Dark': ['Red', 'Yellow', 'Brown'],
    }

    recommended_colors = color_map.get(skin_tone, [])

    return render(request, 'ai/result.html', {
        'image': image_path,
        'skin_tone': skin_tone,
        'colors': recommended_colors
    })
