from backend.crud.booking_crud import get_booking_by_pnr, cancel_booking, get_bookings_by_customer, update_booking_seat
from sqlalchemy.orm import Session

# Cancel trip
def handle_cancel_trip(db: Session, pnr: str):
    booking = get_booking_by_pnr(db, pnr)
    if not booking:
        return {"error": "PNR not found"}
    if booking.booking_status == "Cancelled":
        return {"message": "Booking already cancelled"}
    cancel_booking(db, pnr)
    return {
        "status": "success",
        "message": f"Booking cancelled successfully",
        "booking_info": {
            "PNR": booking.pnr,
            "Refund Amount": f"₹{booking.refund_amount}"
        }
    }

# View booking details
def handle_view_booking(db: Session, pnr: str):
    booking = get_booking_by_pnr(db, pnr)
    if not booking:
        return {"error": f"PNR {pnr} not found"}
    return {
        "status": "success",
        "message": "Booking details retrieved",
        "booking_info": {
            "PNR": booking.pnr,
            "Customer ID": booking.customer_id,
            "Flight ID": booking.flight_id,
            "Seat": booking.assigned_seat,
            "Fare": f"₹{booking.fare_amount}",
            "Booking Status": booking.booking_status
        }
    }


# Get bookings by customer
def handle_bookings_by_customer(db: Session, customer_id: int):
    bookings = get_bookings_by_customer(db, customer_id)
    if not bookings:
        return {"message": f"No bookings found for Customer ID {customer_id}"}
    result = []
    for b in bookings:
        result.append({
            "PNR": b.pnr,
            "Flight ID": b.flight_id,
            "Seat": b.assigned_seat,
            "Status": b.booking_status
        })
    return {"status": "success", "bookings": result}

# Update seat
def handle_update_seat(db: Session, pnr: str, new_seat: str):
    booking = update_booking_seat(db, pnr, new_seat)
    if not booking:
        return {"error": f"PNR {pnr} not found"}
    return {
        "status": "success",
        "message": f"Seat updated successfully to {new_seat}",
        "booking_info": {
            "PNR": booking.pnr,
            "New Seat": booking.assigned_seat
        }
    }

