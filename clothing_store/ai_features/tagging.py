import os
import tensorflow as tf
import numpy as np
from tensorflow.keras.applications.mobilenet_v2 import MobileNetV2, preprocess_input, decode_predictions
from tensorflow.keras.preprocessing import image
from PIL import Image
from sklearn.cluster import KMeans

# Lazy load model
model = None

def load_model():
    global model
    if model is None:
        # Pre-trained on ImageNet (1000 classes)
        model = MobileNetV2(weights='imagenet')

def get_dominant_colors(img_path, num_colors=2):
    """
    KMeans clustering to find dominant colors.
    Returns list of color names (e.g., ['Red', 'Black'])
    """
    try:
        pil_img = Image.open(img_path).convert('RGB')
        pil_img = pil_img.resize((50, 50))
        img_array = np.array(pil_img).reshape(-1, 3)

        kmeans = KMeans(n_clusters=num_colors)
        kmeans.fit(img_array)
        
        colors = kmeans.cluster_centers_.astype(int)
        
        # Simple RGB to Name mapping (Heuristic)
        color_names = set()
        for rgb in colors:
            r, g, b = rgb
            if r > 200 and g > 200 and b > 200: color_names.add("White")
            elif r < 50 and g < 50 and b < 50: color_names.add("Black")
            elif r > 150 and g < 100 and b < 100: color_names.add("Red")
            elif r < 100 and g > 150 and b < 100: color_names.add("Green")
            elif r < 100 and g < 100 and b > 150: color_names.add("Blue")
            elif r > 200 and g > 200 and b < 100: color_names.add("Yellow")
            elif r > 100 and g > 100 and b > 100: color_names.add("Grey")
            
        return list(color_names)
    except Exception:
        return []

def predict_image_tags(img_path):
    """
    Returns a comma-separated string of tags.
    Example: "jersey, sweatshirt, Red, Black"
    """
    load_model()
    
    # 1. Object Detection (MobileNet)
    img = image.load_img(img_path, target_size=(224, 224))
    x = image.img_to_array(img)
    x = np.expand_dims(x, axis=0)
    x = preprocess_input(x)

    preds = model.predict(x)
    decoded = decode_predictions(preds, top=3)[0] # Top 3
    
    # Extract labels (e.g., 'jersey', 'cardigan')
    labels = [d[1] for d in decoded]
    
    # 2. Color Detection
    colors = get_dominant_colors(img_path)
    
    # Combine
    all_tags = labels + colors
    
    # Clean string
    return ", ".join(all_tags)
