# sample_data.py
from DB.database import SessionLocal, engine
from DB.models import Base, Customer, Flight, Booking, Seat, Policy
from sqlalchemy import text # Import text for raw SQL execution
from datetime import datetime

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)
db = SessionLocal()

# --------- Clear Existing Data (Optional but recommended for consistency) --------
# Use this section carefully, it deletes data!
# Comment out if you want to keep existing data and just add more.
print("Clearing existing data (Customers, Flights, Bookings, Seats, Policies)...")
try:
    # Use raw SQL with CASCADE if your DB supports it and FKs are set up correctly
    # For SQLite, FK constraints need to be enabled per-connection,
    # so deleting in dependency order is safer.
    db.execute(text("DELETE FROM bookings;"))
    db.execute(text("DELETE FROM seats;"))
    db.execute(text("DELETE FROM flights;"))
    db.execute(text("DELETE FROM policies;"))
    db.execute(text("DELETE FROM customers;"))
    # Reset sequences for primary keys if using PostgreSQL or similar
    # db.execute(text("ALTER SEQUENCE customers_customer_id_seq RESTART WITH 1;"))
    # db.execute(text("ALTER SEQUENCE flights_flight_id_seq RESTART WITH 1;"))
    # db.execute(text("ALTER SEQUENCE seats_seat_id_seq RESTART WITH 1;"))
    # db.execute(text("ALTER SEQUENCE policies_policy_id_seq RESTART WITH 1;"))
    db.commit()
    print("Existing data cleared.")
except Exception as e:
    db.rollback()
    print(f"Error clearing data: {e}. Proceeding without clearing.")


# --------- Customers (5) ----------
print("Adding Customers...")
# Check if customers table is empty before adding
if not db.query(Customer).first():
    customers = [
        Customer(name="Jeni Mathews", email="jeni@example.com", phone="+919876543210"),
        Customer(name="Arun Kumar", email="arun@example.com", phone="+919812345678"),
        Customer(name="Priya Singh", email="priya@example.com", phone="+919899887766"),
        Customer(name="Rahul Verma", email="rahul@example.com", phone="+919877665544"),
        Customer(name="Sneha Reddy", email="sneha@example.com", phone="+919988776655")
    ]
    db.add_all(customers)
    db.commit() # Commit after adding customers
    print(f"{len(customers)} Customers added.")
else:
    print("Customers already exist, skipping addition.")


# --------- Flights (5) ----------
print("Adding Flights...")
# Check if flights table is empty before adding
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
            airline_code="EK", flight_number="EK510", source_airport_code="DXB", # Added Emirates flight
            destination_airport_code="DEL", scheduled_departure=datetime(2025,10,26,18,30),
            scheduled_arrival=datetime(2025,10,26,20,45), current_status="On Time"
        ),
        Flight(
            airline_code="UA", flight_number="UA123", source_airport_code="LHR", # Added United flight
            destination_airport_code="EWR", scheduled_departure=datetime(2025,10,27,7,15),
            scheduled_arrival=datetime(2025,10,27,9,30), current_status="Scheduled"
        )
    ]
    db.add_all(flights)
    db.commit() # Commit after adding flights
    print(f"{len(flights)} Flights added.")

    # --------- Seats (Added dynamically based on flights just added) ----------
    print("Adding Seats...")
    flights_added = db.query(Flight).order_by(Flight.flight_id).all() # Get flights we just added
    all_seats = []
    seat_count = 0
    for flight in flights_added:
        # Check if seats for this flight already exist
        existing_seat = db.query(Seat).filter(Seat.flight_id == flight.flight_id).first()
        if not existing_seat:
            print(f"  Adding seats for Flight ID: {flight.flight_id} ({flight.flight_number})")
            for row in range(1, 6):  # 5 rows
                for col_idx, col_letter in enumerate(['A', 'B', 'C', 'D', 'E']): # 5 columns
                    # Make only the first seat (1A) booked for simplicity
                    is_booked_status = (row == 1 and col_letter == 'A')
                    seat_price = 5000 + flight.flight_id*100 + row*50 + col_idx*10 # Varied pricing
                    all_seats.append(Seat(
                        flight_id=flight.flight_id,
                        row_number=row,
                        column_letter=col_letter,
                        seat_class="Economy",
                        price=seat_price,
                        is_booked=is_booked_status
                    ))
                    seat_count += 1
        else:
             print(f"  Seats for Flight ID: {flight.flight_id} already exist, skipping.")

    if all_seats:
        db.add_all(all_seats)
        db.commit() # Commit after adding seats
        print(f"{seat_count} Seats added.")
    else:
        print("No new seats added.")


    # --------- Bookings (Link to existing Customers and Flights) ----------
    print("Adding Bookings...")
    # Check if bookings table is empty before adding
    if not db.query(Booking).first():
        # Get IDs of customers and flights we added (or assume they exist if skipping add steps)
        customer_ids = [c.customer_id for c in db.query(Customer.customer_id).order_by(Customer.customer_id).limit(5).all()]
        flight_ids = [f.flight_id for f in db.query(Flight.flight_id).order_by(Flight.flight_id).limit(5).all()]

        if len(customer_ids) >= 5 and len(flight_ids) >= 5:
            bookings = [
                Booking(pnr="PNR12345", customer_id=customer_ids[0], flight_id=flight_ids[0], assigned_seat="1A", fare_amount=5500.0, payment_status="Paid", booking_status="Confirmed"), # Seat 1A matches is_booked=True
                Booking(pnr="PNR67890", customer_id=customer_ids[1], flight_id=flight_ids[1], assigned_seat="2B", fare_amount=6200.0, payment_status="Paid", booking_status="Confirmed"), # Assumes 2B is available
                Booking(pnr="PNR54321", customer_id=customer_ids[2], flight_id=flight_ids[2], assigned_seat="3C", fare_amount=5000.0, payment_status="Paid", booking_status="Confirmed"),
                Booking(pnr="PNR98765", customer_id=customer_ids[3], flight_id=flight_ids[3], assigned_seat="4D", fare_amount=7000.0, payment_status="Paid", booking_status="Confirmed"),
                Booking(pnr="PNR11223", customer_id=customer_ids[4], flight_id=flight_ids[4], assigned_seat="5E", fare_amount=6800.0, payment_status="Paid", booking_status="Confirmed")
            ]
            try:
                db.add_all(bookings)
                db.commit() # Commit after adding bookings
                print(f"{len(bookings)} Bookings added.")
                # Now explicitly mark the booked seats (more robust than relying on initial seat creation)
                print("Marking booked seats...")
                seats_to_update = db.query(Seat).filter(
                    Seat.flight_id.in_([b.flight_id for b in bookings]),
                    Seat.row_number.in_([int(re.match(r"(\d+)", b.assigned_seat).group(1)) for b in bookings if re.match(r"(\d+)", b.assigned_seat)]),
                    Seat.column_letter.in_([re.match(r"\d+([A-Z])", b.assigned_seat).group(1) for b in bookings if re.match(r"\d+([A-Z])", b.assigned_seat)])
                ).all()

                updated_count = 0
                for seat in seats_to_update:
                     # Check if this specific seat corresponds to one of the bookings added
                     is_target_seat = any(
                          s_book.flight_id == seat.flight_id and
                          s_book.assigned_seat == f"{seat.row_number}{seat.column_letter}"
                          for s_book in bookings
                     )
                     if is_target_seat and not seat.is_booked:
                          seat.is_booked = True
                          updated_count += 1
                          print(f"  Marked seat {seat.row_number}{seat.column_letter} on flight {seat.flight_id} as booked.")

                if updated_count > 0:
                     db.commit()
                     print(f"{updated_count} seats marked as booked based on added bookings.")
                else:
                     print("No additional seats needed marking as booked.")


            except Exception as e:
                db.rollback()
                print(f"Error adding bookings or marking seats: {e}")
        else:
            print("Skipping bookings: Not enough customers or flights found/added.")
    else:
        print("Bookings already exist, skipping addition.")

else:
    print("Flights already exist, skipping addition of flights, seats, and bookings.")


# --------- Policies (Reverting to Hardcoded Samples for Multiple Airlines) ----------
# NOTE: This section now runs *every time* sample_data.py is executed
#       It will add these policies again if they already exist, leading to duplicates
#       unless you cleared the table first.
print("Adding hardcoded Policies (AI, DL, UA, EK)...")
policies = [
    # Air India (AI)
    Policy(policy_type="Pet Travel", airline_code="AI", policy_text="Air India: Small dogs and cats under 7kg allowed in cabin in approved carrier. Must be booked in advance. Check IATA and destination rules. Not allowed in exit rows.", source_url="mock_data"),
    Policy(policy_type="Cancellation", airline_code="AI", policy_text="Air India: Cancellations allowed up to 24h before departure with fee (e.g., 10%). Fees vary by fare type. Refunds processed within 7-10 business days.", source_url="mock_data"),
    Policy(policy_type="Baggage", airline_code="AI", policy_text="Air India: Economy standard: 1 checked bag up to 15kg (domestic) or 23kg (international, varies by route), 1 cabin bag up to 7kg. Dimensions apply.", source_url="mock_data"),
    Policy(policy_type="Refund", airline_code="AI", policy_text="Air India: Refunds for eligible cancellations processed to original payment method within 7-10 business days. Cancellation fees apply.", source_url="mock_data"),
    Policy(policy_type="Check-in", airline_code="AI", policy_text="Air India: Online check-in opens 48 hours before departure and closes 2 hours before departure. Airport check-in counters close 60 minutes prior.", source_url="mock_data"),

    # Delta (DL)
    Policy(policy_type="Pet Travel", airline_code="DL", policy_text="Delta: Small dogs, cats, household birds allowed in cabin (fee applies, space limited, book early). Carrier must fit under seat (18x11x11 inches recommended). Check international rules.", source_url="mock_data"),
    Policy(policy_type="Baggage", airline_code="DL", policy_text="Delta: Main Cabin (US Domestic): 1st checked bag $35, 2nd $45 (under 50lbs/23kg). Int'l varies (often 1 free). Carry-on: 1 bag + 1 personal item free.", source_url="mock_data"),
    Policy(policy_type="Cancellation", airline_code="DL", policy_text="Delta: Most tickets (except Basic Economy) can be cancelled for eCredit. Refundable tickets get refund. Check fare rules.", source_url="mock_data"),


    # United (UA)
    Policy(policy_type="Pet Travel", airline_code="UA", policy_text="United: Small dogs/cats in cabin (fee applies, space limited, book early). Carrier under seat. No pets in Polaris/First int'l. Check specific flight/destination rules.", source_url="mock_data"),
    Policy(policy_type="Baggage", airline_code="UA", policy_text="United: Economy (US Domestic): 1st checked bag ~$40, 2nd ~$50 (under 50lbs/23kg). Int'l varies. Carry-on: 1 bag + 1 personal item free (except Basic Economy on some routes).", source_url="mock_data"),
    Policy(policy_type="Cancellation", airline_code="UA", policy_text="United: Most tickets (except Basic Economy) have no change fees, cancellation yields future flight credit. Refundable tickets get refund.", source_url="mock_data"),


    # Emirates (EK)
    Policy(policy_type="Pet Travel", airline_code="EK", policy_text="Emirates: No pets in cabin (except falcons on some routes). Pets travel as checked baggage (fees apply, <17hr journey) or cargo based on size/weight/route. Book well in advance.", source_url="mock_data"),
    Policy(policy_type="Baggage", airline_code="EK", policy_text="Emirates: Allowance by weight or piece depending on route/fare. Economy often 20-35kg or 1-2 pieces. Check specific ticket rules. Carry-on: 1 bag (7kg).", source_url="mock_data"),
    Policy(policy_type="Cancellation", airline_code="EK", policy_text="Emirates: Fees and refund eligibility depend heavily on fare type (Saver, Flex, Flex Plus). Check specific ticket conditions.", source_url="mock_data"),

]
try:
    db.add_all(policies)
    db.commit() # Commit after adding policies
    print(f"{len(policies)} Policies added.")
except Exception as e:
    db.rollback()
    print(f"Error adding policies: {e}")


# Close the session
db.close()

print("\nSample data loading process finished.")

