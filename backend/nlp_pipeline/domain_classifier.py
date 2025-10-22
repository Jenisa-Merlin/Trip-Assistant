# backend/nlp_pipeline/domain_classifier.py
from transformers import pipeline

class DomainClassifier:
    def __init__(self):
        # Pretrained small model for demo (replace with fine-tuned one)
        self.classifier = pipeline("text-classification", model="distilbert-base-uncased")

        # Example domain labels
        self.labels = ["airline", "generic", "finance", "health"]

    def predict(self, text: str) -> str:
        result = self.classifier(text, truncation=True)[0]
        # Mock: if airline-related words appear, force domain
        if any(word in text.lower() for word in ["flight", "airline", "pnr", "baggage"]):
            return "airline"
        return result['label'].lower()
