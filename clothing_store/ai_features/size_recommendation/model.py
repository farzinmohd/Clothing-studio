
import os
import joblib
import pandas as pd
import numpy as np

MODEL_PATH = os.path.join(os.path.dirname(__file__), "size_model.pkl")

_model_artifacts = None

def load_model():
    global _model_artifacts
    if _model_artifacts is None:
        if not os.path.exists(MODEL_PATH):
            return None
        _model_artifacts = joblib.load(MODEL_PATH)
    return _model_artifacts

def predict_size(height, weight, age, gender):
    """
    Returns: (predicted_size, confidence_score)
    """
    artifacts = load_model()
    
    if not artifacts:
        return None, 0.0
    
    model = artifacts['model']
    le_gender = artifacts['le_gender']
    
    # Preprocess
    try:
        gender_encoded = le_gender.transform([gender])[0]
    except:
        # Fallback if unknown gender, default to Male (1) or just 0
        gender_encoded = 0
        
    # Create DataFrame for prediction to match feature names
    X_input = pd.DataFrame([[height, weight, age, gender_encoded]], 
                           columns=['height', 'weight', 'age', 'gender'])
    
    # Predict
    prediction = model.predict(X_input)[0]
    probs = model.predict_proba(X_input)
    confidence = np.max(probs) * 100
    
    return prediction, round(confidence, 1)
