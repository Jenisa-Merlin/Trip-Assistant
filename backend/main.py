from fastapi import FastAPI, Request, Query
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

# Dynamically ensure backend package is importable
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.query_processing.orchestrator import process_user_query

# -----------------------------------------------------
# FastAPI App Configuration
# -----------------------------------------------------
app = FastAPI(
    title="Trip Assistant API",
    description="An intelligent assistant for flight bookings, cancellations, and flight status queries.",
    version="1.0.0"
)

# -----------------------------------------------------
# CORS Setup (for frontend integration)
# -----------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------
# Basic Root Route
# -----------------------------------------------------
@app.get("/")
def home():
    return {"message": "Welcome to the Trip Assistant API!"}

# -----------------------------------------------------
# GET Endpoint (for quick browser testing)
# -----------------------------------------------------
@app.get("/query")
def ask(
    query: str = Query(..., description="Enter your question here, e.g. 'What is the status of flight AI202?'"),
    user_id: str = Query("default_user", description="Optional user ID for session tracking")
):
    """
    Handles GET requests — great for quick testing in browser or Swagger.
    """
    result = process_user_query(user_id, query)
    return {"response": result}

# -----------------------------------------------------
# POST Endpoint (used by the React frontend)
# -----------------------------------------------------
@app.post("/query")
async def handle_query(request: Request):
    """
    Handles POST requests from the frontend.

    Example JSON body:
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

# -----------------------------------------------------
# Run command (development only)
# -----------------------------------------------------
# To run manually: uvicorn backend.main:app --reload
