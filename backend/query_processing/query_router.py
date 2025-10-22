from backend.api_clients.aviationstack_api import get_live_flight_data
from backend.DB.database import SessionLocal
from backend.DB.models import Flight, Policy

def handle_query(intent, entities):
    if intent == "mockdb":
        db = SessionLocal()
        flight_number = entities.get("flight_number")
        flight = db.query(Flight).filter(Flight.flight_number == flight_number).first()
        db.close()
        if flight:
            return {"source": "mockdb", "status": flight.current_status}
        return {"source": "mockdb", "status": "not found"}

    elif intent == "api":
        flight_number = entities.get("flight_number")
        # Note: Your aviationstack_api.py has get_live_flight_data, not get_flight_status
        result = get_live_flight_data(flight_number) 
        return {"source": "api", "data": result}

    elif intent == "rag":
        db = SessionLocal()
        policy = db.query(Policy).first()  # Simplified RAG
        db.close()
        return {"source": "rag", "data": policy.policy_text if policy else "No policy found."}

    return {"source": "unknown"}
