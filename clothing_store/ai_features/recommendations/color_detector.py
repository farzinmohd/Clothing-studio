"""
Color Detection Utility for Visual Search
Detects dominant color from uploaded image and maps to product color categories.
"""

import cv2
import numpy as np
from sklearn.cluster import KMeans
from PIL import Image


def detect_dominant_color(image_path):
    """
    Detect the dominant color from an image and return the color name.
    Focuses on the CENTER region to avoid background interference.
    
    Returns:
        str: Color name ('Green', 'Blue', 'Red', 'Yellow', 'Brown', 'Beige', 'White', 'Black', 'Pink')
    """
    # Load image
    img = Image.open(image_path).convert('RGB')
    
    # CENTER CROP to focus on product (avoid background)
    width, height = img.size
    crop_size = 0.6  # Use center 60% of image
    left = int(width * (1 - crop_size) / 2)
    top = int(height * (1 - crop_size) / 2)
    right = int(width * (1 + crop_size) / 2)
    bottom = int(height * (1 + crop_size) / 2)
    
    img = img.crop((left, top, right, bottom))
    img = img.resize((150, 150))  # Resize for faster processing
    
    # Convert to numpy array
    img_array = np.array(img)
    pixels = img_array.reshape(-1, 3)
    
    # Remove very dark (black) and very bright (white/background) pixels
    # This helps focus on the actual product color
    brightness = pixels.mean(axis=1)
    mask = (brightness > 30) & (brightness < 240)  # Filter out extremes
    filtered_pixels = pixels[mask]
    
    if len(filtered_pixels) < 100:  # Fallback if too few pixels
        filtered_pixels = pixels
    
    # Use K-Means to find dominant colors
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)  # Reduced to 3 for speed
    kmeans.fit(filtered_pixels)
    
    # Get the most dominant color (largest cluster)
    labels = kmeans.labels_
    counts = np.bincount(labels)
    dominant_cluster = np.argmax(counts)
    dominant_color_rgb = kmeans.cluster_centers_[dominant_cluster]
    
    # Convert to HSV for better color classification
    rgb_normalized = dominant_color_rgb.reshape(1, 1, 3).astype(np.uint8)
    hsv = cv2.cvtColor(rgb_normalized, cv2.COLOR_RGB2HSV)[0][0]
    
    h, s, v = hsv[0], hsv[1], hsv[2]
    
    print(f"🎨 Color detection - H:{h}, S:{s}, V:{v}, RGB:{dominant_color_rgb}")
    
    # Classify color based on HSV values
    color_name = classify_color_hsv(h, s, v)
    
    return color_name, dominant_color_rgb


def classify_color_hsv(h, s, v):
    """
    Classify color based on HSV values with improved thresholds.
    
    HSV Ranges:
    - Hue (H): 0-180 in OpenCV
    - Saturation (S): 0-255
    - Value (V): 0-255
    """
    
    # FIRST: Check for grayscale/neutral colors (low saturation)
    if s < 40:  # Increased threshold for better color detection
        if v < 60:
            return 'Black'
        elif v > 180:
            return 'White'
        else:
            return 'Beige'  # Gray/neutral
    
    # SECOND: Vivid colors (high saturation)
    # Hue ranges (OpenCV uses 0-180 for Hue)
    
    # Red (wraps around 0/180)
    if h < 10 or h > 165:
        return 'Red'
    
    # Orange/Brown
    elif 10 <= h < 22:
        if v < 100 or s > 100:
            return 'Brown'
        else:
            return 'Beige'
    
    # Yellow
    elif 22 <= h < 38:
        return 'Yellow'
    
    # GREEN - EXPANDED RANGE for olive, forest, mint, etc.
    elif 38 <= h < 85:  # Wide range: 38-85
        return 'Green'
    
    # Cyan/Teal (often confused with green)
    elif 85 <= h < 100:
        # If saturation is high, it's likely teal/cyan (treat as Blue)
        # If saturation is medium, might be olive (treat as Green)
        if s > 100:
            return 'Blue'
        else:
            return 'Green'  # Olive/dark green
    
    # Blue
    elif 100 <= h < 130:
        return 'Blue'
    
    # Purple/Violet
    elif 130 <= h < 150:
        return 'Pink'  # Map to Pink for fashion
    
    # Pink/Magenta
    elif 150 <= h < 165:
        return 'Pink'
    
    else:
        # Fallback
        return 'Beige'


def get_color_similarity_map():
    """
    Return a mapping of similar colors for fallback matching.
    If exact color not found, try similar colors.
    """
    return {
        'Green': ['Green'],  # Only exact green
        'Blue': ['Blue'],
        'Red': ['Red', 'Pink'],
        'Yellow': ['Yellow', 'Beige'],
        'Brown': ['Brown', 'Beige'],
        'Beige': ['Beige', 'Brown', 'White'],
        'White': ['White', 'Beige'],
        'Black': ['Black'],
        'Pink': ['Pink', 'Red']
    }
