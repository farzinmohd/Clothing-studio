import cv2
import numpy as np
from PIL import Image

# Load OpenCV face detector
FACE_CASCADE = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

def detect_skin_tone(image_path):
    """
    Deterministic skin tone detection using OpenCV + HSV rules
    """

    # Load image
    image = cv2.imread(image_path)
    if image is None:
        return "Medium"  # safe fallback

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Detect face
    faces = FACE_CASCADE.detectMultiScale(
        gray, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100)
    )

    if len(faces) == 0:
        return "Medium"  # fallback if no face detected

    # Take first detected face
    x, y, w, h = faces[0]
    face = image[y:y+h, x:x+w]

    # Convert face to HSV
    hsv = cv2.cvtColor(face, cv2.COLOR_BGR2HSV)

    # Calculate average HSV
    avg_hsv = np.mean(hsv.reshape(-1, 3), axis=0)
    h, s, v = avg_hsv

    # RULE-BASED CLASSIFICATION (NO RANDOMNESS)
    if v > 200 and s < 60:
        return "Very Fair"
    elif v > 170:
        return "Fair"
    elif v > 135:
        return "Medium"
    elif v > 110:
        return "Olive"
    else:
        return "Dark"
