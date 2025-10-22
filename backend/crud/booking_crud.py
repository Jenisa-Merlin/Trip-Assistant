from sqlalchemy.orm import Session
from backend.models import Booking

# Get booking by PNR
def get_booking_by_pnr(db: Session, pnr: str):
    return db.query(Booking).filter(Booking.pnr == pnr).first()

# Cancel a booking
def cancel_booking(db: Session, pnr: str):
    booking = get_booking_by_pnr(db, pnr)
    if booking:
        booking.booking_status = "Cancelled"
        booking.refund_amount = booking.fare_amount * 0.9
        db.commit()
    return booking

# Get bookings by customer
def get_bookings_by_customer(db: Session, customer_id: int):
    return db.query(Booking).filter(Booking.customer_id == customer_id).all()

# Update booking seat
def update_booking_seat(db: Session, pnr: str, new_seat: str):
    booking = get_booking_by_pnr(db, pnr)
    if booking:
        booking.assigned_seat = new_seat
        db.commit()
    return booking