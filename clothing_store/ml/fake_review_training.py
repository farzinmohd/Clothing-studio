# ml/fake_review_training.py

import joblib
import random

from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score


# ----------------------------------
# STEP 1: CREATE DUMMY TRAINING DATA
# ----------------------------------
# Features:
# [review_length, repetition_ratio, rating_variance, sentiment_polarity, rule_score]
# Label:
# 1 = Fake review
# 0 = Genuine review

X = []
y = []

for _ in range(200):
    # Fake reviews
    review_length = random.randint(1, 4)
    repetition_ratio = random.uniform(0.6, 1.0)
    rating_variance = random.uniform(0.0, 0.1)
    sentiment = random.uniform(-0.2, 0.2)
    rule_score = random.uniform(0.6, 1.0)

    X.append([
        review_length,
        repetition_ratio,
        rating_variance,
        sentiment,
        rule_score
    ])
    y.append(1)

for _ in range(200):
    # Genuine reviews
    review_length = random.randint(8, 25)
    repetition_ratio = random.uniform(0.0, 0.3)
    rating_variance = random.uniform(0.3, 1.0)
    sentiment = random.uniform(0.3, 0.9)
    rule_score = random.uniform(0.0, 0.3)

    X.append([
        review_length,
        repetition_ratio,
        rating_variance,
        sentiment,
        rule_score
    ])
    y.append(0)


# ----------------------------------
# STEP 2: SPLIT DATA
# ----------------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)


# ----------------------------------
# STEP 3: TRAIN MODEL
# ----------------------------------
model = LogisticRegression()
model.fit(X_train, y_train)


# ----------------------------------
# STEP 4: EVALUATE
# ----------------------------------
predictions = model.predict(X_test)
accuracy = accuracy_score(y_test, predictions)

print(f"Model trained successfully")
print(f"Accuracy: {accuracy * 100:.2f}%")


# ----------------------------------
# STEP 5: SAVE MODEL
# ----------------------------------
joblib.dump(model, "ml/fake_review_model.pkl")

print("Model saved as ml/fake_review_model.pkl")
