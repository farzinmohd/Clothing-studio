from collections import Counter
import statistics


def detect_fake_review(review, user_reviews):
    """
    Rule-based fake review detection.
    Returns suspicion result with reasons.
    """

    reasons = []
    score = 0.0

    # -------------------------
    # Rule 1: Very short review
    # -------------------------
    words = review.comment.lower().split()
    if len(words) < 4:
        reasons.append("Very short review")
        score += 0.4

    # -------------------------
    # Rule 2: Repeated words
    # -------------------------
    if words:
        word_counts = Counter(words)
        most_common_word, count = word_counts.most_common(1)[0]

        if count / len(words) > 0.6:
            reasons.append("Repeated words detected")
            score += 0.3

    # -------------------------
    # Rule 3: Same rating everywhere
    # -------------------------
    ratings = [r.rating for r in user_reviews]

    if len(ratings) >= 3:
        try:
            variance = statistics.pvariance(ratings)
            if variance < 0.2:
                reasons.append("User gives same rating frequently")
                score += 0.3
        except Exception:
            pass

    return {
        "is_suspicious": score >= 0.5,
        "score": round(score, 2),
        "reasons": reasons
    }
