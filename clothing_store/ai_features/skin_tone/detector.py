import cv2
import numpy as np
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CASCADE_PATH = os.path.join(
    BASE_DIR,
    "haarcascade_frontalface_default.xml"
)

face_cascade = cv2.CascadeClassifier(CASCADE_PATH)


def detect_skin_tone(image_path):
    """
    Detect face → draw bounding box → analyze skin tone
    """

    img = cv2.imread(image_path)
    if img is None:
        return "Medium", None

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 🔁 MULTIPLE FACE DETECTION ATTEMPTS
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
        faces = face_cascade.detectMultiScale(gray, **params)
        if len(faces) > 0:
            break  # ✅ Face found

    # ❌ If no face detected at all
    if len(faces) == 0:
        return "Medium", None

    # ✅ Take the largest face (more reliable)
    faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
    x, y, w, h = faces[0]

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

    # --- SKIN TONE HEURISTIC ---
    hsv = cv2.cvtColor(face_roi, cv2.COLOR_BGR2HSV)
    avg_v = np.mean(hsv[:, :, 2])  # brightness channel

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
