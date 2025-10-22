# backend/nlp_pipeline/intent_classifier.py
from transformers import pipeline

class IntentClassifier:
    def __init__(self):
        self.classifier = pipeline("text-classification", model="distilbert-base-uncased")
        self.intents = ["flight_status", "baggage_policy", "refund_policy", "booking_details", "cancellation"]

    def predict(self, text: str) -> str:
        # Simplified logic - replace with trained classifier
        text_lower = text.lower()
        if "status" in text_lower:
            return "flight_status"
        if "baggage" in text_lower:
            return "baggage_policy"
        if "refund" in text_lower:
            return "refund_policy"
        if "cancel" in text_lower:
            return "cancellation"
        return "booking_details"
