import os
import tensorflow as tf
import numpy as np
from tensorflow.keras.applications.mobilenet_v2 import MobileNetV2, preprocess_input, decode_predictions
from tensorflow.keras.preprocessing import image
from PIL import Image
from sklearn.cluster import KMeans

# Lazy load model
model = None
is_custom_model = False
CUSTOM_CATEGORIES = ['Shirt', 'T-Shirt', 'Jacket', 'Pants', 'Suit', 'Shoes']

def load_model():
    global model, is_custom_model
    if model is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(base_dir, 'menswear_tagger.h5')
        
        if os.path.exists(model_path):
            from tensorflow.keras.models import load_model as keras_load_model
            model = keras_load_model(model_path)
            is_custom_model = True
            print("Loaded custom menswear tagging model!")
        else:
            # Pre-trained on ImageNet (1000 classes fallback)
            model = MobileNetV2(weights='imagenet')
            is_custom_model = False
            print("Loaded fallback ImageNet tagging model.")

def get_dominant_colors(img_path, num_colors=2):
    """
    KMeans clustering to find dominant colors, ignoring background white.
    """
    try:
        pil_img = Image.open(img_path).convert('RGB')
        
        # Tighter Center Crop (Take the middle 40% of the image)
        width, height = pil_img.size
        left = width * 0.30
        top = height * 0.30
        right = width * 0.70
        bottom = height * 0.70
        pil_img = pil_img.crop((left, top, right, bottom))
        
        pil_img = pil_img.resize((50, 50))
        img_array = np.array(pil_img).reshape(-1, 3)

        kmeans = KMeans(n_clusters=num_colors)
        kmeans.fit(img_array)
        
        colors = kmeans.cluster_centers_.astype(int)
        
        # Simple RGB to Name mapping (Heuristic)
        color_names = set()
        for rgb in colors:
            r, g, b = rgb
            
            # Adjusted thresholds to capture more realistic photo colors
            if r > 200 and g > 200 and b > 200: color_names.add("White")
            elif r < 60 and g < 60 and b < 60: color_names.add("Black")
            elif r > 150 and g < 100 and b < 100: color_names.add("Red")
            elif r < 100 and g > 150 and b < 100: color_names.add("Green")
            elif r < 100 and g < 100 and b > 150: color_names.add("Blue")
            elif r > 180 and g > 180 and b < 100: color_names.add("Yellow")
            elif 80 < r < 180 and 80 < g < 180 and 80 < b < 180: color_names.add("Grey")
            
        return list(color_names)
    except Exception:
        return []

def predict_image_tags(img_path):
    """
    Returns a comma-separated string of cleaned tags.
    """
    load_model()
    
    # Menswear Specific Mapping dictionary
    CLOTHING_MAP = {
        'jersey': 'Shirt',
        'sweatshirt': 'Sweatshirt',
        'trench_coat': 'Jacket',
        'cardigan': 'Sweater',
        'suit': 'Suit',
        'wool': 'WinterWear',
        'jean': 'Jeans',
        'running_shoe': 'Shoes',
        'Loafer': 'Shoes',
        'bow_tie': 'Accessory',
        'sombrero': 'Hat'
    }
    
    # 1. Object Detection (MobileNet)
    img = image.load_img(img_path, target_size=(224, 224))
    x = image.img_to_array(img)
    x = np.expand_dims(x, axis=0)
    x = preprocess_input(x)

    preds = model.predict(x)
    clean_labels = set()
    
    if is_custom_model:
        # The custom model directly outputs probabilities for our specific menswear categories
        class_idx = np.argmax(preds[0])
        clothes_tag = CUSTOM_CATEGORIES[class_idx]
        clean_labels.add(clothes_tag)
    else:
        # --- FALLBACK LOGIC (Generic ImageNet model) ---
        decoded = decode_predictions(preds, top=5)[0] # Check top 5
        
        # Extract labels and map them
        raw_labels = [d[1] for d in decoded]
        
        for label in raw_labels:
            # Check if the ImageNet label is in our map
            if label in CLOTHING_MAP:
                clean_labels.add(CLOTHING_MAP[label])
            # If it's a generic clothing term, add it directly capitalized
            elif 'shirt' in label or 'jacket' in label or 'pant' in label or 'coat' in label:
                clean_labels.add(label.replace('_', ' ').title())
                
        # If it couldn't find ANY mapped clothing, default to "Apparel"
        if not clean_labels:
            clean_labels.add("Apparel")
    
    # 2. Color Detection
    colors = get_dominant_colors(img_path)
    
    # Combine
    all_tags = list(clean_labels) + colors
    
    # Clean string
    return ", ".join(all_tags)
