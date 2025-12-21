# ai_features/reviews/sentiment.py

from textblob import TextBlob


def analyze_review_sentiment(text):
    """
    Analyze sentiment of a review comment.

    Returns:
        {
            'label': 'Positive' | 'Neutral' | 'Negative',
            'polarity': float
        }
    """

    if not text:
        return {
            'label': 'Neutral',
            'polarity': 0.0
        }

    blob = TextBlob(text)
    polarity = blob.sentiment.polarity

    if polarity > 0.1:
        label = 'Positive'
    elif polarity < -0.1:
        label = 'Negative'
    else:
        label = 'Neutral'

    return {
        'label': label,
        'polarity': round(polarity, 2)
    }
