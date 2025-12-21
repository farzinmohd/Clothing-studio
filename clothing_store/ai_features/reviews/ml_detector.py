import joblib
import os

# Load model only once (safe & fast)
MODEL_PATH = os.path.join("ml", "fake_review_model.pkl")
_model = None


def _load_model():
    global _model
    if _model is None:
        _model = joblib.load(MODEL_PATH)
    return _model


def get_fake_probability(features):
    """
    features = [
        review_length,
        repetition_ratio,
        rating_variance,
        sentiment_polarity,
        rule_score
    ]
    Returns probability (0.0 – 1.0)
    """
    model = _load_model()
    prob = model.predict_proba([features])[0][1]
    return round(float(prob), 2)
