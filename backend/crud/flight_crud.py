from sqlalchemy.orm import Session
from backend.models import Flight, Seat

# Get flight by ID
def get_flight_by_id(db: Session, flight_id: int):
    return db.query(Flight).filter(Flight.flight_id == flight_id).first()

# Get flight by flight number
def get_flight_by_number(db: Session, flight_number: str):
    return db.query(Flight).filter(Flight.flight_number == flight_number).first()

# Get all flights (optional)
def get_all_flights(db: Session):
    return db.query(Flight).all()

# Get seat availability for a flight
def get_seats_by_flight(db: Session, flight_id: int):
    return db.query(Seat).filter(Seat.flight_id == flight_id).all()
