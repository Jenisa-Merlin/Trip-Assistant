# models.py
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.DB.database import Base

class Customer(Base):
    __tablename__ = "customers"
    customer_id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String)
    phone = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    bookings = relationship("Booking", back_populates="customer")


class Flight(Base):
    __tablename__ = "flights"
    flight_id = Column(Integer, primary_key=True, index=True)
    airline_code = Column(String)
    flight_number = Column(String)
    source_airport_code = Column(String)
    destination_airport_code = Column(String)
    scheduled_departure = Column(DateTime)
    scheduled_arrival = Column(DateTime)
    current_status = Column(String)
    seats = relationship("Seat", back_populates="flight")
    bookings = relationship("Booking", back_populates="flight")


class Booking(Base):
    __tablename__ = "bookings"
    pnr = Column(String, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.customer_id"))
    flight_id = Column(Integer, ForeignKey("flights.flight_id"))
    booking_date = Column(DateTime, default=datetime.utcnow)
    assigned_seat = Column(String)
    fare_amount = Column(Float)
    payment_status = Column(String)
    booking_status = Column(String)
    refund_amount = Column(Float, nullable=True)
    refund_date = Column(DateTime, nullable=True)
    customer = relationship("Customer", back_populates="bookings")
    flight = relationship("Flight", back_populates="bookings")


class Seat(Base):
    __tablename__ = "seats"
    seat_id = Column(Integer, primary_key=True, index=True)
    flight_id = Column(Integer, ForeignKey("flights.flight_id"))
    row_number = Column(Integer)
    column_letter = Column(String)
    seat_class = Column(String)
    price = Column(Float)
    is_booked = Column(Boolean, default=False)
    flight = relationship("Flight", back_populates="seats")


class Policy(Base):
    __tablename__ = "policies"
    policy_id = Column(Integer, primary_key=True, index=True)
    policy_type = Column(String)
    airline_code = Column(String)
    policy_text = Column(String)
    source_url = Column(String)
    last_updated = Column(DateTime, default=datetime.utcnow)
