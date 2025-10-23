# 🧳 Trip Assistant

Trip Assistant is an AI-powered travel chatbot that helps users manage flights, bookings, and travel queries through a conversational interface.  
It integrates **FastAPI** for the backend and **Streamlit** for the frontend.

---

## 🚀 Features
- Flight booking and policy management system  
- NLP-powered chatbot (spaCy + BERT model)  
- FastAPI backend with automatic docs (`/docs`)  
- Streamlit frontend UI  
- SQLite database with mock airline data  
- Optional integration with external APIs (AviationStack, OpenAI)

---

## 🧩 Prerequisites
Make sure you have:
- **Python** 3.8 or later → `python --version`
- **pip** (comes with Python) → `pip --version`
- **Git** (if cloning the repo)

---

## ⚙️ Setup Instructions

### Clone or Download
```
git clone https://github.com/yourusername/Trip-Assistant.git
cd Trip-Assistant
```
Or download and extract the project folder manually.

### Create and Activate Virtual Environment
```
python -m venv venv
```

Windows:
```
.\venv\Scripts\activate
```

macOS/Linux:
```
source venv/bin/activate
```

### Install Dependencies
```
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### Configure API Keys (Optional)

Create a .env file in the project root and add your API keys:

### .env
```
AVIATIONSTACK_API_KEY=your_aviationstack_api_key
OPENAI_API_KEY=your_openai_api_key
```

If not provided, default or template-based responses will be used.

### Initialize Database
```
python sample_data.py
```

This creates and populates airline.db with sample flights, customers, and policies.

### Run the Backend (FastAPI)
```
uvicorn main:app --reload --port 8000
```

Open docs: http://127.0.0.1:8000/docs

### Run the Frontend (Streamlit)

Open a new terminal (keep backend running):

### Activate venv again if needed
```
streamlit run streamlit_app.py
```

App runs at: http://localhost:8501

### Stop the App

Stop Streamlit: Ctrl + C

Stop FastAPI: Ctrl + C

Deactivate environment: deactivate