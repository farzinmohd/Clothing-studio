import os
import numpy as np
import pickle
from PIL import Image
from django.conf import settings
from django.core.files.storage import default_storage

# Lazy imports to avoid import errors if TF is not ready/heavy startup
tensorflow = None
preprocess_input = None
ResNet50 = None
image = None

def load_tf_dependencies():
    global tensorflow, preprocess_input, ResNet50, image
    if tensorflow is None:
        import tensorflow as tf
        from tensorflow.keras.applications.resnet50 import ResNet50 as KerasResNet50, preprocess_input as keras_preprocess_input
        from tensorflow.keras.preprocessing import image as keras_image
        tensorflow = tf
        preprocess_input = keras_preprocess_input
        ResNet50 = KerasResNet50
        image = keras_image

class FeatureExtractor:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FeatureExtractor, cls).__new__(cls)
            cls._instance.model = None
            cls._instance.initialized = False
        return cls._instance

    def initialize(self):
        if not self.initialized:
            load_tf_dependencies()
            # Include_top=False removes the final classification layer
            self.model = ResNet50(weights='imagenet', include_top=False, pooling='avg')
            self.initialized = True

    def extract(self, img_path):
        self.initialize()
        # Resize image to 224x224 for ResNet50
        img = image.load_img(img_path, target_size=(224, 224))
        x = image.img_to_array(img)
        x = np.expand_dims(x, axis=0)
        x = preprocess_input(x)
        
        # Extract features
        features = self.model.predict(x)
        # Flatten and normalize
        features = features.flatten()
        features = features / np.linalg.norm(features) # L2 Normalization
        
        # --- 🎨 ADD COLOR FEATURES (Histogram) ---
        # ResNet is great for shape/pattern, but can ignore color (e.g., white vs light blue).
        # We manually extract color histogram to force color matching.
        
        # Reload image as PIL for independent color processing
        pil_img = Image.open(img_path).convert('RGB')
        pil_img = pil_img.resize((64, 64)) # Speed up
        
        # Calculate histogram (RGB, 8 bins per channel = 512 features)
        hist = pil_img.histogram()
        # Normalize
        hist = np.array(hist) / (pil_img.size[0] * pil_img.size[1])
        
        # Normalize vector length
        hist = hist / np.linalg.norm(hist)

        # Concatenate: [ResNet(2048) ... Color(768)]
        # We weight color strongly (x1.5) to fix the user's issue
        combined_features = np.concatenate([features, hist * 1.5])
        combined_features = combined_features / np.linalg.norm(combined_features)
        
        return combined_features

FEATURES_PATH = os.path.join(settings.MEDIA_ROOT, 'ai_features', 'product_embeddings.pkl')

def load_catalog_features():
    if os.path.exists(FEATURES_PATH):
        with open(FEATURES_PATH, 'rb') as f:
            return pickle.load(f)
    return {}

def save_catalog_features(features_dict):
    os.makedirs(os.path.dirname(FEATURES_PATH), exist_ok=True)
    with open(FEATURES_PATH, 'wb') as f:
        pickle.dump(features_dict, f)

def find_similar_products(query_image_path, top_k=6):
    """
    Finds existing products in the catalog similar to the query image.
    Returns: List of product IDs
    """
    extractor = FeatureExtractor()
    query_features = extractor.extract(query_image_path)
    
    catalog_features = load_catalog_features()
    if not catalog_features:
        return []

    scores = []
    for product_id, features in catalog_features.items():
        # Cosine similarity
        similarity = np.dot(query_features, features)
        scores.append((product_id, similarity))
    
    # Sort by similarity (highest first)
    scores.sort(key=lambda x: x[1], reverse=True)
    
    # Return top K product IDs
    return [pid for pid, score in scores[:top_k]]
