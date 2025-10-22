# backend/DB/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# ✅ build path to root-level airline.db
BASE_DIR = os.path.dirname(os.path.abspath(__file__))      # backend/DB/
ROOT_DIR = os.path.dirname(os.path.dirname(BASE_DIR))      # Trip-Assistant/
DATABASE_PATH = os.path.join(ROOT_DIR, "airline.db")       # Trip-Assistant/airline.db

DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

print(f"✅ Using database at: {DATABASE_PATH}")
