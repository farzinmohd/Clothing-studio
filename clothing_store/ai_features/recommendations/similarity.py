import os
import numpy as np
import pickle
from PIL import Image
from django.conf import settings
from django.core.files.storage import default_storage

# Lazy imports to avoid import errors if TF is not ready/heavy startup
tensorflow = None
preprocess_input = None
EfficientNetB0 = None
image = None

def load_tf_dependencies():
    global tensorflow, preprocess_input, EfficientNetB0, image
    if tensorflow is None:
        import tensorflow as tf
        from tensorflow.keras.applications.efficientnet import EfficientNetB0 as KerasEfficientNetB0, preprocess_input as keras_preprocess_input
        from tensorflow.keras.preprocessing import image as keras_image
        tensorflow = tf
        preprocess_input = keras_preprocess_input
        EfficientNetB0 = KerasEfficientNetB0
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
            # EfficientNetB0: Better accuracy with fewer parameters, ideal for fashion/product images
            # Include_top=False removes the final classification layer
            self.model = EfficientNetB0(weights='imagenet', include_top=False, pooling='avg')
            self.initialized = True


    def extract(self, img_path):
        self.initialize()
        
        # --- 🖼️ PREPROCESSING: Center crop to focus on product ---
        pil_img_original = Image.open(img_path).convert('RGB')
        pil_img = self._center_crop_product(pil_img_original)
        
        # Resize for EfficientNetB0
        img = pil_img.resize((224, 224))
        x = image.img_to_array(img)
        x = np.expand_dims(x, axis=0)
        x = preprocess_input(x)
        
        # Extract features using EfficientNetB0
        features = self.model.predict(x, verbose=0)
        # Flatten and normalize
        features = features.flatten()
        features = features / np.linalg.norm(features) # L2 Normalization
        
        # --- 🎨 ENHANCED COLOR FEATURES (MULTI-SPACE) ---
        
        # 1. RGB Color Histogram (overall color distribution)
        pil_img_small = pil_img.resize((64, 64))
        rgb_hist = np.array(pil_img_small.histogram())
        rgb_hist = rgb_hist / (pil_img_small.size[0] * pil_img_small.size[1])
        rgb_hist = rgb_hist / (np.linalg.norm(rgb_hist) + 1e-7)
        
        # 2. HSV Color Features (better for human color perception)
        hsv_features = self._extract_hsv_features(pil_img)
        
        # 3. Dominant Colors (K-Means on RGB)
        dominant_colors_rgb = self._extract_dominant_colors(pil_img, n_colors=5)
        
        # 4. Dominant Colors in HSV space (captures hue/saturation better)
        # Increase to 7 colors to capture more color variations
        dominant_colors_hsv = self._extract_dominant_colors_hsv(pil_img, n_colors=7)
        
        
        # --- 🔧 EXTREME COLOR PRIORITY MODE ---
        # COLOR IS 95%+ OF MATCHING - Style is almost ignored
        # This ensures green shirt ONLY matches green products
        combined_features = np.concatenate([
            features * 0.05,             # Style/shape (ALMOST ZERO - barely used)
            rgb_hist * 6.0,              # RGB distribution (VERY HIGH)
            hsv_features * 12.0,         # HSV features (EXTREME - absolute priority!)
            dominant_colors_rgb * 5.0,   # RGB dominant colors (VERY HIGH)
            dominant_colors_hsv * 10.0   # HSV dominant colors (EXTREME!)
        ])
        combined_features = combined_features / np.linalg.norm(combined_features)
        
        return combined_features

    
    def _center_crop_product(self, pil_img, crop_ratio=0.9):
        """
        Center crop to focus on the product and reduce background noise.
        Using 90% crop to preserve more product details.
        """
        width, height = pil_img.size
        new_width = int(width * crop_ratio)
        new_height = int(height * crop_ratio)
        
        left = (width - new_width) // 2
        top = (height - new_height) // 2
        right = left + new_width
        bottom = top + new_height
        
        return pil_img.crop((left, top, right, bottom))
    
    def _extract_hsv_features(self, pil_img):
        """
        Extract HSV color histogram features.
        HSV is better for color matching than RGB because:
        - Hue represents actual color (red, green, blue)
        - Saturation represents color intensity
        - Value represents brightness
        """
        import cv2
        
        # Convert PIL to numpy array
        img_array = np.array(pil_img.resize((64, 64)))
        
        # Convert RGB to HSV
        hsv_img = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)
        
        # Calculate histogram for each channel
        h_hist = cv2.calcHist([hsv_img], [0], None, [32], [0, 180])  # Hue: 0-180
        s_hist = cv2.calcHist([hsv_img], [1], None, [32], [0, 256])  # Saturation: 0-255
        v_hist = cv2.calcHist([hsv_img], [2], None, [32], [0, 256])  # Value: 0-255
        
        # Normalize
        h_hist = h_hist.flatten() / (h_hist.sum() + 1e-7)
        s_hist = s_hist.flatten() / (s_hist.sum() + 1e-7)
        v_hist = v_hist.flatten() / (v_hist.sum() + 1e-7)
        
        # Combine (96 features total)
        hsv_features = np.concatenate([h_hist, s_hist, v_hist])
        return hsv_features / (np.linalg.norm(hsv_features) + 1e-7)
    
    def _extract_dominant_colors(self, pil_img, n_colors=5):
        """
        Extract dominant colors using K-Means clustering in RGB space.
        """
        from sklearn.cluster import KMeans
        
        # Resize for faster processing
        img_small = pil_img.resize((100, 100))
        pixels = np.array(img_small).reshape(-1, 3)
        
        # Apply K-Means to find dominant colors
        kmeans = KMeans(n_clusters=n_colors, random_state=42, n_init=10)
        kmeans.fit(pixels)
        
        # Get cluster centers (dominant colors) and normalize to 0-1 range
        dominant_colors = kmeans.cluster_centers_ / 255.0
        
        # Flatten to 1D array (5 colors * 3 channels = 15 features)
        return dominant_colors.flatten()
    
    def _extract_dominant_colors_hsv(self, pil_img, n_colors=7):
        """
        Extract dominant colors in HSV space for better perceptual matching.
        Using 7 colors to capture more color variations.
        """
        import cv2
        from sklearn.cluster import KMeans
        
        # Convert to HSV
        img_array = np.array(pil_img.resize((100, 100)))
        hsv_img = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)
        pixels = hsv_img.reshape(-1, 3)
        
        # K-Means in HSV space
        kmeans = KMeans(n_clusters=n_colors, random_state=42, n_init=10)
        kmeans.fit(pixels)
        
        # Normalize: H(0-180), S(0-255), V(0-255)
        dominant_hsv = kmeans.cluster_centers_
        dominant_hsv[:, 0] = dominant_hsv[:, 0] / 180.0  # Hue
        dominant_hsv[:, 1] = dominant_hsv[:, 1] / 255.0  # Saturation
        dominant_hsv[:, 2] = dominant_hsv[:, 2] / 255.0  # Value
        
        # Flatten (7 colors * 3 channels = 21 features)
        return dominant_hsv.flatten()


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

def find_similar_products(query_image_path, top_k=6, return_scores=False):
    """
    Finds existing products in the catalog similar to the query image.
    
    Args:
        query_image_path: Path to the query image
        top_k: Number of results to return
        return_scores: If True, returns (product_id, confidence_score) tuples
        
    Returns: 
        If return_scores=False: List of product IDs
        If return_scores=True: List of (product_id, confidence_percentage) tuples
    """
    extractor = FeatureExtractor()
    query_features = extractor.extract(query_image_path)
    
    catalog_features = load_catalog_features()
    if not catalog_features:
        return [] if not return_scores else []

    scores = []
    for product_id, features in catalog_features.items():
        # Cosine similarity (ranges from -1 to 1, but normalized features give 0 to 1)
        similarity = np.dot(query_features, features)
        
        # Convert to confidence percentage (0-100%)
        # Cosine similarity with normalized vectors ranges ~0.5-1.0 for similar items
        # We scale this to a more intuitive 0-100% range
        confidence = int(min(max(similarity * 100, 0), 100))
        
        scores.append((product_id, similarity, confidence))
    
    # Sort by similarity (highest first)
    scores.sort(key=lambda x: x[1], reverse=True)
    
    # Return top K results
    if return_scores:
        return [(pid, conf) for pid, sim, conf in scores[:top_k]]
    else:
        return [pid for pid, sim, conf in scores[:top_k]]
