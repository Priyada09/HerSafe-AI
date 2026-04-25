"""
analyzer.py — HerSafe AI NLP Threat Detection Engine

Uses a layered keyword + pattern + sentiment approach.
No model training required. Easily swappable with a HuggingFace model.
"""

import re
from textblob import TextBlob

# ─── Threat Lexicons ───────────────────────────────────────────────────────────

THREAT_KEYWORDS = [
    "kill", "hurt", "find you", "know where you live", "watch out",
    "regret it", "come after you", "destroy you", "make you pay",
    "track you", "hunt you", "harm you", "stab", "shoot", "attack",
    "end you", "going to get you", "beat you", "i will find you",
    "you will pay", "you're dead", "dead meat"
]

ABUSE_KEYWORDS = [
    "stupid", "worthless", "idiot", "moron", "ugly", "disgusting",
    "pathetic", "loser", "trash", "garbage", "dumb", "freak",
    "nobody wants you", "hate you", "shut up", "get out of my sight"
]

HARASSMENT_KEYWORDS = [
    "always watching", "following you", "won't leave you alone",
    "never escape", "everywhere you go", "nobody will believe",
    "your fault", "deserve it", "i know your routine",
    "stalk", "obsessed with you", "can't hide from me"
]

MANIPULATION_KEYWORDS = [
    "you made me do this", "no one cares about you",
    "you're nothing without me", "you're lucky i",
    "nobody else would", "should be grateful",
    "you belong to me", "i own you"
]

# ─── Scoring weights ───────────────────────────────────────────────────────────

WEIGHTS = {
    "threat":      30,
    "abuse":       15,
    "harassment":  25,
    "manipulation":12,
}

# ─── Analysis function ─────────────────────────────────────────────────────────

def analyze_text(text: str) -> dict:
    lower = text.lower()
    flags = []
    score = 0

    # 1. Keyword matching
    threat_hits      = [w for w in THREAT_KEYWORDS      if w in lower]
    abuse_hits       = [w for w in ABUSE_KEYWORDS       if w in lower]
    harassment_hits  = [w for w in HARASSMENT_KEYWORDS  if w in lower]
    manipulation_hits= [w for w in MANIPULATION_KEYWORDS if w in lower]

    score += len(threat_hits)       * WEIGHTS["threat"]
    score += len(abuse_hits)        * WEIGHTS["abuse"]
    score += len(harassment_hits)   * WEIGHTS["harassment"]
    score += len(manipulation_hits) * WEIGHTS["manipulation"]

    if threat_hits:
        flags.append("Threatening language")
    if abuse_hits:
        flags.append("Abusive language")
    if harassment_hits:
        flags.append("Harassment pattern")
    if manipulation_hits:
        flags.append("Manipulation tactic")

    # 2. Tone signals
    exclamation_count = text.count("!")
    caps_ratio = len(re.findall(r"[A-Z]", text)) / max(len(text), 1)

    if exclamation_count > 2:
        score += 5
    if caps_ratio > 0.5 and len(text) > 8:
        score += 10
        flags.append("Aggressive tone (excessive caps)")

    # 3. Sentiment analysis via TextBlob
    blob = TextBlob(text)
    sentiment_polarity = blob.sentiment.polarity  # -1.0 (negative) to 1.0 (positive)

    if sentiment_polarity < -0.6:
        score += 15
        flags.append("Strongly negative sentiment")
    elif sentiment_polarity < -0.3:
        score += 8

    # 4. Cap score at 100
    score = min(score, 100)

    # 5. Determine category
    if score >= 60:
        category = "Dangerous"
        alert = (
            "⛔ Serious threat indicators detected. This message contains language "
            "associated with physical threats, stalking, or severe harassment. "
            "Consider blocking the sender and reporting to authorities or a trusted person."
        )
    elif score >= 20:
        category = "Suspicious"
        alert = (
            "⚠️ Potentially harmful content detected. This message contains language "
            "that may indicate hostility, manipulation, or mild harassment. "
            "Proceed with caution."
        )
    else:
        category = "Safe"
        alert = "✅ No significant threat indicators found. This message appears safe."

    return {
        "category": category,
        "severity_score": score,
        "alert": alert,
        "flags": flags,
        "sentiment": round(sentiment_polarity, 3)
    }
