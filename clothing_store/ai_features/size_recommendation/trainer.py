
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import joblib
import os
import random

# Path to save the model
MODEL_PATH = os.path.join(os.path.dirname(__file__), "size_model.pkl")

def generate_dummy_data(n_samples=5000):
    """
    Generate synthetic data for training based on BMI rules.
    """
    data = []
    
    # ---------------------------
    # LOGIC RULES for Ground Truth
    # ---------------------------
    def get_size(height, weight, gender):
        bmi = weight / ((height / 100) ** 2)
        
        if gender == 'M':
            if weight < 65: size_idx = 0 # S
            elif weight < 76: size_idx = 1 # M
            elif weight < 88: size_idx = 2 # L
            else: size_idx = 3 # XL
            
            # Height overrides for length
            if height >= 184 and size_idx < 2:
                size_idx = 2
            elif height >= 176 and size_idx < 1:
                size_idx = 1
                
            if bmi >= 28.0:
                size_idx = min(3, size_idx + 1)
                
        else: # Female
            if weight < 52: size_idx = 0 # S
            elif weight < 62: size_idx = 1 # M
            elif weight < 72: size_idx = 2 # L
            else: size_idx = 3 # XL
            
            if height >= 173 and size_idx < 2:
                size_idx = 2
            elif height >= 165 and size_idx < 1:
                size_idx = 1
                
            if bmi >= 28.0:
                size_idx = min(3, size_idx + 1)
                
        sizes = ['S', 'M', 'L', 'XL']
        return sizes[size_idx]

    genders = ['M', 'F']
    
    for _ in range(n_samples):
        gender = random.choice(genders)
        
        # Random realistic height/weight
        if gender == 'M':
            height = random.randint(140, 200)  # Expanded range (was 160-200)
            weight = random.randint(30, 120)   # Expanded range (was 50-120)
        else:
            height = random.randint(130, 180)  # Expanded range
            weight = random.randint(30, 100)   # Expanded range
            
        age = random.randint(15, 70)  # Expanded age
        
        size = get_size(height, weight, gender)
        
        # Add some noise/randomness to make it realistic (10% chance of being wrong size)
        if random.random() < 0.1:
            sizes = ['S', 'M', 'L', 'XL']
            size = random.choice(sizes)
            
        data.append([height, weight, age, gender, size])
            
    df = pd.DataFrame(data, columns=['height', 'weight', 'age', 'gender', 'size'])
    return df

def train_model():
    print("⏳ Generating dummy data...")
    df = generate_dummy_data()
    
    X = df[['height', 'weight', 'age', 'gender']]
    y = df['size']
    
    # Encode Gender
    le_gender = LabelEncoder()
    X['gender'] = le_gender.fit_transform(X['gender']) # M=1, F=0 approx
    
    # Train Model
    print("🧠 Training Random Forest...")
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X, y)
    
    # Save artifacts
    artifacts = {
        'model': clf,
        'le_gender': le_gender
    }
    
    joblib.dump(artifacts, MODEL_PATH)
    print(f"✅ Model saved to {MODEL_PATH}")

if __name__ == "__main__":
    train_model()
