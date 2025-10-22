def classify_airline_intent(query: str):
    """
    Classify airline-related queries into mockdb/api/rag.
    """
    if any(k in query.lower() for k in ["book", "cancel", "pnr", "seat", "refund"]):
        return "mockdb"
    elif any(k in query.lower() for k in ["status", "live", "track"]):
        return "api"
    elif any(k in query.lower() for k in ["policy", "baggage", "rules", "terms"]):
        return "rag"
    else:
        return "mockdb"
