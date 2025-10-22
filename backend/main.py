# backend/main.py
from fastapi import FastAPI
from backend.database import engine
import backend.models
from backend.nlp_pipeline.pipeline import QueryProcessor
from backend.routers.booking_router import booking_router
from backend.routers.flight_router import flight_router
from backend.routers.policy_router import policy_router

backend.models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Airline Request System")

processor = QueryProcessor()

@app.post("/query")
def handle_query(query: str):
    result = processor.process(query)
    return result

@app.get("/")
def root():
    return {"message": "Welcome to Airline API 🚀"}

app.include_router(booking_router, prefix="/api")
app.include_router(flight_router, prefix="/api")
app.include_router(policy_router, prefix="/api")