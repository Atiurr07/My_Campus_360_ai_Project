def summarize_transcript(text):
    # naive extractive summarizer: take top N sentences (placeholder)
    sentences = [s.strip() for s in text.split('.') if s.strip()]
    if not sentences:
        return ""
    summary = '. '.join(sentences[:3])
    return summary

def analyze_sentiment(text):
    # very simple sentiment heuristic
    low = text.lower()
    if any(w in low for w in ["good","great","happy","excellent","love"]):
        return "positive"
    if any(w in low for w in ["bad","sad","angry","upset","hate"]):
        return "negative"
    return "neutral"
