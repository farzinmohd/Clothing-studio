# Project Overview: Tailored Elegance

## 1. Project Overview

**Tailored Elegance** is a sophisticated e-commerce platform dedicated to menswear, specifically designed to elevate the online shopping experience through AI-driven personalization. The project aims to blend traditional e-commerce functionality with cutting-edge artificial intelligence to offer features like an AI Stylist, visual search, and dynamic pricing. The objective is to provide users with a seamless, personalized shopping journey ("fashion that fits your lifestyle") while giving administrators powerful tools for inventory and price management.

## 2. Technology Stack

### Frontend

- **Frameworks/Libraries:**
  - **Bootstrap 5.3.2**: Used for responsive, mobile-first layout and UI components (via CDN).
  - **Vanilla JavaScript**: Handles client-side interactivity, such as search suggestions and dynamic DOM updates.
  - **Font Awesome 6.4.0**: Provides iconography throughout the application.
  - **Django Templates**: Server-side rendering engine used to generate HTML dynamically.
  - **CSS**: Custom styling (`navbar.css`, `index.css`) complements Bootstrap to achieve a premium "Darkly" or custom aesthetic.

### Backend

- **Language**: **Python 3.x**
  - Core logic and data processing.
- **Framework**: **Django 5.2.9**
  - Handles routing, ORM, authentication, and core business process.
  - **Jazzmin**: Utilized for a customized, dark-themed Admin interface (`django-jazzmin`).
- **Dependencies**:
  - `django-decouple`: For managing configuration and secrets.
  - `Pillow`: For image processing.

### Database

- **System**: **MySQL**
  - The project uses a MySQL database named `clothing_db`.
- **ORM**: Django ORM is used for all database interactions and migrations.

### Additional Tools & Services

- **Stripe**: Integrated for secure payment processing.
- **TensorFlow / Keras**: For running deep learning models (MobileNetV2).
- **Scikit-Learn**: Used for clustering algorithms (KMeans) in color detection.

## 3. Features

### Core E-Commerce Features

- **User Authentication**: Sign up, login, and profile management including order history.
- **Product Catalog**: Comprehensive listing with categories, search, and filtering.
- **Product Details**: Multi-image support, size/color browsing, and reviews.
- **Shopping Cart & Checkout**: Full cart management and secure checkout flow with coupon support.
- **Wishlist**: Users can save items for later.
- **Admin Dashboard**: Advanced admin interface using Jazzmin for managing products, orders, and users.

### AI Features (Highlights)

- **✨ AI Stylist**: A personalized recommendation engine that suggests products based on user interactions.
- **📷 Visual Search**: Allows users to search for products using images, leveraging object detection.
- **Smart Tagging**: Automatically generates tags and detects dominant colors for products using computer vision, streamlining inventory management.
- **Dynamic Pricing**: An AI module that adjusts product prices based on demand scores and other metrics to optimize sales.

## 4. AI Technology

The project leverages Python's rich data science ecosystem to implement intelligent features:

- **Frameworks**:

  - **TensorFlow (Keras)**: Runs the pre-trained **MobileNetV2** model (trained on ImageNet) for object detection and image classification.
  - **Scikit-Learn**: Uses **KMeans Clustering** to extract dominant colors from product images.
  - **NumPy**: Handles efficient array manipulations for image processing.

- **Integration**:
  - AI modules are encapsulated in the `ai_features` app.
  - **Tagging**: When product images are processed, the `predict_image_tags` function uses MobileNetV2 to identify clothing types (e.g., "jersey") and KMeans to identify colors (e.g., "Red", "Black").
  - **Recommendations**: Implicit feedback (views, wishlists, purchases) is tracked in the `UserProductInteraction` table to power collaborative filtering or score-based recommendations.
  - **Pricing**: A serialized model (`pricing_model.pkl`) is likely used to predict optimal price points based on demand data.

## 5. Database Design

The database schema is designed to support a robust e-commerce workflow with specific extensions for AI data.

### Key Tables & Relationships

#### Products & Inventory

- **Category**: `name`
- **Product**: The central table containing:
  - `name`, `description`, `price`, `stock`
  - **AI Fields**: `color` (main color), `tags` (AI-generated), `current_demand_score` (for pricing).
  - _Relationship_: ForeignKey to `Category`.
- **ProductVariant**: Handles SKU variations (Size/Color).
  - _Relationship_: ForeignKey to `Product`.
- **ProductImage**: Stores multiple images per product.

#### Orders & Sales

- **Order**: Tracks user orders with status (`pending`, `shipped`, etc.) and totals.
  - `total_amount`, `discount_amount`, `final_amount`, `payment_method`.
  - _Relationship_: ForeignKey to `User`, `Address`, and `Coupon`.
- **OrderItem**: Links specific products/variants to an order.
  - `quantity`, `price` at time of purchase.
- **Coupon**: Stores discount codes (`active`, `expiry_date`, `discount_type`).

#### User & Interactions

- **Review**: User ratings and comments for products.
- **Wishlist**: Links `User` and `Product`.
- **UserProductInteraction** (AI):
  - Tracks specific actions: `View`, `Wishlist`, `Purchase`.
  - Used to build user preference profiles.
  - _Relationship_: ForeignKey to `User` and `Product`.

## 6. Detailed AI Technology Breakdown

| Feature                       | Tech Stack & Libraries                                              | Analysis of Implementation                                                                                                                                                                                                                                      |
| :---------------------------- | :------------------------------------------------------------------ | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Real-Time Dynamic Pricing** | **Scikit-Learn** (`RandomForestRegressor`), **Pandas**, **NumPy**   | Uses a **Random Forest** model trained on synthetic data (Views + Cart Adds + Sales). It calculates a `demand_score` (0-100) and adjusts the base price by **+10% to -10%** based on this score.                                                                |
| **AI Size Recommendation**    | **Scikit-Learn** (`joblib` for loading model), **Pandas**           | Uses a pre-trained classification model (`size_model.pkl`) to predict clothing size (S/M/L/XL) based on user inputs: `height`, `weight`, `age`, and `gender`.                                                                                                   |
| **Visual Search**             | **TensorFlow / Keras** (`ResNet50`), **Pillow** (PIL), **NumPy**    | **Deep Learning approach**: Extracts features from images using a pre-trained **ResNet50** (structure) and combines them with **Color Histograms** (color). It uses **Cosine Similarity** to find the closest matching products in the catalog.                 |
| **Smart Tagging**             | **TensorFlow / Keras** (`MobileNetV2`), **Scikit-Learn** (`KMeans`) | **Object Detection**: Uses **MobileNetV2** (ImageNet weights) to identify the item type (e.g., "Sweatshirt").<br>**Color Detection**: Uses **KMeans Clustering** to find the dominant colors in the image pixel data.                                           |
| **Skin Tone Recommendation**  | **OpenCV** (`cv2`), **Haar Cascades**                               | **Computer Vision approach**: Detects faces using a standard Haar Cascade classifier. It then analyzes the **HSV** (Hue, Saturation, Value) brightness channel of the face region to categorize skin tone into 5 heuristic buckets (Fair, Medium, Olive, etc.). |
| **Fake Review Detection**     | **Python Standard Logic** (No AI/ML)                                | **Rule-Based System**: It is _not_ AI-based. It flags reviews based on:<br>1. Short length (< 4 words)<br>2. Repeated words (> 60% frequency)<br>3. Low variance in user's rating history.                                                                      |
| **AI Based Sentiment NLP**    | **TextBlob**                                                        | Uses `TextBlob` library to calculate the **polarity** of the review text. <br>- `Polarity > 0.1` = **Positive**<br>- `Polarity < -0.1` = **Negative**<br>- Otherwise = **Neutral**                                                                              |

## 7. API Usage

The project utilizes APIs primarily for internal communication between the frontend and backend, with some external integrations.

- **Internal APIs**:

  - The project does **not** use the Django Rest Framework (DRF) for a public REST API.
  - Instead, it employs standard Django Views returning `JsonResponse` to serve data to frontend AJAX calls (using `fetch()` in JavaScript).
  - **Key Internal Endpoints**:
    - `/products/search-suggestions/`: Provides real-time search suggestions.
    - `/ai/predict-size/`: Accepts user measurements and returns size recommendations.

- **External APIs**:
  - **Stripe**: Integrated for secure payment processing using `STRIPE_PUBLIC_KEY`.

## 8. Conclusion

The **Tailored Elegance** project is a modern, full-stack e-commerce solution that stands out by integrating practical AI implementations directly into the Django ecosystem. By combining a reliable MySQL/Django backend with a responsive Bootstrap frontend, it ensures a solid user experience. The inclusion of **TensorFlow**, **Scikit-Learn**, and **OpenCV** enables advanced features like **Visual Search**, **Smart Tagging**, and **Skin Tone Analysis**, automating complex tasks and providing personalized experiences that are typically found only in large-scale enterprise platforms.
