from backend.crud.flight_crud import get_flight_by_id, get_flight_by_number, get_seats_by_flight
from sqlalchemy.orm import Session

# Get flight status
def handle_flight_status(db: Session, flight_id: int):
    flight = get_flight_by_id(db, flight_id)
    if not flight:
        return {"error": f"Flight ID {flight_id} not found"}
    
    return {
        "status": "success",
        "message": f"Flight status retrieved successfully",
        "flight_info": {
            "Flight Number": flight.flight_number,
            "Source": flight.source_airport_code,
            "Destination": flight.destination_airport_code,
            "Scheduled Departure": str(flight.scheduled_departure),
            "Scheduled Arrival": str(flight.scheduled_arrival),
            "Current Status": flight.current_status
        }
    }

# Get flight details by number (optional)
def handle_flight_details(db: Session, flight_number: str):
    flight = get_flight_by_number(db, flight_number)
    if not flight:
        return {"error": f"Flight {flight_number} not found"}
    
    return {
        "status": "success",
        "flight_info": {
            "Flight Number": flight.flight_number,
            "Source": flight.source_airport_code,
            "Destination": flight.destination_airport_code,
            "Scheduled Departure": str(flight.scheduled_departure),
            "Scheduled Arrival": str(flight.scheduled_arrival),
            "Current Status": flight.current_status
        }
    }

# Get seat availability
def handle_seat_availability(db: Session, flight_id: int):
    seats = get_seats_by_flight(db, flight_id)
    if not seats:
        return {"error": f"No seats found for Flight ID {flight_id}"}
    
    seat_list = []
    for seat in seats:
        seat_list.append({
            "Row": seat.row_number,
            "Column": seat.column_letter,
            "Class": seat.seat_class,
            "Price": f"₹{seat.price}",
            "Booked": seat.is_booked
        })
    
    return {
        "status": "success",
        "flight_id": flight_id,
        "available_seats": seat_list
    }
