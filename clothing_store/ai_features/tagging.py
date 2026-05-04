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
        
        # Tighter Center Crop (Take the middle 20% of the image to avoid hands/background)
        width, height = pil_img.size
        left = width * 0.40
        top = height * 0.40
        right = width * 0.60
        bottom = height * 0.60
        pil_img = pil_img.crop((left, top, right, bottom))
        
        pil_img = pil_img.resize((50, 50))
        img_array = np.array(pil_img).reshape(-1, 3)

        kmeans = KMeans(n_clusters=num_colors)
        labels = kmeans.fit_predict(img_array)
        
        # Sort clusters by size to prioritize the true garment color
        counts = np.bincount(labels)
        sorted_indices = np.argsort(counts)[::-1]
        
        # Use only the most dominant color to avoid background/skin tones
        colors = [kmeans.cluster_centers_[sorted_indices[0]].astype(int)]
        
        # Better color mapping using Euclidean distance
        BASIC_COLORS = {
            "White": (255, 255, 255),
            "Black": (20, 20, 20),
            "Red": (255, 0, 0),
            "Green": (0, 200, 0),
            "Blue": (0, 0, 255),
            "Yellow": (255, 255, 0),
            "Cyan": (0, 255, 255),
            "Magenta": (255, 0, 255),
            "Grey": (128, 128, 128),
            "Dark Grey": (64, 64, 64),
            "Navy": (0, 0, 128),
            "Maroon": (128, 0, 0),
            "Olive": (128, 128, 0),
            "Teal": (0, 128, 128),
            "Purple": (128, 0, 128),
            "Brown": (139, 69, 19),
            "Dark Brown": (70, 40, 30),
            "Orange": (255, 140, 0),
            "Pink": (255, 192, 203),
            "Beige": (245, 245, 220)
        }
        
        color_names = set()
        for rgb in colors:
            closest_color = min(BASIC_COLORS.keys(), key=lambda k: sum((c1 - c2) ** 2 for c1, c2 in zip(rgb, BASIC_COLORS[k])))
            color_names.add(closest_color)
            
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
        'jersey': 'T-Shirt',
        'sweatshirt': 'Sweatshirt',
        'trench_coat': 'Jacket',
        'cardigan': 'Sweater',
        'suit': 'Suit',
        'wool': 'WinterWear',
        'jean': 'Jeans',
        'running_shoe': 'Shoes',
        'Loafer': 'Shoes',
        'bow_tie': 'Accessory',
        'sombrero': 'Hat',
        'fur_coat': 'Coat',
        'cloak': 'Coat',
        'poncho': 'Outerwear',
        'vestment': 'Outerwear',
        'Windsor_tie': 'Tie',
        'bolo_tie': 'Tie',
        'stole': 'Accessory',
        'sunglasses': 'Accessories',
        'sunglass': 'Accessories',
        'miniskirt': 'Skirt',
        'overskirt': 'Skirt',
        'pajama': 'Sleepwear',
        'swimming_trunks': 'Swimwear',
        'sandal': 'Footwear',
        'cowboy_boot': 'Boots',
        'half_track': 'Boots',
        'kimono': 'Traditional',
        'apron': 'Apron',
        'diaper': 'Bottoms',
        'bulletproof_vest': 'Vest',
        'backpack': 'Bag',
        'purse': 'Bag',
        'wallet': 'Accessory'
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
        decoded = decode_predictions(preds, top=15)[0] # Check top 15
        
        # Extract labels and confidences
        raw_labels = [(d[1], d[2]) for d in decoded]
        
        # Heuristic: ImageNet struggles with basic button-up shirts, predicting them as suits/coats
        upper_body_classes = ['jersey', 'sweatshirt', 'cardigan', 'suit', 'trench_coat', 'cloak', 'fur_coat', 'lab_coat', 'pajama']
        
        for label, conf in raw_labels:
            if len(clean_labels) >= 2:
                break # Limit to top 2 clothing categories
                
            # If the model thinks it's an upper body garment but isn't highly confident, it's usually a Shirt
            if len(clean_labels) == 0 and label in upper_body_classes and conf < 0.4:
                clean_labels.add('Shirt')
                
            # Check if the ImageNet label is in our map
            if label in CLOTHING_MAP:
                clean_labels.add(CLOTHING_MAP[label])
            # If it's a generic clothing term, add it directly capitalized
            elif any(term in label for term in ['shirt', 'jacket', 'pant', 'coat', 'shoe', 'boot', 'dress', 'skirt', 'sweater', 'hoodie', 'jean']):
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
