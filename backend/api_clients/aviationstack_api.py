import os
import requests

API_KEY = os.getenv("AVIATIONSTACK_API_KEY", "e7756e008bc428874a9335672813efe7")
BASE_URL = "http://api.aviationstack.com/v1/flights"

def get_live_flight_data(flight_number: str) -> dict | None:
    """
    Returns normalized flight info dict or None.
    Normalized keys: flight_number, airline, status, departure_airport, arrival_airport,
    departure_estimated, arrival_estimated, scheduled_departure, scheduled_arrival, gate, terminal
    """
    if not API_KEY:
        # No key configured — caller should handle fallback
        return None

    params = {"access_key": API_KEY, "flight_iata": flight_number}
    try:
        resp = requests.get(BASE_URL, params=params, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        if not data.get("data"):
            return None

        # take first matching record
        rec = data["data"][0]
        normalized = {
            "flight_number": rec.get("flight", {}).get("iata") or flight_number,
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
        return normalized
    except Exception as e:
        print("[AviationStack] error:", e)
        return None