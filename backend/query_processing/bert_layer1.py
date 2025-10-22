from transformers import pipeline

classifier = pipeline("text-classification", model="distilbert-base-uncased")

def classify_domain(query: str):
    """
    Returns 'airline' or 'generic' based on domain classification.
    """
    # In practice, you'd fine-tune this
    keywords = ["flight", "ticket", "airline", "cancel", "refund", "baggage"]
    if any(k in query.lower() for k in keywords):
        return "airline"
    return "generic"
