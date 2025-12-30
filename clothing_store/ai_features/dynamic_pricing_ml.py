import pandas as pd
import numpy as np
import os
import joblib
from sklearn.ensemble import RandomForestRegressor
from django.conf import settings

# Path to save the trained model
MODEL_PATH = os.path.join(settings.BASE_DIR, 'ai_features', 'pricing_model.pkl')

def train_pricing_model():
    """
    Trains a Random Forest model on SYNTHETIC data to learn pricing rules.
    Concepts:
    - High View + Low Stock = High Demand (Score -> 100)
    - Low View + High Stock = Low Demand (Score -> 0)
    """
    # 1. Generate Synthetic Data
    data = []
    for _ in range(1000):
        views = np.random.randint(0, 500)
        cart_adds = np.random.randint(0, 50)
        stock = np.random.randint(0, 100)
        
        # Heuristic for "True Demand Score" (The target we want AI to learn)
        # Views weight: 0.3, Cart weight: 2.0 (stronger signal), Stock penalty (scarcity)
        
        score = (views * 0.1) + (cart_adds * 3.0)
        
        # Scarcity Multiplier
        if stock < 5:
            score *= 1.5
        elif stock > 50:
            score *= 0.8
            
        # Normalize roughly to 0-100
        score = min(max(score, 0), 100)
        
        data.append([views, cart_adds, stock, score])

    df = pd.DataFrame(data, columns=['views', 'cart_adds', 'stock', 'demand_score'])

    # 2. Train Model
    X = df[['views', 'cart_adds', 'stock']]
    y = df['demand_score']

    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)

    # 3. Save Model
    joblib.dump(model, MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")
    return model

def predict_demand_score(product):
    """
    Returns a Demand Score (0-100) for a product.
    """
    # Load model (or train if missing)
    if os.path.exists(MODEL_PATH):
        model = joblib.load(MODEL_PATH)
    else:
        print("Model not found. Training new one...")
        model = train_pricing_model()

    # Create input vector
    # Sum of stock across all variants
    total_stock = product.variants.aggregate(total=models.Sum('stock'))['total'] or 0
    
    features = pd.DataFrame([[
        product.view_count,
        product.cart_add_count,
        total_stock
    ]], columns=['views', 'cart_adds', 'stock'])
    
    score = model.predict(features)[0]
    return int(score)

def calculate_new_price(product, demand_score):
    """
    Adjusts price based on Demand Score.
    - Score > 80: +10%
    - Score > 60: +5%
    - Score < 20: -10% (Discount)
    - Score < 40: -5%
    """
    base = float(product.base_price) if product.base_price else float(product.price)
    
    if demand_score > 80:
        factor = 1.10
    elif demand_score > 60:
        factor = 1.05
    elif demand_score < 20:
        factor = 0.90
    elif demand_score < 40:
        factor = 0.95
    else:
        factor = 1.0  # Neutral

    new_price = round(base * factor, 2)
    return new_price

# Helper for Django Aggregation hook
from django.db import models
