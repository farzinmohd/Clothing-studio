import cv2
import numpy as np
import os
import math

# Try to import dlib, fallback to Haar Cascade if not available
try:
    import dlib
    DLIB_AVAILABLE = True
except ImportError:
    DLIB_AVAILABLE = False
    print("dlib not available, using Haar Cascade fallback")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CASCADE_PATH = os.path.join(
    BASE_DIR,
    "haarcascade_frontalface_default.xml"
)

# Initialize face detectors
face_cascade = cv2.CascadeClassifier(CASCADE_PATH)
if DLIB_AVAILABLE:
    dlib_detector = dlib.get_frontal_face_detector()


def detect_face_dlib(gray_image):
    """
    Detect face using dlib (more accurate)
    Returns: (x, y, w, h) or None
    """
    if not DLIB_AVAILABLE:
        return None
    
    try:
        faces = dlib_detector(gray_image, 1)
        if len(faces) == 0:
            return None
        
        # Get largest face
        largest_face = max(faces, key=lambda rect: rect.width() * rect.height())
        
        # Convert dlib rectangle to (x, y, w, h)
        x = largest_face.left()
        y = largest_face.top()
        w = largest_face.width()
        h = largest_face.height()
        
        return (x, y, w, h)
    except Exception as e:
        print(f"dlib detection failed: {e}")
        return None


def detect_face_haar(gray_image):
    """
    Detect face using Haar Cascade (fallback)
    Returns: (x, y, w, h) or None
    """
    detection_params = [
        # Attempt 1: strict (best quality)
        dict(scaleFactor=1.3, minNeighbors=6, minSize=(80, 80)),
        # Attempt 2: medium
        dict(scaleFactor=1.2, minNeighbors=5, minSize=(60, 60)),
        # Attempt 3: relaxed (small / difficult faces)
        dict(scaleFactor=1.1, minNeighbors=4, minSize=(40, 40)),
    ]
    
    faces = []
    for params in detection_params:
        faces = face_cascade.detectMultiScale(gray_image, **params)
        if len(faces) > 0:
            break
    
    if len(faces) == 0:
        return None
    
    # Get largest face
    faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
    return tuple(faces[0])


def extract_forehead_region(face_roi, x, y, w, h):
    """
    Extract forehead region (top 30% of face)
    This area has the most consistent skin tone
    """
    forehead_height = int(h * 0.3)
    forehead_roi = face_roi[0:forehead_height, :]
    return forehead_roi


def calculate_ita_angle(face_roi):
    """
    Calculate ITA° (Individual Typology Angle)
    Scientific standard for skin tone measurement
    
    Formula: ITA° = arctan((L* - 50) / b*) × (180/π)
    
    Where:
    - L* = Lightness (0-100)
    - b* = Blue-Yellow axis (-128 to 127)
    """
    # Convert to LAB color space
    lab = cv2.cvtColor(face_roi, cv2.COLOR_BGR2LAB)
    
    # Extract L and b channels
    L = np.mean(lab[:, :, 0])  # Lightness
    b = np.mean(lab[:, :, 2])  # Blue-Yellow
    
    # Avoid division by zero
    if abs(b) < 0.001:
        b = 0.001
    
    # Calculate ITA° angle
    ita_radians = math.atan((L - 50) / b)
    ita_degrees = math.degrees(ita_radians)
    
    return ita_degrees


def classify_skin_tone_ita(ita_angle):
    """
    Classify skin tone based on ITA° value
    Using scientific dermatology standards
    
    ITA° Ranges (Scientific Standard):
    > 55°  : Very Fair
    41-55° : Fair
    28-41° : Medium
    10-28° : Olive
    < 10°  : Dark
    """
    if ita_angle > 55:
        return "Very Fair"
    elif ita_angle > 41:
        return "Fair"
    elif ita_angle > 28:
        return "Medium"
    elif ita_angle > 10:
        return "Olive"
    else:
        return "Dark"


def detect_skin_tone(image_path):
    """
    Detect face → extract forehead → analyze skin tone using ITA°
    
    Improvements:
    - Uses dlib for better face detection (fallback to Haar Cascade)
    - Analyzes forehead region (most consistent skin tone)
    - Uses ITA° (Individual Typology Angle) - scientific standard
    - LAB color space (lighting-independent)
    
    Returns:
        (skin_tone, boxed_image_path)
    """
    
    img = cv2.imread(image_path)
    if img is None:
        return "Medium", None
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 🔍 FACE DETECTION (dlib first, then Haar Cascade fallback)
    face_coords = None
    
    if DLIB_AVAILABLE:
        face_coords = detect_face_dlib(gray)
        if face_coords:
            print("Face detected using dlib")
    
    if face_coords is None:
        face_coords = detect_face_haar(gray)
        if face_coords:
            print("Face detected using Haar Cascade (fallback)")
    
    # If no face detected at all
    if face_coords is None:
        print("No face detected")
        return "Medium", None
    
    x, y, w, h = face_coords
    
    # Draw bounding box
    boxed_img = img.copy()
    cv2.rectangle(
        boxed_img,
        (x, y),
        (x + w, y + h),
        (0, 255, 0),
        2
    )
    
    # Crop face region
    face_roi = img[y:y + h, x:x + w]
    
    # 🎯 EXTRACT FOREHEAD REGION (most consistent skin tone)
    forehead_roi = extract_forehead_region(face_roi, x, y, w, h)
    
    # Draw forehead region indicator (optional - for debugging)
    forehead_h = int(h * 0.3)
    cv2.rectangle(
        boxed_img,
        (x, y),
        (x + w, y + forehead_h),
        (255, 0, 0),  # Blue rectangle for forehead
        1
    )
    
    # Calculate ITA° (Individual Typology Angle)
    try:
        ita_angle = calculate_ita_angle(forehead_roi)
        skin_tone = classify_skin_tone_ita(ita_angle)
        print(f"ITA° = {ita_angle:.2f}° -> Skin Tone: {skin_tone}")
    except Exception as e:
        print(f"ITA° calculation failed: {e}, using fallback")
        # Fallback to old HSV method
        hsv = cv2.cvtColor(forehead_roi, cv2.COLOR_BGR2HSV)
        avg_v = np.mean(hsv[:, :, 2])
        
        if avg_v > 180:
            skin_tone = "Very Fair"
        elif avg_v > 150:
            skin_tone = "Fair"
        elif avg_v > 120:
            skin_tone = "Medium"
        elif avg_v > 90:
            skin_tone = "Olive"
        else:
            skin_tone = "Dark"
    
    # Save boxed image safely
    output_path = image_path.replace(".", "_boxed.")
    cv2.imwrite(output_path, boxed_img)
    
    return skin_tone, output_path
