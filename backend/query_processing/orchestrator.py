# backend/query_processing/orchestrator.py
from backend.query_processing.spacy_processor import extract_entities_and_keywords
from backend.api_clients.aviationstack_api import get_live_flight_data, search_flights_by_route
from backend.query_processing.llm_layer import craft_flight_info_response, get_conversational_fallback, call_llm_for_rag # Import RAG LLM call
from backend.query_processing.rag import query_policy_rag # Import RAG function
from backend.DB.mockdb_utils import (
    get_flight_status_from_db, cancel_booking, create_booking,
    find_flights_by_route, find_available_seat, get_customer_by_id,
    get_seat_availability # <-- Import the new function
)
from backend.DB.database import SessionLocal
from backend.DB.models import Flight, Customer, Booking, Policy # Import Policy
from sqlalchemy.orm import joinedload
from typing import Dict, Any # For state typing
import re # Import re for seat parsing in cancellation
import traceback # Import traceback for detailed error logging

# in-memory conversation state (simple). For production, use redis or persistent store.
# Structure: { user_id: {"history": [], "awaiting_X": bool, "details": {...}} }
conversation_state: Dict[str, Dict[str, Any]] = {}

def process_user_query(user_id: str, query: str) -> str:
    """Processes user query, manages state, and returns response."""
    q = query.strip()
    # Get or initialize state for the user, ensuring history key exists
    state = conversation_state.get(user_id, {"history": []})
    # Ensure history is always a list, even if state was malformed
    if not isinstance(state.get("history"), list):
        state["history"] = []
    state["history"].append(f"USER: {q}") # Append current query

    response = "" # Initialize response

    # --- State Machine Logic ---
    try:
        # --- State: Awaiting PNR for cancellation ---
        if state.get("awaiting_pnr"):
            pnr = q.upper()
            session = SessionLocal()
            try:
                # Use joinedload to eagerly load the flight relationship
                bk = session.query(Booking).options(joinedload(Booking.flight)).filter(Booking.pnr == pnr).first()
                if not bk:
                    response = "I couldn't find that PNR in our system. Please check and send the PNR again."
                    # Don't reset state here, let them try again
                else:
                    flight_num_str = f"(Flight {bk.flight.flight_number})" if bk.flight else "(Flight info unavailable)"
                    customer_id_str = bk.customer_id
                    # Update state
                    state["awaiting_pnr"] = False
                    state["awaiting_cancel_confirmation"] = True
                    state["pnr"] = pnr
                    response = f"I found booking {pnr} for customer id {customer_id_str} {flight_num_str}. Do you want to cancel it? (yes/no)"
            finally:
                session.close() # Ensure session is closed

        # --- State: Awaiting Cancel Confirmation ---
        elif state.get("awaiting_cancel_confirmation"):
            ans = q.lower()
            pnr = state.get("pnr")
            if ans in ("yes", "y", "confirm") and pnr:
                response = cancel_booking(pnr) # Handles its own session
            else:
                response = "Okay — I will not cancel the booking."
            # Reset state fully after confirmation/denial, keeping history
            state = {"history": state.get("history", [])}

        # --- State: Awaiting Booking Source Airport ---
        elif state.get("awaiting_booking_source"):
            source_code = q.upper()
            # Basic validation for 3-letter IATA code
            if not (len(source_code) == 3 and source_code.isalpha()):
                response = "Please provide a valid 3-letter IATA code for the source airport (e.g., DEL)."
            else:
                state["awaiting_booking_source"] = False
                state["awaiting_booking_dest"] = True
                state["booking_details"] = {"source": source_code} # Initialize details
                response = f"Got it, flying from {source_code}. Where are you flying to? (e.g., BOM, BLR)"

        # --- State: Awaiting Booking Destination Airport ---
        elif state.get("awaiting_booking_dest"):
            dest_code = q.upper()
            if not (len(dest_code) == 3 and dest_code.isalpha()):
                response = "Please provide a valid 3-letter IATA code for the destination airport (e.g., BOM)."
            else:
                source_code = state.get("booking_details", {}).get("source", "N/A")
                state["booking_details"]["destination"] = dest_code
                flights = find_flights_by_route(source_code, dest_code) # DB Call
                if not flights:
                    response = f"I'm sorry, I couldn't find any available flights from {source_code} to {dest_code} in our mock booking system."
                    state = {"history": state.get("history", [])} # Reset
                else:
                    flight = flights[0] # Pick first available flight for demo
                    seat = find_available_seat(flight.flight_id) # DB Call
                    if not seat:
                        response = f"I found flight {flight.flight_number}, but unfortunately, it has no available seats."
                        state = {"history": state.get("history", [])} # Reset
                    else:
                        # Transition to confirmation state
                        state["awaiting_booking_dest"] = False
                        state["awaiting_booking_confirmation"] = True
                        # Store necessary details for booking
                        state["booking_details"]["flight_id"] = flight.flight_id
                        state["booking_details"]["assigned_seat"] = f"{seat.row_number}{seat.column_letter}"
                        state["booking_details"]["fare_amount"] = seat.price
                        response = (f"I found mock flight {flight.flight_number} from {flight.source_airport_code} to {flight.destination_airport_code} "
                                    f"with seat {state['booking_details']['assigned_seat']} priced at ₹{state['booking_details']['fare_amount']:.2f}. "
                                    "This is for demo booking. Would you like to confirm? (yes/no)")

        # --- State: Awaiting Booking Confirmation ---
        elif state.get("awaiting_booking_confirmation"):
            ans = q.lower()
            if ans in ("yes", "y", "confirm"):
                state["awaiting_booking_confirmation"] = False
                state["awaiting_booking_customer_id"] = True # Proceed to ask for customer ID
                response = "Great! Please provide your existing Customer ID to complete the booking. (e.g., 1, 2, 3)"
            else:
                response = "Okay, I've cancelled this booking request."
                state = {"history": state.get("history", [])} # Reset

        # --- State: Awaiting Customer ID for Booking ---
        elif state.get("awaiting_booking_customer_id"):
            try:
                cust_id = int(q)
                customer = get_customer_by_id(cust_id) # DB Call
                if not customer:
                    response = f"I couldn't find a customer with ID {cust_id}. Please provide a valid Customer ID (e.g., 1-5 from sample data)."
                    # Don't reset, let them try again
                else:
                    # Retrieve booking details and attempt to create booking
                    details = state.get("booking_details", {}) # Use .get for safety
                    # Ensure all details needed are present
                    if not all(k in details for k in ["flight_id", "assigned_seat", "fare_amount"]):
                         print(f"[Orchestrator] Error: Missing booking details in state for customer {cust_id}.")
                         response = "Sorry, something went wrong with the booking process. Please start again."
                         state = {"history": state.get("history", [])} # Reset
                    else:
                        try:
                            booking = create_booking( # DB Call
                                customer_id=cust_id,
                                flight_id=details["flight_id"],
                                assigned_seat=details["assigned_seat"],
                                fare_amount=details["fare_amount"]
                            )
                            response = f"Booking confirmed! Your PNR is {booking.pnr} for {customer.name}."
                        except ValueError as ve: # Catch specific booking errors (e.g., seat taken)
                             response = f"Booking failed: {ve}. Please try booking again."
                        except Exception as e: # Catch other potential errors during booking
                             print(f"[Orchestrator] Create Booking DB Error: {e}")
                             response = "Sorry, an unexpected error occurred while finalizing the booking."
                        # Reset state after booking attempt (success or failure)
                        state = {"history": state.get("history", [])}
            except ValueError:
                response = "Please provide a valid numeric Customer ID."


        # --- State: Awaiting Search Source Airport ---
        elif state.get("awaiting_search_source"):
            source_code = q.upper()
            if not (len(source_code) == 3 and source_code.isalpha()):
                response = "Please provide a valid 3-letter IATA code for the source airport (e.g., DEL)."
            else:
                state["awaiting_search_source"] = False
                state["awaiting_search_dest"] = True
                state["search_details"] = {"source": source_code} # Store source
                response = f"Got it, flying from {source_code}. Where are you flying to? (e.g., BOM, BLR)"

        # --- State: Awaiting Search Destination Airport ---
        elif state.get("awaiting_search_dest"):
            dest_code = q.upper()
            if not (len(dest_code) == 3 and dest_code.isalpha()):
                response = "Please provide a valid 3-letter IATA code for the destination airport (e.g., BOM)."
            else:
                source_code = state.get("search_details", {}).get("source", "N/A")
                # Important: Reset state BEFORE the API call
                state = {"history": state.get("history", [])}
                print(f"[Orchestrator] Calling API to search flights: {source_code} -> {dest_code}")
                flights_data = search_flights_by_route(source_code, dest_code) # API call
                if flights_data is None:
                    response = "Sorry, I encountered an error trying to search for flights using the live API. Please try again later."
                elif not flights_data:
                    response = f"Sorry, I couldn't find any live flights listed from {source_code} to {dest_code} for today in the API."
                else:
                    # Format the response with flight details
                    response_lines = [f"Okay, I found {len(flights_data)} live flight(s) from {source_code} to {dest_code} for today via the API:"]
                    for flight in flights_data:
                        dep_time_full = flight.get('departure_scheduled', 'N/A')
                        arr_time_full = flight.get('arrival_scheduled', 'N/A')
                        # Safely extract HH:MM part
                        dep_time = dep_time_full.split('T')[-1].split('+')[0][:5] if isinstance(dep_time_full, str) and 'T' in dep_time_full else 'N/A'
                        arr_time = arr_time_full.split('T')[-1].split('+')[0][:5] if isinstance(arr_time_full, str) and 'T' in arr_time_full else 'N/A'
                        fn = flight.get('flight_number', 'N/A')
                        airline = flight.get('airline', 'Unknown Airline')
                        status = flight.get('status', 'Unknown')
                        response_lines.append(f"• {fn} ({airline}): Departs: {dep_time}, Arrives: {arr_time} (Status: {status})")
                    response = "\n".join(response_lines)


        # --- No Active State: Process New Query ---
        else:
            ents = extract_entities_and_keywords(q)
            intent_hint = ents.get("intent_hint")
            flight_number = ents.get("flight_number") # Extract once for reuse

            # --- Intent: Check Seat Availability ---
            if intent_hint == "check_seat_availability":
                fn_seat_check = flight_number # Use specific variable name
                if not fn_seat_check:
                     # If intent is clear but no flight number, ask for it
                     response = "Which flight are you asking about? Please provide the flight number to check seat availability (e.g., AI202)."
                     # Potential future enhancement: set state awaiting_flight_for_seat_check
                else:
                    print(f"[Orchestrator] Checking seat availability for {fn_seat_check}")
                    available, total, err_msg = get_seat_availability(fn_seat_check) # DB Call
                    if err_msg:
                        response = err_msg # Pass DB error message directly
                    elif available is not None and total is not None:
                        # Provide more conversational responses based on availability
                        if total == 0:
                            response = f"It seems flight {fn_seat_check} doesn't have any seats listed in our system."
                        elif available == 0:
                            response = f"Flight {fn_seat_check} currently has no available seats listed in our mock database ({total} total seats)."
                        elif available == 1:
                            response = f"Flight {fn_seat_check} currently has only 1 available seat out of {total} total seats listed in our mock database."
                        else:
                            response = f"Flight {fn_seat_check} currently has {available} available seats out of {total} total seats listed in our mock database."
                    else: # Fallback safeguard
                        print(f"[Orchestrator] Seat availability check returned None without error for {fn_seat_check}")
                        response = "Sorry, I couldn't retrieve the seat availability information right now."

            # --- Intent: Flight Status ---
            elif intent_hint == "api_flight_info":
                fn_status = flight_number # Use specific variable name
                if not fn_status:
                    # Attempt reconstruction if parts are available
                    airline_code = ents.get("airline_code")
                    flight_digits = ents.get("flight_digits")
                    if airline_code and flight_digits:
                         fn_status = f"{airline_code}{flight_digits}"
                         print(f"[Orchestrator] Reconstructed flight number for status: {fn_status}")
                    else:
                         # Ask for flight number if intent is status but number is missing
                         response = "To check the flight status, please provide the flight number including the airline code (e.g., AI202, EK510, UA123)."

                # Proceed only if we definitely have a flight number now
                if fn_status:
                    live = get_live_flight_data(fn_status) # API call
                    if live:
                        # Use LLM to craft response from live data
                        response = craft_flight_info_response(live, q)
                    else:
                        # Fallback to DB if live API fails
                        print(f"[Orchestrator] Live data failed or not found for {fn_status}. Checking mock DB.")
                        db_status = get_flight_status_from_db(fn_status) # DB call
                        if db_status:
                            # Create fallback data dict and use LLM layer's template/LLM
                            fallback = {"flight_number": fn_status, "airline": "Airline (from Internal DB)", "status": db_status}
                            response = craft_flight_info_response(fallback, q)
                        else:
                            # If neither API nor DB has info
                            response = "I couldn't find any information for that flight in the live API data or our internal records."

            # --- Intent: Search Flights by Route (Start/Direct) ---
            elif intent_hint == "search_flights_by_route":
                locations = ents.get("locations", [])
                # Check if source/destination already extracted
                if len(locations) >= 2:
                     # Attempt to identify source and destination more reliably
                     source_code = None
                     dest_code = None
                     # Basic logic: look for "from X to Y" pattern
                     match = re.search(r"from\s+([A-Z]{3})\s+to\s+([A-Z]{3})", q, re.IGNORECASE)
                     if match:
                          source_code, dest_code = match.group(1).upper(), match.group(2).upper()
                     elif len(locations) == 2: # Otherwise, assume first is source, second is dest
                          source_code, dest_code = locations[0], locations[1] # Already uppercase from spacy_processor

                     if source_code and dest_code:
                         # Reset state before API call (no longer in conversation)
                         state = {"history": state.get("history", [])}
                         print(f"[Orchestrator] Calling API to search flights directly: {source_code} -> {dest_code}")
                         # --- [Code Block for Direct Search API Call - Duplicates Conversation] ---
                         flights_data = search_flights_by_route(source_code, dest_code) # API call
                         if flights_data is None:
                             response = "Sorry, I encountered an error trying to search for flights using the live API. Please try again later."
                         elif not flights_data:
                             response = f"Sorry, I couldn't find any live flights listed from {source_code} to {dest_code} for today in the API."
                         else:
                             response_lines = [f"Okay, I found {len(flights_data)} live flight(s) from {source_code} to {dest_code} for today via the API:"]
                             for flight in flights_data:
                                 dep_time_full = flight.get('departure_scheduled', 'N/A')
                                 arr_time_full = flight.get('arrival_scheduled', 'N/A')
                                 dep_time = dep_time_full.split('T')[-1].split('+')[0][:5] if isinstance(dep_time_full, str) and 'T' in dep_time_full else 'N/A'
                                 arr_time = arr_time_full.split('T')[-1].split('+')[0][:5] if isinstance(arr_time_full, str) and 'T' in arr_time_full else 'N/A'
                                 fn = flight.get('flight_number', 'N/A')
                                 airline = flight.get('airline', 'Unknown Airline')
                                 status = flight.get('status', 'Unknown')
                                 response_lines.append(f"• {fn} ({airline}): Departs: {dep_time}, Arrives: {arr_time} (Status: {status})")
                             response = "\n".join(response_lines)
                         # --- [End Code Block] ---
                     else: # If couldn't determine source/dest clearly from entities
                          state["awaiting_search_source"] = True
                          response = "It looks like you want to search flights. Where are you flying from? (Please provide the 3-letter IATA code, e.g., DEL)"
                elif len(locations) == 1:
                     # Only one location given, need the other - start conversation
                     state["awaiting_search_source"] = True # Assume they gave source or dest, ask for source first
                     response = f"Okay, you mentioned {locations[0]}. Are you flying from or to there? Let's start with where you are flying from? (e.g., DEL)"
                else:
                    # Start conversational search if no locations found yet
                    state["awaiting_search_source"] = True
                    response = "Sure, I can look up today's flights for you. Where are you flying from? (Please provide the 3-letter IATA code, e.g., DEL)"


            # --- Intent: Cancel Flow (Start) ---
            elif intent_hint == "cancel_booking":
                state["awaiting_pnr"] = True # Set state to await PNR
                response = "Sure — please share the PNR of the booking you want to cancel."

            # --- Intent: Booking Flow (Start) ---
            elif intent_hint == "create_booking":
                state["awaiting_booking_source"] = True # Set state to await source airport
                state["booking_details"] = {} # Initialize details
                response = "Okay, I can help with a mock booking using our internal data. Where are you flying from? (e.g., DEL, BOM, BLR)"

            # --- Intent: RAG/Policy Queries ---
            elif intent_hint == "rag_policy":
                policy_type = "Unknown"
                airline_code = "AI" # Default airline
                try: # Add try block for robustness
                    keywords = ents.get("keywords", [])
                    # Determine policy type from keywords more specifically
                    if "baggage" in keywords: policy_type = "Baggage"
                    elif "pet" in keywords or "animal" in keywords: policy_type = "Pet Travel" # Match Policy type name
                    elif "refund" in keywords: policy_type = "Refund"
                    elif "check-in" in keywords or "check in" in q.lower(): policy_type = "Check-in"
                    elif "cancel" in keywords: policy_type = "Cancellation" # Cancellation policy specific

                    # Try to get airline code from flight number OR explicit mention
                    extracted_airline_code = ents.get("airline_code")
                    if extracted_airline_code:
                         airline_code = extracted_airline_code
                    else:
                         # Simple fallback - check common airline mentions if no flight number
                         q_lower = q.lower()
                         if "delta" in q_lower: airline_code = "DL"
                         elif "united" in q_lower: airline_code = "UA"
                         elif "emirates" in q_lower or "ek flight" in q_lower : airline_code = "EK" # Match "EK flight"
                         elif "air india" in q_lower: airline_code = "AI"
                         # Keep default 'AI' if none explicitly mentioned

                    print(f"[Orchestrator] RAG Query - Type: {policy_type}, Airline: {airline_code}")
                    # --- ADDED TRY/EXCEPT AROUND RAG CALL ---
                    try:
                        response = query_policy_rag(q, policy_type=policy_type, airline_code=airline_code)
                    except Exception as rag_err:
                        print(f"[Orchestrator] Error during RAG call for '{q}': {rag_err}")
                        traceback.print_exc() # Print full RAG traceback
                        response = "Sorry, I had trouble retrieving or processing the policy information right now."
                    # --- END ADDED TRY/EXCEPT ---

                except Exception as policy_logic_err:
                    # Catch errors in determining policy type or airline code
                    print(f"[Orchestrator] Error determining policy type/airline for RAG: {policy_logic_err}")
                    traceback.print_exc()
                    response = "Sorry, I couldn't quite understand which policy or airline you're asking about. Can you please specify?"


            # --- Fallback: Conversational LLM ---
            else: # intent_hint == "unknown" or missed cases
                print(f"[Orchestrator] No specific intent matched for query: '{q}'. Using conversational fallback.")
                response = get_conversational_fallback(q) # LLM call

        # Update the master state dictionary (outside the `else` for initial queries)
        # This ensures state changes from within the `if/elif` blocks are saved
        conversation_state[user_id] = state

    # --- MAIN EXCEPTION HANDLER ---
    except Exception as e:
        print(f"[Orchestrator] !!! UNHANDLED EXCEPTION in main loop for user {user_id}, query '{q}' !!!: {e}")
        # Log the full traceback for critical debugging
        traceback.print_exc()
        # Reset state safely to avoid getting stuck, preserving history
        current_history = state.get("history", []) # Get history before reset
        conversation_state[user_id] = {"history": current_history} # Reset state, keep history
        # Provide the generic error message to the user
        response = "Sorry, I encountered an unexpected problem processing your request. Please try rephrasing or starting over."

    # --- Final Response Handling ---
    # Ensure response is not empty before proceeding
    if not response:
         print(f"[Orchestrator] WARNING: Reached end of processing with empty response for query: '{q}'. Using fallback.")
         # Attempt fallback if main logic yielded nothing
         try:
             response = get_conversational_fallback(q)
         except Exception as llm_fallback_err:
             print(f"[Orchestrator] Error during final LLM fallback: {llm_fallback_err}")
             response = "I'm having trouble processing that request right now." # Absolute fallback

    # Append bot response to history AFTER processing and potential errors
    # Get the potentially updated/reset state
    final_state = conversation_state.get(user_id, {"history": []})
     # Ensure history is a list before appending
    if not isinstance(final_state.get("history"), list):
        final_state["history"] = []
    final_state["history"].append(f"BOT: {response}")

    # Trim history if it exceeds a certain length (e.g., keep last 10 turns)
    MAX_HISTORY = 10
    if len(final_state["history"]) > MAX_HISTORY:
        final_state["history"] = final_state["history"][-MAX_HISTORY:]

    conversation_state[user_id] = final_state # Save the final state with updated history

    print(f"[Orchestrator] Final Response for '{q}': {response[:100]}...") # Log truncated response
    return response

