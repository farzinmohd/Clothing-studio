import cv2
import mediapipe as mp

mp_pose = mp.solutions.pose

def detect_shoulders(image_path):
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
