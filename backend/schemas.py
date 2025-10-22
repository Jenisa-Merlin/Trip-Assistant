# schemas.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class CustomerBase(BaseModel):
    name: str
    email: str
    phone: str

class CustomerResponse(CustomerBase):
    customer_id: int
    created_at: datetime
    class Config:
        orm_mode = True


class FlightBase(BaseModel):
    airline_code: str
    flight_number: str
    source_airport_code: str
    destination_airport_code: str
    scheduled_departure: datetime
    scheduled_arrival: datetime
    current_status: str

class FlightResponse(FlightBase):
    flight_id: int
    class Config:
        orm_mode = True


class BookingBase(BaseModel):
    pnr: str
    customer_id: int
    flight_id: int
    assigned_seat: str
    fare_amount: float
    payment_status: str
    booking_status: str

class BookingResponse(BookingBase):
    booking_date: datetime
    class Config:
        orm_mode = True


class PolicyBase(BaseModel):
    policy_type: str
    airline_code: str
    policy_text: str

class PolicyResponse(PolicyBase):
    policy_id: int
    last_updated: datetime
    class Config:
        orm_mode = True
