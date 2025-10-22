# backend/query_processing/orchestrator.py
from backend.query_processing.spacy_processor import extract_entities_and_keywords
from backend.api_clients.aviationstack_api import get_live_flight_data
from backend.query_processing.llm_layer import craft_flight_info_response
from backend.DB.mockdb_utils import get_flight_status_from_db, cancel_booking, create_booking
from backend.DB.database import SessionLocal
from backend.DB.models import Flight, Customer

# in-memory conversation state (simple). For production, use redis or persistent store.
conversation_state: dict = {}

def process_user_query(user_id: str, query: str):
    q = query.strip()
    state = conversation_state.get(user_id, {})

    # --- Follow-up: awaiting PNR for cancel ---
    if state.get("awaiting_pnr"):
        pnr = q.upper()
        # check booking exists
        db = SessionLocal()
        booking = db.query(Flight).filter(Flight.flight_number == pnr).first()  # this is wrong usage; we check booking below
        db.close()
        # Use mockdb cancel flow: orchestrator expects pnr -> confirm -> cancel
        session = SessionLocal()
        from backend.DB.models import Booking
        bk = session.query(Booking).filter(Booking.pnr == pnr).first()
        session.close()
        if not bk:
            conversation_state[user_id] = {}
            return "I couldn't find that PNR in our system. Please check and send the PNR again."

        conversation_state[user_id] = {"awaiting_cancel_confirmation": True, "pnr": pnr}
        return f"I found booking {pnr} for customer id {bk.customer_id}. Do you want to cancel it? (yes/no)"

    # --- Follow-up: awaiting cancel confirmation ---
    if state.get("awaiting_cancel_confirmation"):
        ans = q.lower()
        if ans in ("yes", "y", "confirm"):
            pnr = state["pnr"]
            res = cancel_booking(pnr)
            conversation_state[user_id] = {}
            return res
        else:
            conversation_state[user_id] = {}
            return "Okay — I will not cancel the booking."

    # --- Follow-up: awaiting booking confirmation ---
    if state.get("awaiting_booking_confirmation"):
        ans = q.lower()
        if ans in ("yes", "y", "confirm"):
            details = state["booking_details"]
            try:
                booking = create_booking(**details)
                conversation_state[user_id] = {}
                return f"Booking confirmed! Your PNR is {booking.pnr}."
            except Exception as e:
                conversation_state[user_id] = {}
                return f"Failed to create booking: {e}"
        else:
            conversation_state[user_id] = {}
            return "Okay — booking cancelled."

    # --- New query handling ---
    ents = extract_entities_and_keywords(q)

    # If flight info type (api_flight_info)
    if ents.get("intent_hint") == "api_flight_info" or ("flight" in q.lower() and "status" in q.lower()):
        fn = ents.get("flight_number")
        if not fn:
            return "Please provide a flight number (e.g., AI202 or UA2402)."

        # 1) call live API
        live = get_live_flight_data(fn)
        if live:
            return craft_flight_info_response(live, q)

        # 2) fallback to mock DB
        db_status = get_flight_status_from_db(fn)
        if db_status:
            # craft a small reply using available data
            fallback = {"flight_number": fn, "airline": None, "status": db_status}
            return craft_flight_info_response(fallback, q)
        return "I couldn't find any information for that flight in live data or our records."

    # Cancel flow
    if "cancel" in q.lower() and "ticket" in q.lower():
        conversation_state[user_id] = {"awaiting_pnr": True}
        return "Sure — please share the PNR of the booking you want to cancel."

    # Booking flow (simple)
    if "book" in q.lower() and "flight" in q.lower():
        # pick first available flight & customer for demo; in real flow, ask specifics
        db = SessionLocal()
        flight = db.query(Flight).filter(Flight.current_status != "Cancelled").first()
        customer = db.query(Customer).first()
        db.close()
        if not flight or not customer:
            return "Sorry — no flights or customers available in mock DB."

        # choose a first free seat for that flight
        session = SessionLocal()
        from backend.DB.models import Seat
        free_seat = session.query(Seat).filter(Seat.flight_id == flight.flight_id, Seat.is_booked == False).first()
        session.close()
        if not free_seat:
            return "No free seats available on that flight."

        booking_details = {
            "customer_id": customer.customer_id,
            "flight_id": flight.flight_id,
            "assigned_seat": f"{free_seat.row_number}{free_seat.column_letter}",
            "fare_amount": free_seat.price
        }
        conversation_state[user_id] = {"awaiting_booking_confirmation": True, "booking_details": booking_details}

        return (f"I found flight {flight.flight_number} from {flight.source_airport_code} to {flight.destination_airport_code} "
                f"with seat {booking_details['assigned_seat']} priced ₹{booking_details['fare_amount']}. Confirm booking? (yes/no)")

    # RAG/policy queries (simple lookup)
    if any(k in q.lower() for k in ("policy", "baggage", "refund", "check-in", "pet")):
        # look up policy table (first match)
        session = SessionLocal()
        from backend.DB.models import Policy
        keyword = None
        for k in ("baggage", "refund", "cancellation", "pet", "check"):
            if k in q.lower():
                keyword = k
                break
        policy = None
        if keyword:
            policy = session.query(Policy).filter(Policy.policy_type.ilike(f"%{keyword}%")).first()
        if not policy:
            policy = session.query(Policy).first()
        session.close()
        if policy:
            return f"Policy ({policy.policy_type}): {policy.policy_text}"
        return "I couldn't find a matching policy right now."

    # Fallback - generic
    return "Sorry — I didn't understand that. Try asking about flight status, booking, or cancellation."
