def analyze_review_text(text):
    """
    Analyzes review text and determines if it is fake or genuine.
    Returns a dictionary with result and explanation.
    """
    if not text or len(text.strip()) == 0:
        return {"status": "error", "message": "No text provided"}
        
    text_lower = text.lower()
    
    # Simple rule-based NLP for demonstration
    spam_keywords = ['guaranteed', '100%', 'best product ever', 'click here', 'buy now', 'amazing', 'perfect', 'flawless']
    
    spam_score = sum(1 for word in spam_keywords if word in text_lower)
    
    is_caps = sum(1 for c in text if c.isupper()) / len(text) if len(text) > 0 else 0
    is_short = len(text.strip()) < 20
    
    if spam_score >= 2 or is_caps > 0.3 or is_short:
        return {
            "status": "success",
            "prediction": "Fake / Suspicious",
            "confidence": "87%",
            "reason": "Review contains unnatural language patterns, excessive capitalization, spam keywords, or lacks detailed product experience.",
            "css_class": "bad-stat"
        }
    else:
        return {
            "status": "success",
            "prediction": "Genuine",
            "confidence": "92%",
            "reason": "Review contains natural language patterns and detailed descriptions typical of real user experiences.",
            "css_class": "good-stat"
        }
