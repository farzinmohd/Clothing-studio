# 👗 Tailored Elegance - AI-Powered Fashion E-Commerce

**Tailored Elegance** is a next-generation e-commerce platform that blends traditional shopping with cutting-edge AI features to personalize the user experience.

![Project Banner](https://via.placeholder.com/1000x300?text=Tailored+Elegance+AI)

## ✨ Key Features

### 🧠 AI & Machine Learning

- **📷 Visual Search ("Shop the Look")**: Upload any photo (e.g., from Pinterest), and our **EfficientNetB0 + Enhanced Color Matching** engine will find the most similar products in your catalog based on **Style, Color Distribution & Dominant Colors**. Results include confidence scores showing match quality.

* **🏷️ Smart Tagging**: Automatically tagging products using **MobileNetV2** (Object Detection) and **K-Means Clustering** (Color Analysis).

- **🤖 Elegance Bot (Shopping Assistant)**: A smart chat interface that answers FAQs (Shipping, Returns, etc.) and offers **AI Product Discovery**. It can find specific items like "blue shirts" or "formal wear" and display them in an interactive carousel.

* **📏 Smart Size Predictor**: Enter your height, weight, and age to get an instant size recommendation (S/M/L/XL) with confidence scoring.
* **🎨 Skin Tone Analysis**: Upload a selfie to detect your skin tone (Cool/Warm/Neutral) and get personalized color recommendations.
* **🤖 Virtual Try-On**: (Beta) Visualize how clothes might look on your body shape.
* **📈 Dynamic Pricing**: AI algorithms adjust product prices based on real-time demand signals.

### 🛍️ Core E-Commerce

- **User Accounts**: Secure Login/Register with Profile management.
- **Product Catalog**: Categories, Variants (Sizes/Colors), Reviews, and Wishlists.
- **Shopping Cart**: Database-backed cart with session persistence.
- **Checkout**: Order placement, Coupon codes, and Order tracking.
- **Payment**: Integrated Stripe/Payment gateway placeholders.

### 📊 Admin Dashboard

- **Analytics**: Visual charts for Monthly Sales, Revenue, and Order Status.
- **Reports**: PDF & CSV export for sales data.
- **AI Control**: Trigger manual re-indexing of AI embeddings.

---

## 🛠️ Technology Stack

- **Backend**: Django 5.2 (Python)
- **Database**: MySQL
- **AI Frameworks**: TensorFlow, Keras (ResNet50), NumPy, OpenCV, MediaPipe
- **Frontend**: Bootstrap 5, Vanilla JS, Jinja2 Templates
- **Admin UI**: Jazzmin

---

## 🚀 Installation & Setup

### Prerequisites

- Python 3.10+
- MySQL Server installed and running

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/clothing-store.git
cd clothing-store
```

### 2. Set Up Virtual Environment

```bash
python -m venv venv
# Windows
.\venv\Scripts\activate
# Mac/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

_Note: This will install Django, TensorFlow, and other required libraries._

### 4. Configure Database

1.  Create a MySQL database named `clothing_db`.
2.  Update `clothing_store/settings.py` with your DB credentials if they differ from default:
    ```python
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'clothing_db',
            'USER': 'root',
            'PASSWORD': 'your_password',
            ...
        }
    }
    ```

### 5. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Build AI Embeddings (Important!)

For Visual Search to work, you must generate the initial AI fingerprints for your products:

```bash
python manage.py build_embeddings
```

### 7. Run the Server

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000` to start shopping! 🚀

---

## 🧪 Testing AI Features

1.  **Visual Search**: Click the 📷 icon in the navbar. Upload a photo of a red dress. Watch it find red dresses in your store!
2.  **Elegance Bot**: Click the chat bubble in the bottom right. Ask "What is your return policy?" or "Show me blue shirts".
3.  **Size Predictor**: Go to any product page -> "What's my size?".
4.  **Skin Tone**: Go to "AI Stylist" in the navbar.

---

## 👤 Admin Access

- **URL**: `/admin`
- **Username**: `admin` (Create via `python manage.py createsuperuser`)
