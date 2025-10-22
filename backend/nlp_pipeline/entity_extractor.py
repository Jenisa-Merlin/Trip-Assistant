# backend/nlp_pipeline/entity_extractor.py
import spacy

class EntityExtractor:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")

    def extract(self, text: str) -> dict:
        doc = self.nlp(text)
        entities = {}
        for ent in doc.ents:
            entities[ent.label_] = ent.text

        # Simple keyword extraction
        if "AI" in text:
            entities["airline_code"] = "AI"
        if any(x in text.upper() for x in ["PNR", "BOOKING"]):
            entities["pnr"] = text.split()[-1]
        return entities
