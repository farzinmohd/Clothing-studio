"""
Simple Overlay Virtual Try-On
Main algorithm for overlaying garments on person images
"""

import cv2
import numpy as np
import os
from .pose_detect import detect_full_body_pose, get_body_measurements, draw_pose_skeleton
from .garment_processor import prepare_garment, resize_garment, create_garment_mask, add_shadow_effect


def virtual_tryon_simple(person_image_path, garment_image_path, output_path=None, debug=False):
    """
    Perform simple overlay virtual try-on
    
    Args:
        person_image_path: Path to person's photo
        garment_image_path: Path to garment image
        output_path: Optional path to save result
        debug: If True, show intermediate steps
    
    Returns:
        tuple: (result_image, success_message) or (None, error_message)
    """
    try:
        # Step 1: Load person image
        person_img = cv2.imread(person_image_path)
        if person_img is None:
            return None, "Could not load person image"
        
        # Step 2: Detect pose
        keypoints = detect_full_body_pose(person_image_path)
        if keypoints is None:
            return None, "Could not detect pose. Please use a clear, frontal photo."
        
        # Step 3: Get body measurements
        measurements = get_body_measurements(keypoints)
        
        # Step 4: Prepare garment
        garment = prepare_garment(garment_image_path, remove_bg=True)
        
        # Step 5: Resize garment to fit body
        target_width = int(measurements['chest_width'])
        target_height = int(measurements['torso_height'] * 1.2)  # Slightly longer
        
        garment_resized = resize_garment(garment, target_width, target_height)
        
        # Step 6: Warp garment to body shape
        warped_garment = warp_garment_to_body(garment_resized, keypoints, measurements)
        
        # Step 7: Add shadow effect
        warped_garment = add_shadow_effect(warped_garment, shadow_intensity=0.2)
        
        # Step 8: Blend garment with person image
        result = blend_garment_with_person(person_img, warped_garment, keypoints)
        
        # Debug visualization
        if debug:
            skeleton_img = draw_pose_skeleton(person_img, keypoints)
            cv2.imshow("Pose Detection", skeleton_img)
            cv2.imshow("Warped Garment", warped_garment)
            cv2.waitKey(0)
        
        # Save result if output path provided
        if output_path:
            cv2.imwrite(output_path, result)
        
        return result, "Virtual try-on successful!"
        
    except Exception as e:
        return None, f"Error during virtual try-on: {str(e)}"


def warp_garment_to_body(garment, keypoints, measurements):
    """
    Warp garment using perspective transform to fit body shape
    
    Args:
        garment: RGBA garment image
        keypoints: Body keypoints
        measurements: Body measurements
    
    Returns:
        Warped garment image
    """
    h, w = garment.shape[:2]
    
    # Define source points (garment corners)
    src_points = np.float32([
        [w * 0.2, 0],           # Top-left (neck area)
        [w * 0.8, 0],           # Top-right (neck area)
        [w * 0.9, h],           # Bottom-right (hip area)
        [w * 0.1, h]            # Bottom-left (hip area)
    ])
    
    # Define destination points (body keypoints)
    # Adjust for natural clothing drape
    shoulder_offset = 20  # Pixels beyond shoulder
    
    dst_points = np.float32([
        [keypoints['left_shoulder'][0] - shoulder_offset, keypoints['neck'][1]],
        [keypoints['right_shoulder'][0] + shoulder_offset, keypoints['neck'][1]],
        [keypoints['right_hip'][0] + 10, keypoints['right_hip'][1]],
        [keypoints['left_hip'][0] - 10, keypoints['left_hip'][1]]
    ])
    
    # Calculate perspective transform matrix
    matrix = cv2.getPerspectiveTransform(src_points, dst_points)
    
    # Apply transformation
    img_h, img_w = keypoints['image_height'], keypoints['image_width']
    warped = cv2.warpPerspective(garment, matrix, (img_w, img_h), 
                                 flags=cv2.INTER_LINEAR,
                                 borderMode=cv2.BORDER_CONSTANT,
                                 borderValue=(0, 0, 0, 0))
    
    return warped


def blend_garment_with_person(person_img, garment, keypoints, blend_alpha=0.85):
    """
    Blend garment with person image using alpha compositing
    
    Args:
        person_img: Original person image (BGR)
        garment: Warped garment image (RGBA)
        keypoints: Body keypoints
        blend_alpha: Blending factor (0-1)
    
    Returns:
        Blended result image
    """
    # Convert person image to RGBA
    person_rgba = cv2.cvtColor(person_img, cv2.COLOR_BGR2RGBA)
    
    # Ensure same size
    if person_rgba.shape[:2] != garment.shape[:2]:
        garment = cv2.resize(garment, (person_rgba.shape[1], person_rgba.shape[0]))
    
    # Extract alpha channel from garment
    garment_alpha = garment[:, :, 3] / 255.0
    garment_alpha = garment_alpha * blend_alpha  # Apply blend factor
    
    # Create mask to preserve person's face/head
    face_mask = create_face_preservation_mask(person_rgba.shape[:2], keypoints)
    garment_alpha = garment_alpha * (1 - face_mask)
    
    # Blend using alpha compositing
    result = person_rgba.copy().astype(float)
    
    for c in range(3):  # RGB channels
        result[:, :, c] = (garment_alpha * garment[:, :, c] + 
                          (1 - garment_alpha) * person_rgba[:, :, c])
    
    # Convert back to BGR
    result = result.astype(np.uint8)
    result_bgr = cv2.cvtColor(result, cv2.COLOR_RGBA2BGR)
    
    return result_bgr


def create_face_preservation_mask(image_shape, keypoints):
    """
    Create mask to preserve person's face and head
    
    Args:
        image_shape: (height, width)
        keypoints: Body keypoints
    
    Returns:
        Binary mask (0-1 float)
    """
    h, w = image_shape
    mask = np.zeros((h, w), dtype=np.float32)
    
    # Define face/head region
    nose_y = keypoints['nose'][1]
    neck_y = keypoints['neck'][1]
    shoulder_center_x = keypoints['shoulder_center'][0]
    
    # Create ellipse for head region
    head_height = neck_y - nose_y + 50  # Extra padding
    head_width = int(keypoints['shoulder_width'] * 0.6)
    
    center = (shoulder_center_x, nose_y - 20)
    axes = (head_width // 2, head_height)
    
    cv2.ellipse(mask, center, axes, 0, 0, 360, 1.0, -1)
    
    # Smooth edges
    mask = cv2.GaussianBlur(mask, (21, 21), 0)
    
    return mask


def create_result_with_comparison(person_img, result_img):
    """
    Create side-by-side comparison image
    
    Args:
        person_img: Original person image
        result_img: Try-on result image
    
    Returns:
        Combined comparison image
    """
    # Resize to same height if needed
    h1, w1 = person_img.shape[:2]
    h2, w2 = result_img.shape[:2]
    
    if h1 != h2:
        scale = h1 / h2
        result_img = cv2.resize(result_img, (int(w2 * scale), h1))
        h2, w2 = result_img.shape[:2]
    
    # Create combined image
    combined = np.hstack([person_img, result_img])
    
    # Add labels
    cv2.putText(combined, "Original", (20, 40), 
               cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.putText(combined, "Virtual Try-On", (w1 + 20, 40), 
               cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    return combined
