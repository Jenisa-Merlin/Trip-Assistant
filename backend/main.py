# backend/main.py
from fastapi import FastAPI
from backend.database import SessionLocal, engine
import backend.models
from backend.nlp_pipeline.pipeline import QueryProcessor

backend.models.Base.metadata.create_all(bind=engine)
app = FastAPI(title="Airline Query Processor 🚀")

processor = QueryProcessor()

@app.post("/query")
def handle_query(query: str):
    result = processor.process(query)
    return result

@app.get("/")
def root():
    return {"message": "Welcome to Airline API 🚀"}
