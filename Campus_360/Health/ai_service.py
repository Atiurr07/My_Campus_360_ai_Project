def mental_health_response(user_text):
    """
    Very basic rule-based responses — replace with sentiment/classifier later.
    """

    txt = user_text.lower()
    if any(w in txt for w in ["sad", "depressed", "unhappy", "lonely"]):
        return "I'm sorry you're feeling low. Try talking to someone you trust. Would you like breathing exercises?"
    if any(w in txt for w in ["anxious", "nervous", "stressed"]):
        return "Take a deep breath. Try a 5-minute breathing exercise. Would you like guidance?"
    return "Thanks for sharing. Tell me more or say 'help' if you want suggestions."

def symptom_checker(symptoms_text):
    # simple keyword mapping::
    text = symptoms_text.lower()
    points = []
    if "fever" in text:
        points.append("Possible infection - monitor temperature.")
    if "headache" in text:
        points.append("Hydrate and rest; consult if severe.")
    if not points:
        points.append("Symptoms unclear; consider consulting clinic.")
    return {"recommendations": points}
