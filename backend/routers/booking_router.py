from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.services.booking_service import handle_cancel_trip, handle_bookings_by_customer, handle_update_seat, handle_view_booking

booking_router = APIRouter()

# Cancel booking
@booking_router.post("/bookings/cancel/{pnr}")
def cancel_booking_endpoint(pnr: str, db: Session = Depends(get_db)):
    return handle_cancel_trip(db, pnr)

# View booking details
@booking_router.get("/bookings/{pnr}")
def view_booking_endpoint(pnr: str, db: Session = Depends(get_db)):
    return handle_view_booking(db, pnr)

# Get bookings by customer
@booking_router.get("/bookings/customer/{customer_id}")
def bookings_by_customer_endpoint(customer_id: int, db: Session = Depends(get_db)):
    return handle_bookings_by_customer(db, customer_id)

# Update seat
@booking_router.put("/bookings/{pnr}/seat/{new_seat}")
def update_seat_endpoint(pnr: str, new_seat: str, db: Session = Depends(get_db)):
    return handle_update_seat(db, pnr, new_seat)

