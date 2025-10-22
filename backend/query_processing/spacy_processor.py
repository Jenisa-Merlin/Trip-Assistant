# backend/query_processing/spacy_processor.py
import re
import spacy

nlp = spacy.load("en_core_web_sm")

FLIGHT_RE = re.compile(r"\b([A-Z]{2}\d{3,4})\b")  # AI202, UA2402

def extract_entities_and_keywords(text: str) -> dict:
    """
    Returns:
      {
        "flight_number": "AI202",
        "dates": [...],
        "airline": "...",
        "locations": [...],
        "keywords": ["arrival", "delay", ...]
      }
    """
    doc = nlp(text)
    entities = {"keywords": []}

    # Named entities
    locations = []
    dates = []
    for ent in doc.ents:
        if ent.label_ in ("GPE", "LOC"):
            locations.append(ent.text)
        elif ent.label_ in ("DATE", "TIME"):
            dates.append(ent.text)
        elif ent.label_ in ("ORG"):
            entities.setdefault("orgs", []).append(ent.text)

    if locations:
        entities["locations"] = locations
    if dates:
        entities["dates"] = dates

    # Flight number via regex (most reliable)
    m = FLIGHT_RE.search(text.upper())
    if m:
        entities["flight_number"] = m.group(1)

    # keywords detection
    keyword_set = {"status", "arrival", "depart", "departure", "eta", "delay", "gate", "terminal",
                   "schedule", "on time", "cancel", "book", "pnr", "seat", "baggage", "refund"}
    text_lower = text.lower()
    for kw in keyword_set:
        if kw in text_lower:
            entities["keywords"].append(kw)

    # quick intent hint (best-effort)
    if any(k in entities["keywords"] for k in ("arrival", "departure", "status", "eta", "delay")):
        entities["intent_hint"] = "api_flight_info"
    elif "cancel" in entities["keywords"]:
        entities["intent_hint"] = "cancel_booking"
    elif "book" in entities["keywords"]:
        entities["intent_hint"] = "create_booking"
    elif any(k in entities["keywords"] for k in ("policy", "baggage", "refund")):
        entities["intent_hint"] = "rag_policy"
    else:
        entities["intent_hint"] = "unknown"

    return entities
