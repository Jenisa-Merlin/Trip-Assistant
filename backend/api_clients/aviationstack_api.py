import os
import requests
from datetime import datetime

API_KEY = os.getenv("AVIATIONSTACK_API_KEY", "e7756e008bc428874a9335672813efe7")
BASE_URL = "http://api.aviationstack.com/v1/flights"

def _normalize_flight_data(rec: dict) -> dict:
    """Helper function to normalize a single flight record from AviationStack."""
    flight_number = rec.get("flight", {}).get("iata") or rec.get("flight", {}).get("number")
    return {
        "flight_number": flight_number,
        "airline": rec.get("airline", {}).get("name"),
        "status": rec.get("flight_status"),
        "departure_airport": rec.get("departure", {}).get("airport"),
        "arrival_airport": rec.get("arrival", {}).get("airport"),
        "departure_scheduled": rec.get("departure", {}).get("scheduled"),
        "departure_estimated": rec.get("departure", {}).get("estimated"),
        "arrival_scheduled": rec.get("arrival", {}).get("scheduled"),
        "arrival_estimated": rec.get("arrival", {}).get("estimated"),
        "departure_gate": rec.get("departure", {}).get("gate"),
        "arrival_gate": rec.get("arrival", {}).get("gate"),
        "departure_terminal": rec.get("departure", {}).get("terminal"),
        "arrival_terminal": rec.get("arrival", {}).get("terminal"),
        "raw": rec
    }

def get_live_flight_data(flight_number: str) -> dict | None:
    """
    Returns normalized flight info dict or None.
    Normalized keys: flight_number, airline, status, departure_airport, arrival_airport,
    departure_estimated, arrival_estimated, scheduled_departure, scheduled_arrival, gate, terminal
    """
    if not API_KEY:
        # No key configured — caller should handle fallback
        print("[AviationStack] No API key configured.")
        return None

    params = {"access_key": API_KEY, "flight_iata": flight_number}
    try:
        resp = requests.get(BASE_URL, params=params, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        if not data.get("data") or len(data["data"]) == 0:
            print(f"[AviationStack] No data found for {flight_number}")
            return None

        # take first matching record
        rec = data["data"][0]
        return _normalize_flight_data(rec)
    except Exception as e:
        print(f"[AviationStack] error in get_live_flight_data: {e}")
        return None

def search_flights_by_route(dep_iata: str, arr_iata: str) -> list[dict] | None:
    """
    Searches for flights between two airports for the current day.
    """
    if not API_KEY:
        print("[AviationStack] No API key configured.")
        return None

    # Get today's date in YYYY-MM-DD format
    flight_date = datetime.now().strftime('%Y-%m-%d')
    
    params = {
        "access_key": API_KEY,
        "dep_iata": dep_iata.upper(),
        "arr_iata": arr_iata.upper(),
        "flight_date": flight_date,
        "limit": 10 # Limit to 10 flights for demo
    }
    
    try:
        resp = requests.get(BASE_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        if not data.get("data") or len(data["data"]) == 0:
            print(f"[AviationStack] No flights found for route {dep_iata}->{arr_iata} on {flight_date}")
            return [] # Return empty list for no flights

        # Normalize all flight records
        flights = [_normalize_flight_data(rec) for rec in data["data"]]
        return flights
    except Exception as e:
        print(f"[AviationStack] error in search_flights_by_route: {e}")
        return None # Return None for an actual API error

