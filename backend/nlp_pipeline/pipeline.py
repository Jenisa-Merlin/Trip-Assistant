# backend/nlp_pipeline/pipeline.py
from .domain_classifier import DomainClassifier
from .intent_classifier import IntentClassifier
from .entity_extractor import EntityExtractor
from .llm_response import LLMResponder
from backend.database import SessionLocal
from backend.models import Flight, Policy

class QueryProcessor:
    def __init__(self):
        self.domain_model = DomainClassifier()
        self.intent_model = IntentClassifier()
        self.entity_model = EntityExtractor()
        self.llm = LLMResponder()

    def process(self, query: str):
        domain = self.domain_model.predict(query)
        if domain != "airline":
            return {"response": "Sorry, I can only help with airline-related questions."}

        intent = self.intent_model.predict(query)
        entities = self.entity_model.extract(query)

        db = SessionLocal()
        db_result = {}

        if intent == "flight_status" and "flight_number" in entities:
            db_result = db.query(Flight).filter(Flight.flight_number == entities["flight_number"]).first()
        elif "policy" in intent:
            db_result = db.query(Policy).filter(Policy.policy_type.ilike(f"%{intent.split('_')[0]}%")).first()

        db.close()

        response = self.llm.generate(intent, entities, db_result.__dict__ if db_result else {})
        return {"intent": intent, "entities": entities, "response": response}
