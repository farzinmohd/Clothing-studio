import cv2

# Load images
person_img = cv2.imread("person.jpg")      # demo model image
cloth_img = cv2.imread("cloth.png", cv2.IMREAD_UNCHANGED)  # transparent PNG

# Convert to grayscale
gray = cv2.cvtColor(person_img, cv2.COLOR_BGR2GRAY)

# Load Haarcascade for upper body
body_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_upperbody.xml"
)

# Detect upper body
bodies = body_cascade.detectMultiScale(
    gray,
    scaleFactor=1.1,
    minNeighbors=5
)

for (x, y, w, h) in bodies:
    # Resize clothing to fit body width
    cloth_resized = cv2.resize(cloth_img, (w, int(h * 0.6)))

    # Overlay clothing (basic)
    for i in range(cloth_resized.shape[0]):
        for j in range(cloth_resized.shape[1]):
            if cloth_resized[i, j][3] > 0:  # alpha channel
                person_img[y + i, x + j] = cloth_resized[i, j][:3]

    break  # demo: first detection only

# Show result
cv2.imshow("Virtual Try-On Preview", person_img)
cv2.waitKey(0)
cv2.destroyAllWindows()
