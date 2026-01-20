"""
Garment Processing for Virtual Try-On
Handles garment image preparation, sizing, and manipulation
"""

import cv2
import numpy as np
from PIL import Image


def prepare_garment(garment_path, remove_bg=True):
    """
    Prepare garment image for overlay
    
    Args:
        garment_path: Path to garment image
        remove_bg: Whether to attempt background removal
    
    Returns:
        Garment image with alpha channel (RGBA)
    """
    # Read image
    garment = cv2.imread(garment_path, cv2.IMREAD_UNCHANGED)
    
    if garment is None:
        raise ValueError(f"Could not load garment image: {garment_path}")
    
    # Convert to RGBA if needed
    if len(garment.shape) == 2:  # Grayscale
        garment = cv2.cvtColor(garment, cv2.COLOR_GRAY2RGBA)
    elif garment.shape[2] == 3:  # BGR
        garment = cv2.cvtColor(garment, cv2.COLOR_BGR2RGBA)
    elif garment.shape[2] == 4:  # Already BGRA
        garment = cv2.cvtColor(garment, cv2.COLOR_BGRA2RGBA)
    
    # Simple background removal if requested
    if remove_bg and not _has_transparency(garment):
        garment = _simple_background_removal(garment)
    
    return garment


def _has_transparency(image):
    """Check if image has transparency"""
    if image.shape[2] < 4:
        return False
    return np.any(image[:, :, 3] < 255)


def _simple_background_removal(image):
    """
    Simple background removal using color-based segmentation
    Assumes white or light background
    """
    # Convert to HSV for better color segmentation
    rgb = image[:, :, :3]
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    
    # Create mask for non-white areas
    # Adjust these thresholds based on your garment images
    lower_white = np.array([0, 0, 200])
    upper_white = np.array([180, 30, 255])
    
    white_mask = cv2.inRange(hsv, lower_white, upper_white)
    
    # Invert mask (we want to keep non-white areas)
    garment_mask = cv2.bitwise_not(white_mask)
    
    # Apply morphological operations to clean up mask
    kernel = np.ones((3, 3), np.uint8)
    garment_mask = cv2.morphologyEx(garment_mask, cv2.MORPH_CLOSE, kernel)
    garment_mask = cv2.morphologyEx(garment_mask, cv2.MORPH_OPEN, kernel)
    
    # Create RGBA image with alpha channel
    rgba = np.dstack([rgb, garment_mask])
    
    return rgba


def resize_garment(garment, target_width, target_height):
    """
    Resize garment to target dimensions while maintaining aspect ratio
    
    Args:
        garment: RGBA garment image
        target_width: Target width in pixels
        target_height: Target height in pixels
    
    Returns:
        Resized garment image
    """
    h, w = garment.shape[:2]
    
    # Calculate scaling to fit target size
    scale_w = target_width / w
    scale_h = target_height / h
    scale = min(scale_w, scale_h)
    
    new_w = int(w * scale)
    new_h = int(h * scale)
    
    # Resize
    resized = cv2.resize(garment, (new_w, new_h), interpolation=cv2.INTER_AREA)
    
    # Create canvas of target size
    canvas = np.zeros((target_height, target_width, 4), dtype=np.uint8)
    
    # Center the garment on canvas
    y_offset = (target_height - new_h) // 2
    x_offset = (target_width - new_w) // 2
    
    canvas[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized
    
    return canvas


def create_garment_mask(garment):
    """
    Create binary mask from garment alpha channel
    
    Args:
        garment: RGBA garment image
    
    Returns:
        Binary mask (0 or 255)
    """
    if garment.shape[2] < 4:
        # No alpha channel, create mask from brightness
        gray = cv2.cvtColor(garment[:, :, :3], cv2.COLOR_RGB2GRAY)
        _, mask = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY)
    else:
        # Use alpha channel
        mask = garment[:, :, 3]
    
    return mask


def add_shadow_effect(garment, shadow_intensity=0.3):
    """
    Add subtle shadow effect to garment for realism
    
    Args:
        garment: RGBA garment image
        shadow_intensity: Shadow darkness (0-1)
    
    Returns:
        Garment with shadow effect
    """
    result = garment.copy()
    
    # Create shadow on bottom and right edges
    h, w = garment.shape[:2]
    
    # Vertical gradient for shadow
    gradient_v = np.linspace(1.0, 1.0 - shadow_intensity, h)
    gradient_v = np.tile(gradient_v[:, np.newaxis], (1, w))
    
    # Horizontal gradient for shadow
    gradient_h = np.linspace(1.0, 1.0 - shadow_intensity, w)
    gradient_h = np.tile(gradient_h[np.newaxis, :], (h, 1))
    
    # Combine gradients
    shadow = np.minimum(gradient_v, gradient_h)
    
    # Apply shadow to RGB channels
    for i in range(3):
        result[:, :, i] = (result[:, :, i] * shadow).astype(np.uint8)
    
    return result


def adjust_garment_brightness(garment, person_image, person_region):
    """
    Adjust garment brightness to match person's lighting
    
    Args:
        garment: RGBA garment image
        person_image: Original person image
        person_region: Region of person to sample lighting from
    
    Returns:
        Brightness-adjusted garment
    """
    # Calculate average brightness of person's torso
    person_gray = cv2.cvtColor(person_image, cv2.COLOR_BGR2GRAY)
    person_brightness = np.mean(person_gray[person_region])
    
    # Calculate garment brightness
    garment_gray = cv2.cvtColor(garment[:, :, :3], cv2.COLOR_RGB2GRAY)
    garment_brightness = np.mean(garment_gray[garment_gray > 0])
    
    # Calculate adjustment factor
    if garment_brightness > 0:
        factor = person_brightness / garment_brightness
        factor = np.clip(factor, 0.5, 1.5)  # Limit adjustment range
        
        # Apply adjustment
        result = garment.copy()
        for i in range(3):
            result[:, :, i] = np.clip(result[:, :, i] * factor, 0, 255).astype(np.uint8)
        
        return result
    
    return garment
