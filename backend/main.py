from fastapi import FastAPI, Request, Query
from backend.query_processing.orchestrator import process_user_query

app = FastAPI(
    title="Trip Assistant API",
    description="An intelligent assistant for flight bookings, cancellations, and flight status queries.",
    version="1.0.0"
)


@app.get("/")
def home():
    return {"message": "Welcome to the Trip Assistant API!"}


# ✅ GET endpoint for quick browser testing
@app.get("/query")
def ask(
    query: str = Query(..., description="Enter your question here, e.g. 'What is the status of flight AI202?'"),
    user_id: str = Query("default_user", description="Optional user ID for session tracking")
):
    result = process_user_query(user_id, query)
    return {"response": result}


# ✅ POST endpoint for structured requests (Swagger UI)
@app.post("/query")
async def handle_query(request: Request):
    """
    POST endpoint for chatbot-like queries.
    Example:
    {
      "query": "I want to cancel my flight ticket",
      "user_id": "user123"
    }
    """
    data = await request.json()
    user_query = data.get("query")
    user_id = data.get("user_id", "default_user")

    if not user_query:
        return {"error": "Query text is required."}

    response = process_user_query(user_id, user_query)
    return {"response": response}
