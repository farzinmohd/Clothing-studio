"""
Enhanced Pose Detection for Virtual Try-On
Detects full upper body keypoints for accurate garment placement
"""

import cv2
import mediapipe as mp
import numpy as np

mp_pose = mp.solutions.pose


def detect_shoulders(image_path):
    """
    LEGACY FUNCTION - Kept for backward compatibility
    Detect shoulders only (original function)
    """
    image = cv2.imread(image_path)
    if image is None:
        return None

    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    with mp_pose.Pose(static_image_mode=True) as pose:
        results = pose.process(image_rgb)

        if not results.pose_landmarks:
            return None

        landmarks = results.pose_landmarks.landmark

        left = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
        right = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]

        h, w, _ = image.shape

        left_px = (int(left.x * w), int(left.y * h))
        right_px = (int(right.x * w), int(right.y * h))

        return {
            "left": left_px,
            "right": right_px,
            "width": abs(right_px[0] - left_px[0]),
            "y": int((left_px[1] + right_px[1]) / 2)
        }


def detect_full_body_pose(image_path):
    """
    Detect full body pose with all necessary keypoints for virtual try-on
    
    Returns:
        dict: Keypoints with pixel coordinates or None if detection fails
    """
    image = cv2.imread(image_path)
    if image is None:
        return None
    
    h, w, _ = image.shape
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    with mp_pose.Pose(static_image_mode=True, min_detection_confidence=0.5) as pose:
        results = pose.process(image_rgb)
        
        if not results.pose_landmarks:
            return None
        
        landmarks = results.pose_landmarks.landmark
        
        # Extract key body points
        keypoints = {
            # Shoulders
            'left_shoulder': _landmark_to_pixel(landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER], w, h),
            'right_shoulder': _landmark_to_pixel(landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER], w, h),
            
            # Elbows
            'left_elbow': _landmark_to_pixel(landmarks[mp_pose.PoseLandmark.LEFT_ELBOW], w, h),
            'right_elbow': _landmark_to_pixel(landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW], w, h),
            
            # Hips
            'left_hip': _landmark_to_pixel(landmarks[mp_pose.PoseLandmark.LEFT_HIP], w, h),
            'right_hip': _landmark_to_pixel(landmarks[mp_pose.PoseLandmark.RIGHT_HIP], w, h),
            
            # Wrists (for sleeve placement)
            'left_wrist': _landmark_to_pixel(landmarks[mp_pose.PoseLandmark.LEFT_WRIST], w, h),
            'right_wrist': _landmark_to_pixel(landmarks[mp_pose.PoseLandmark.RIGHT_WRIST], w, h),
            
            # Nose (for face reference)
            'nose': _landmark_to_pixel(landmarks[mp_pose.PoseLandmark.NOSE], w, h),
        }
        
        # Calculate derived points
        keypoints['shoulder_center'] = _midpoint(keypoints['left_shoulder'], keypoints['right_shoulder'])
        keypoints['hip_center'] = _midpoint(keypoints['left_hip'], keypoints['right_hip'])
        keypoints['neck'] = _calculate_neck_position(keypoints['nose'], keypoints['shoulder_center'])
        
        # Add image dimensions
        keypoints['image_width'] = w
        keypoints['image_height'] = h
        
        return keypoints


def _landmark_to_pixel(landmark, width, height):
    """Convert normalized landmark to pixel coordinates"""
    return (int(landmark.x * width), int(landmark.y * height))


def _midpoint(point1, point2):
    """Calculate midpoint between two points"""
    return (
        (point1[0] + point2[0]) // 2,
        (point1[1] + point2[1]) // 2
    )


def _calculate_neck_position(nose, shoulder_center):
    """Estimate neck position between nose and shoulders"""
    # Neck is approximately 70% of the way from nose to shoulder center
    x = int(nose[0] * 0.3 + shoulder_center[0] * 0.7)
    y = int(nose[1] * 0.3 + shoulder_center[1] * 0.7)
    return (x, y)


def get_body_measurements(keypoints):
    """
    Calculate body measurements from keypoints
    
    Returns:
        dict: Body measurements in pixels
    """
    measurements = {
        'shoulder_width': _distance(keypoints['left_shoulder'], keypoints['right_shoulder']),
        'torso_height': _distance(keypoints['shoulder_center'], keypoints['hip_center']),
        'left_arm_length': _distance(keypoints['left_shoulder'], keypoints['left_wrist']),
        'right_arm_length': _distance(keypoints['right_shoulder'], keypoints['right_wrist']),
        'chest_width': int(_distance(keypoints['left_shoulder'], keypoints['right_shoulder']) * 1.2),  # Slightly wider
        'waist_width': _distance(keypoints['left_hip'], keypoints['right_hip']),
    }
    
    return measurements


def _distance(point1, point2):
    """Calculate Euclidean distance between two points"""
    return int(np.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2))


def draw_pose_skeleton(image, keypoints):
    """
    Draw skeleton on image for debugging/visualization
    
    Args:
        image: OpenCV image
        keypoints: Dictionary of keypoints
    
    Returns:
        Image with skeleton drawn
    """
    img_copy = image.copy()
    
    # Define connections
    connections = [
        ('left_shoulder', 'right_shoulder'),
        ('left_shoulder', 'left_elbow'),
        ('right_shoulder', 'right_elbow'),
        ('left_elbow', 'left_wrist'),
        ('right_elbow', 'right_wrist'),
        ('left_shoulder', 'left_hip'),
        ('right_shoulder', 'right_hip'),
        ('left_hip', 'right_hip'),
        ('shoulder_center', 'hip_center'),
    ]
    
    # Draw connections
    for start, end in connections:
        if start in keypoints and end in keypoints:
            cv2.line(img_copy, keypoints[start], keypoints[end], (0, 255, 0), 2)
    
    # Draw keypoints
    for name, point in keypoints.items():
        if isinstance(point, tuple) and len(point) == 2:
            cv2.circle(img_copy, point, 5, (0, 0, 255), -1)
            cv2.putText(img_copy, name[:3], (point[0] + 10, point[1]), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 255), 1)
    
    return img_copy
