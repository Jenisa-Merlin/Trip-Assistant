# backend/utils/config.py
import os
from dotenv import load_dotenv

# Load .env file from the project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(BASE_DIR, '.env'))

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
