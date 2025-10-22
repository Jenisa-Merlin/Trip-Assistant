# sample_data.py
from backend.DB.database import SessionLocal, engine
from backend.DB.models import Base, Customer, Flight, Booking, Seat, Policy
from datetime import datetime

# Create tables
Base.metadata.create_all(bind=engine)
db = SessionLocal()

# --------- Customers (5) ----------
if not db.query(Customer).first():
    customers = [
        Customer(name="Jeni Mathews", email="jeni@example.com", phone="+919876543210"),
        Customer(name="Arun Kumar", email="arun@example.com", phone="+919812345678"),
        Customer(name="Priya Singh", email="priya@example.com", phone="+919899887766"),
        Customer(name="Rahul Verma", email="rahul@example.com", phone="+919877665544"),
        Customer(name="Sneha Reddy", email="sneha@example.com", phone="+919988776655")
    ]
    db.add_all(customers)

# --------- Flights (5) ----------
if not db.query(Flight).first():
    flights = [
        Flight(
            airline_code="AI", flight_number="AI202", source_airport_code="DEL",
            destination_airport_code="BOM", scheduled_departure=datetime(2025,10,23,9,30),
            scheduled_arrival=datetime(2025,10,23,11,45), current_status="On Time"
        ),
        Flight(
            airline_code="AI", flight_number="AI305", source_airport_code="DEL",
            destination_airport_code="BLR", scheduled_departure=datetime(2025,10,24,14,0),
            scheduled_arrival=datetime(2025,10,24,16,15), current_status="Scheduled"
        ),
        Flight(
            airline_code="AI", flight_number="AI450", source_airport_code="BOM",
            destination_airport_code="DEL", scheduled_departure=datetime(2025,10,25,8,0),
            scheduled_arrival=datetime(2025,10,25,10,15), current_status="Delayed"
        ),
        Flight(
            airline_code="AI", flight_number="AI512", source_airport_code="BLR",
            destination_airport_code="DEL", scheduled_departure=datetime(2025,10,26,18,30),
            scheduled_arrival=datetime(2025,10,26,20,45), current_status="On Time"
        ),
        Flight(
            airline_code="AI", flight_number="AI601", source_airport_code="DEL",
            destination_airport_code="MAA", scheduled_departure=datetime(2025,10,27,7,15),
            scheduled_arrival=datetime(2025,10,27,9,30), current_status="Cancelled"
        )
    ]
    db.add_all(flights)

# --------- Bookings (5) ----------
if not db.query(Booking).first():
    bookings = [
        Booking(pnr="PNR12345", customer_id=1, flight_id=1, assigned_seat="12A", fare_amount=5500.0, payment_status="Paid", booking_status="Confirmed"),
        Booking(pnr="PNR67890", customer_id=2, flight_id=2, assigned_seat="10B", fare_amount=6200.0, payment_status="Paid", booking_status="Confirmed"),
        Booking(pnr="PNR54321", customer_id=3, flight_id=3, assigned_seat="14C", fare_amount=5000.0, payment_status="Paid", booking_status="Confirmed"),
        Booking(pnr="PNR98765", customer_id=4, flight_id=4, assigned_seat="5D", fare_amount=7000.0, payment_status="Paid", booking_status="Confirmed"),
        Booking(pnr="PNR11223", customer_id=5, flight_id=5, assigned_seat="7E", fare_amount=6800.0, payment_status="Paid", booking_status="Confirmed")
    ]
    db.add_all(bookings)

# --------- Seats (5 per flight) ----------
if not db.query(Seat).first():
    for flight_id in range(1,6):  # 5 flights
        for i in range(1,6):  # 5 seats per flight
            db.add(Seat(
                flight_id=flight_id,
                row_number=i,
                column_letter=chr(64+i),  # A, B, C, D, E
                seat_class="Economy",
                price=5000 + flight_id*100 + i*50,
                is_booked=(i==1)
            ))

# --------- Policies (5) ----------
if not db.query(Policy).first():
    policies = [
        Policy(policy_type="Pet Travel", airline_code="AI", policy_text="Pets under 7kg allowed in cabin."),
        Policy(policy_type="Cancellation", airline_code="AI", policy_text="Cancellations allowed up to 24h before departure with 10% charge."),
        Policy(policy_type="Baggage", airline_code="AI", policy_text="Max 15kg checked baggage, 7kg cabin baggage."),
        Policy(policy_type="Refund", airline_code="AI", policy_text="Refund processed within 7 business days."),
        Policy(policy_type="Check-in", airline_code="AI", policy_text="Online check-in opens 24h before departure.")
    ]
    db.add_all(policies)

# Commit and close
db.commit()
db.close()

print("Sample data loaded successfully with 5 records per table!")
