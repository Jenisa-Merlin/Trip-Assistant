# backend/DB/mockdb_utils.py
from backend.DB.database import SessionLocal
from backend.DB.models import Booking, Seat, Flight, Customer
from sqlalchemy.orm import joinedload
from sqlalchemy import func # Import func for count
from datetime import datetime
import random
import re # Import re for seat parsing
from typing import Tuple, Optional, List # For type hinting

# --- Flight Status ---
def get_flight_status_from_db(flight_number: str) -> Optional[str]:
    """Retrieves the current status of a flight from the mock DB."""
    db = SessionLocal()
    try:
        flight = db.query(Flight).filter(Flight.flight_number == flight_number.upper()).first()
        return flight.current_status if flight else None
    except Exception as e:
        print(f"[DB Utils] Error getting flight status for {flight_number}: {e}")
        return None
    finally:
        db.close()

# --- Cancellation ---
def cancel_booking(pnr: str) -> str:
    """Cancels a booking by PNR and marks the seat as available."""
    db = SessionLocal()
    try:
        # Query booking and eager load the related seat via flight relationship
        booking = db.query(Booking).options(
            joinedload(Booking.flight).joinedload(Flight.seats) # Load flight then seats
        ).filter(Booking.pnr == pnr.upper()).first()

        if not booking:
            return f"No booking found for PNR {pnr}."

        if booking.booking_status and booking.booking_status.lower() == "cancelled":
            return f"Booking {pnr} is already cancelled."

        # Find and free the specific assigned seat
        seat_to_free = None
        if booking.assigned_seat and booking.flight and booking.flight.seats:
            try:
                # Robust parsing of seat string (e.g., "12A", "3B")
                seat_match = re.match(r"(\d+)([A-Z])", booking.assigned_seat.upper())
                if seat_match:
                    seat_row = int(seat_match.group(1))
                    seat_col = seat_match.group(2)
                    for seat in booking.flight.seats:
                        if seat.row_number == seat_row and seat.column_letter == seat_col:
                            seat_to_free = seat
                            break
                else:
                     print(f"[DB Utils] Could not parse seat '{booking.assigned_seat}' for PNR {pnr}.")
            except ValueError:
                 print(f"[DB Utils] Invalid number in seat '{booking.assigned_seat}' for PNR {pnr}.")
            except Exception as e:
                 print(f"[DB Utils] Unexpected error parsing seat '{booking.assigned_seat}' for PNR {pnr}: {e}")


        if seat_to_free:
            if seat_to_free.is_booked:
                print(f"[DB Utils] Marking seat {seat_to_free.row_number}{seat_to_free.column_letter} on flight {booking.flight_id} as not booked.")
                seat_to_free.is_booked = False
            else:
                 print(f"[DB Utils] Seat {seat_to_free.row_number}{seat_to_free.column_letter} for PNR {pnr} was already marked as not booked.")
        else:
             print(f"[DB Utils] Warning: Could not find DB entry for seat '{booking.assigned_seat}' to free for PNR {pnr}.")

        # Update booking status and refund info
        booking.booking_status = "Cancelled"
        booking.refund_amount = (booking.fare_amount or 0.0) * 0.9  # apply 10% fee example
        booking.refund_date = datetime.utcnow()

        db.commit()
        return f"Booking with PNR {pnr} has been cancelled. Seat {booking.assigned_seat or ''} is now available. Refund initiated: ₹{booking.refund_amount:.2f}."

    except Exception as e:
        db.rollback()
        print(f"[DB Utils] cancel_booking error for PNR {pnr}: {e}")
        return "An error occurred while cancelling the booking."
    finally:
        db.close()


# --- Booking Creation ---
def create_booking(customer_id: int, flight_id: int, assigned_seat: str, fare_amount: float) -> Booking:
    """Creates a new booking and marks the seat as booked. Raises ValueError if seat is taken."""
    db = SessionLocal()
    try:
        # Find and check seat availability
        seat_match = re.match(r"(\d+)([A-Z])", assigned_seat.upper())
        if not seat_match:
            raise ValueError(f"Invalid seat format '{assigned_seat}'. Use format like '12A'.")

        seat_row = int(seat_match.group(1))
        seat_col = seat_match.group(2)

        seat = db.query(Seat).filter(
            Seat.flight_id == flight_id,
            Seat.row_number == seat_row,
            Seat.column_letter == seat_col
        ).with_for_update().first() # Lock the seat row during transaction

        if not seat:
            raise ValueError(f"Seat {assigned_seat} does not exist on this flight.")
        if seat.is_booked:
            raise ValueError(f"Sorry, seat {assigned_seat} is already booked.")

        # Create unique PNR (simple approach)
        pnr = "PNR" + str(random.randint(100000, 999999))
        while db.query(Booking).filter(Booking.pnr == pnr).first(): # Ensure PNR uniqueness
            pnr = "PNR" + str(random.randint(100000, 999999))

        new_booking = Booking(
            pnr=pnr,
            customer_id=customer_id,
            flight_id=flight_id,
            booking_date=datetime.utcnow(),
            assigned_seat=f"{seat.row_number}{seat.column_letter}", # Use confirmed seat format
            fare_amount=fare_amount, # Use provided fare (should match seat price)
            payment_status="Paid", # Assume payment succeeded for mock
            booking_status="Confirmed"
        )
        db.add(new_booking)

        # Mark seat as booked
        seat.is_booked = True
        print(f"[DB Utils] Marking seat {seat.row_number}{seat.column_letter} on flight {flight_id} as booked for PNR {pnr}.")

        db.commit()
        db.refresh(new_booking) # Refresh to get latest state
        return new_booking
    except ValueError as ve:
         db.rollback()
         print(f"[DB Utils] create_booking Value Error: {ve}")
         raise # Re-raise specific errors for orchestrator
    except Exception as e:
        db.rollback()
        print(f"[DB Utils] create_booking error: {e}")
        # Raise a more generic exception or handle differently
        raise Exception("An unexpected error occurred while creating the booking.") from e
    finally:
        db.close()

# --- Helper Functions for Booking ---
def find_flights_by_route(source_code: str, dest_code: str) -> List[Flight]:
    """Finds flights matching the source and destination in the mock DB."""
    db = SessionLocal()
    try:
        flights = db.query(Flight).filter(
            Flight.source_airport_code == source_code.upper(),
            Flight.destination_airport_code == dest_code.upper(),
            Flight.current_status.notin_(['Cancelled', 'Departed', 'Landed']) # Only show bookable flights
        ).order_by(Flight.scheduled_departure).all() # Order by departure time
        return flights
    except Exception as e:
        print(f"[DB Utils] Error finding flights for {source_code}->{dest_code}: {e}")
        return []
    finally:
        db.close()

def find_available_seat(flight_id: int) -> Optional[Seat]:
    """Finds the first available seat for a given flight ID."""
    db = SessionLocal()
    try:
        seat = db.query(Seat).filter(
            Seat.flight_id == flight_id,
            Seat.is_booked == False
        ).order_by(Seat.row_number, Seat.column_letter).first() # Get the 'first' available
        return seat
    except Exception as e:
        print(f"[DB Utils] Error finding available seat for flight {flight_id}: {e}")
        return None
    finally:
        db.close()

def get_customer_by_id(customer_id: int) -> Optional[Customer]:
    """Retrieves a customer by their ID."""
    db = SessionLocal()
    try:
        customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
        return customer
    except Exception as e:
        print(f"[DB Utils] Error getting customer {customer_id}: {e}")
        return None
    finally:
        db.close()

# --- NEW: Seat Availability Check ---
def get_seat_availability(flight_number: str) -> Tuple[Optional[int], Optional[int], Optional[str]]:
    """
    Checks the number of available seats for a given flight number in the mock DB.

    Returns:
        Tuple: (available_seats, total_seats, error_message | None)
        Returns (None, None, error_message) if flight not found or error occurs.
    """
    db = SessionLocal()
    try:
        # 1. Find the flight_id for the given flight_number
        flight = db.query(Flight.flight_id).filter(Flight.flight_number == flight_number.upper()).first()
        if not flight:
            print(f"[DB Utils] Flight {flight_number} not found for seat availability check.")
            return None, None, f"Sorry, I couldn't find flight {flight_number} in our records."

        flight_id = flight.flight_id
        print(f"[DB Utils] Checking seat availability for flight_id: {flight_id} (Number: {flight_number})")

        # 2. Count total seats for this flight_id
        total_seats = db.query(func.count(Seat.seat_id)).filter(Seat.flight_id == flight_id).scalar()
        total_seats = total_seats if total_seats is not None else 0 # Handle case where count returns None
        print(f"[DB Utils] Total seats found: {total_seats}")


        # 3. Count available seats (is_booked == False) for this flight_id
        available_seats = db.query(func.count(Seat.seat_id)).filter(
            Seat.flight_id == flight_id,
            Seat.is_booked == False # In SQL, False is often represented as 0
        ).scalar()
        available_seats = available_seats if available_seats is not None else 0 # Handle case where count returns None
        print(f"[DB Utils] Available seats found: {available_seats}")


        return available_seats, total_seats, None # Success, no error message

    except Exception as e:
        print(f"[DB Utils] Error getting seat availability for {flight_number}: {e}")
        return None, None, "Sorry, an error occurred while checking seat availability."
    finally:
        db.close()
        print(f"[DB Utils] Session closed for seat availability check.")

