from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.services.flight_service import handle_flight_status, handle_seat_availability, handle_flight_details

flight_router = APIRouter()

# Flight Status
@flight_router.get("/flights/{flight_id}/status")
def flight_status_endpoint(flight_id: int, db: Session = Depends(get_db)):
    return handle_flight_status(db, flight_id)

# Flight Details by number
@flight_router.get("/flights/number/{flight_number}")
def flight_details_endpoint(flight_number: str, db: Session = Depends(get_db)):
    return handle_flight_details(db, flight_number)

# Seat Availability
@flight_router.get("/flights/{flight_id}/seats")
def seat_availability_endpoint(flight_id: int, db: Session = Depends(get_db)):
    return handle_seat_availability(db, flight_id)
