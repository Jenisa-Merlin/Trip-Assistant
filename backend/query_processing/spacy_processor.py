# backend/query_processing/spacy_processor.py
import re
import spacy
from typing import Dict, List, Optional # Added typing imports

# Load spacy model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Spacy model 'en_core_web_sm' not found. Run 'python -m spacy download en_core_web_sm'")
    nlp = spacy.blank("en")


# Updated regex to be more flexible:
# Handles 2-3 letters (e.g., AI, DAL)
# Handles optional space (e.g., "AI 202" or "AI202")
# Handles 2-4 digits (e.g., 92, 202, 1070)
FLIGHT_RE = re.compile(r"\b([A-Z]{2,3})\s?(\d{2,4})\b")


def extract_entities_and_keywords(text: str) -> Dict[str, Optional[str | List[str]]]:
    """
    Extracts flight numbers, locations, dates, keywords, and provides an intent hint.

    Returns:
      Dict with keys like "flight_number", "airline_code", "flight_digits",
      "locations", "dates", "keywords", "intent_hint".
    """
    doc = nlp(text)
    entities: Dict[str, Optional[str | List[str]]] = {"keywords": []}

    # Named entities
    locations: List[str] = []
    dates: List[str] = []
    orgs: List[str] = [] # Initialize orgs
    for ent in doc.ents:
        if ent.label_ in ("GPE", "LOC"):
            # Check for 3-letter IATA codes (Spacy often misses them)
            # Also capture longer location names
            if len(ent.text) == 3 and ent.text.isupper():
                locations.append(ent.text)
            elif len(ent.text) > 3: # Avoid adding short, non-IATA codes unless 3 uppercase
                 # Simple check for likely airport names
                 if "airport" in ent.text.lower() or len(ent.text.split()) > 1 :
                      locations.append(ent.text)
        elif ent.label_ in ("DATE", "TIME"):
            dates.append(ent.text)
        elif ent.label_ == "ORG": # Check specifically for ORG
            # Basic filtering for potential airlines if needed
            orgs.append(ent.text)

    # IATA code regex (e.g., "from DEL to BOM")
    iata_re = re.compile(r"\b(from|to|flying from|flying to)\s+([A-Z]{3})\b", re.IGNORECASE) # Added IGNORECASE and more phrases
    for match in iata_re.finditer(text): # Use text directly
        locations.append(match.group(2).upper()) # Ensure uppercase

    if locations:
        # Remove duplicates preserving order (roughly)
        seen_loc = set()
        entities["locations"] = [loc for loc in locations if not (loc in seen_loc or seen_loc.add(loc))]

    if dates:
        entities["dates"] = dates
    if orgs:
        entities["orgs"] = orgs # Store detected organizations

    # Flight number via regex (most reliable)
    m = FLIGHT_RE.search(text.upper())
    if m:
        entities["flight_number"] = f"{m.group(1)}{m.group(2)}"
        entities["airline_code"] = m.group(1)
        entities["flight_digits"] = m.group(2)

    # Keywords detection
    keyword_set = {
        "status", "arrival", "depart", "departure", "eta", "delay", "gate", "terminal",
        "schedule", "on time", "cancel", "book", "pnr", "seat", "seats", # Added plural 'seats'
        "baggage", "refund", "policy", "pet", "animal", "check-in", "check in",
        "available", "availability", "how many", "empty", "vacant", # Added seat availability keywords
        "search", "find", "look for", "flights" # Added search keywords
    }
    text_lower = text.lower()
    detected_keywords: List[str] = [] # Start fresh list for keywords

    for kw in keyword_set:
        # Use regex word boundaries for more precise matching
        if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
            detected_keywords.append(kw)

    # Simple deduplication
    entities["keywords"] = sorted(list(set(detected_keywords)))

    # --- Intent Hint Logic (Order matters - more specific first) ---
    keywords = entities.get("keywords", []) # Get the final list

    # Check seat availability intent
    if any(k in keywords for k in ("seat", "seats")) and \
       any(k in keywords for k in ("available", "availability", "empty", "vacant", "how many")) and \
       "book" not in keywords:
         entities["intent_hint"] = "check_seat_availability"
    # Check flight status/info intent (keywords + potentially flight number)
    elif entities.get("flight_number") and \
         any(k in keywords for k in ("status", "arrival", "departure", "eta", "delay", "gate", "terminal", "schedule", "on time")):
        entities["intent_hint"] = "api_flight_info"
    # Check cancellation intent
    elif "cancel" in keywords and "book" not in keywords and "policy" not in keywords: # Avoid conflict with policy
        entities["intent_hint"] = "cancel_booking"
    # Check booking intent
    elif "book" in keywords:
        entities["intent_hint"] = "create_booking"
    # Check flight search intent (based on locations and search keywords)
    # Require at least two locations OR one location and search keywords
    elif (len(entities.get("locations", [])) >= 2 or \
          (len(entities.get("locations", [])) >= 1 and any(k in keywords for k in ("search", "find", "look for", "flights")))):
         entities["intent_hint"] = "search_flights_by_route"
    # Check policy intent (RAG)
    elif any(k in keywords for k in ("policy", "baggage", "refund", "pet", "animal", "check-in", "check in")) or "policy" in text_lower:
         # Refine policy check to avoid triggering on general words like 'check'
         if any(k in keywords for k in ("baggage", "refund", "pet", "animal", "check-in", "check in", "policy", "cancel")) or "policy" in text_lower:
              entities["intent_hint"] = "rag_policy"
         else: # Fallback if only ambiguous keywords like 'check' were found without policy context
              entities["intent_hint"] = "unknown"
    # Fallback check for flight status if only flight number and maybe generic words are present
    elif entities.get("flight_number") and not entities["intent_hint"]: # Check if intent hasn't been set yet
         entities["intent_hint"] = "api_flight_info"
    # Default/Fallback intent
    else:
         if not entities.get("intent_hint"): # Only set unknown if nothing else matched
            entities["intent_hint"] = "unknown"

    # Post-processing: If locations detected but no search intent, maybe ask clarification?
    # Example: User says "flights to DEL" - locations=['DEL'], keywords=[] -> intent='unknown'
    if entities["intent_hint"] == "unknown" and entities.get("locations"):
         # More robust check: if they mention 'flights' and have a location, likely a search
         if 'flights' in keywords:
              entities["intent_hint"] = "search_flights_by_route"
         # Could optionally add logic here to ask "Are you trying to search for flights?"
         pass # Keep it simple for now

    # Debug print (optional)
    # print(f"[SpaCy Processor] Text: '{text}' -> Entities: {entities}")

    return entities

