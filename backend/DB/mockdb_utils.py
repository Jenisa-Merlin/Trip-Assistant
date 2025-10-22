# backend/DB/mockdb_utils.py
from backend.DB.database import SessionLocal
from backend.DB.models import Booking, Seat, Flight, Customer
from datetime import datetime
import random

def get_flight_status_from_db(flight_number: str):
    db = SessionLocal()
    try:
        f = db.query(Flight).filter(Flight.flight_number == flight_number).first()
        return f.current_status if f else None
    finally:
        db.close()

def cancel_booking(pnr: str):
    db = SessionLocal()
    try:
        booking = db.query(Booking).filter(Booking.pnr == pnr).first()
        if not booking:
            return f"No booking found for PNR {pnr}."

        if booking.booking_status and booking.booking_status.lower() == "cancelled":
            return f"Booking {pnr} is already cancelled."

        # Free seat if it exists
        if booking.assigned_seat:
            # find seat row+letter mapping in seats table for this flight
            seat = db.query(Seat).filter(
                Seat.flight_id == booking.flight_id,
                Seat.row_number == int(''.join(filter(str.isdigit, booking.assigned_seat))) if any(c.isdigit() for c in booking.assigned_seat) else None,
                Seat.column_letter == ''.join(filter(str.isalpha, booking.assigned_seat))
            ).first()
            if seat:
                seat.is_booked = False

        booking.booking_status = "Cancelled"
        booking.refund_amount = booking.fare_amount * 0.9  # apply 10% fee example
        booking.refund_date = datetime.utcnow()
        db.commit()
        return f"Booking with PNR {pnr} has been cancelled. Refund: {booking.refund_amount}."
    except Exception as e:
        db.rollback()
        print("cancel_booking error:", e)
        return "An error occurred while cancelling the booking."
    finally:
        db.close()

def create_booking(customer_id: int, flight_id: int, assigned_seat: str, fare_amount: float):
    db = SessionLocal()
    try:
        # ensure seat is available
        seat = db.query(Seat).filter(
            Seat.flight_id == flight_id,
            Seat.column_letter == ''.join(filter(str.isalpha, assigned_seat)),
            Seat.row_number == int(''.join(filter(str.isdigit, assigned_seat)))
        ).first()
        if seat and seat.is_booked:
            raise ValueError("Selected seat is already booked.")

        # create unique PNR
        pnr = "PNR" + str(random.randint(10000, 99999))
        new_booking = Booking(
            pnr=pnr,
            customer_id=customer_id,
            flight_id=flight_id,
            booking_date=datetime.utcnow(),
            assigned_seat=assigned_seat,
            fare_amount=fare_amount,
            payment_status="Paid",
            booking_status="Confirmed"
        )
        db.add(new_booking)

        # mark seat booked
        if seat:
            seat.is_booked = True

        db.commit()
        db.refresh(new_booking)
        return new_booking
    except Exception as e:
        db.rollback()
        print("create_booking error:", e)
        raise
    finally:
        db.close()
