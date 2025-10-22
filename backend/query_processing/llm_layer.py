# backend/query_processing/llm_layer.py
import os
import openai
from backend.utils.config import OPENAI_API_KEY

# Set up OpenAI key
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY
    # Check for gpt-4o-mini availability once
    try:
        models = openai.Model.list()
        DEFAULT_MODEL = "gpt-4o-mini" if "gpt-4o-mini" in [m.id for m in models] else "gpt-3.5-turbo"
        print(f"[LLM] OpenAI key found. Using model: {DEFAULT_MODEL}")
    except Exception as e:
        print(f"[LLM] Warning: OpenAI key provided but API check failed. {e}")
        DEFAULT_MODEL = "gpt-3.5-turbo"
else:
    print("[LLM] Warning: OPENAI_API_KEY not set. LLM features will be disabled.")
    DEFAULT_MODEL = None


def generate_llm_response(prompt: str, model: str = None) -> str | None:
    """Helper function to call OpenAI API."""
    if not OPENAI_API_KEY or not DEFAULT_MODEL:
        return None  # Fallback to template
    
    try:
        resp = openai.ChatCompletion.create(
            model=model or DEFAULT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1, # Low temperature for factual responses
            max_tokens=250,
        )
        content = resp.choices[0].message.content.strip()
        return content
    except Exception as e:
        print(f"[LLM] Error: {e}")
        return None # Fallback to template


def craft_flight_info_response(flight_info: dict, user_question: str = "") -> str:
    """
    If OPENAI_KEY available, call the API to create a natural response.
    Otherwise, return a templated response using available fields.
    """
    # 1. Try to use LLM for a natural response
    if OPENAI_API_KEY:
        # --- REFINED PROMPT ---
        # Instruct the LLM to be specific to the user's question.
        prompt = (
            f"You are an airline assistant. A user asked: '{user_question}'\n\n"
            f"Here is the flight data I found: {flight_info}\n\n"
            f"Please answer the user's *specific question* using *only* this data. "
            f"For example, if they ask for 'arrival time', just give the arrival time. If they ask for 'status', just give the status. "
            f"If the data doesn't contain the specific info (e.g., they ask for a 'gate' but it's not listed), "
            f"state that you have the flight status but not that specific detail."
        )
        llm_response = generate_llm_response(prompt)
        if llm_response:
            return llm_response

    # 2. Template fallback if LLM fails or no key
    print("[LLM] Fallback: Using template response for flight info.")
    if not flight_info:
        return "I couldn't find any live information for that flight right now."

    status = flight_info.get("status", "Unknown")
    airline = flight_info.get("airline", "")
    fn = flight_info.get("flight_number")
    q_lower = user_question.lower()

    # --- REFINED TEMPLATE FALLBACK ---
    # Try to answer the specific question first.
    if "arrival" in q_lower or "eta" in q_lower:
        arr_time = flight_info.get("arrival_estimated") or flight_info.get("arrival_scheduled")
        if arr_time:
            return f"The estimated arrival time for {fn} is {arr_time}."
    
    if "departure" in q_lower:
        dep_time = flight_info.get("departure_estimated") or flight_info.get("departure_scheduled")
        if dep_time:
            return f"The estimated departure time for {fn} is {dep_time}."

    if "gate" in q_lower:
        arr_gate = flight_info.get("arrival_gate")
        dep_gate = flight_info.get("departure_gate")
        if arr_gate:
            return f"Flight {fn} is scheduled to arrive at gate {arr_gate}."
        if dep_gate:
            return f"Flight {fn} is scheduled to depart from gate {dep_gate}."
            
    if "terminal" in q_lower:
        arr_terminal = flight_info.get("arrival_terminal")
        dep_terminal = flight_info.get("departure_terminal")
        if arr_terminal:
            return f"Flight {fn} is scheduled to arrive at terminal {arr_terminal}."
        if dep_terminal:
            return f"Flight {fn} is scheduled to depart from terminal {dep_terminal}."

    # If no specific question was matched, build the generic response
    base_response = f"Flight {fn} ({airline}) is currently *{status}*."
    template = [base_response]
    dep = flight_info.get("departure_airport")
    arr = flight_info.get("arrival_airport")

    if dep and arr:
        template.append(f"It is flying from {dep} to {arr}.")

    return " ".join(template)


def call_llm_for_rag(user_query: str, policy_docs: list[str]) -> str:
    """
    Answers a user's policy question using only the provided policy documents.
    """
    if not policy_docs:
        return "I couldn't find any specific policies on that topic."

    # 1. Try to use LLM for RAG response
    if OPENAI_API_KEY:
        context = "\n\n".join(policy_docs)
        prompt = (
            f"You are an airline policy assistant.\n"
            f"Please answer the user's question: '{user_query}'\n\n"
            f"Use *only* the following policy information to answer. Do not add any external knowledge. If the answer isn't in the documents, say so.\n\n"
            f"--- POLICY DOCUMENTS ---\n"
            f"{context}\n"
            f"--- END OF DOCUMENTS ---\n\n"
            f"Answer:"
        )
        llm_response = generate_llm_response(prompt)
        if llm_response:
            return llm_response

    # 2. Template fallback (just return the first doc)
    print("[LLM] Fallback: Using template response for RAG.")
    return f"Here is the policy I found:\n{policy_docs[0]}"


def get_conversational_fallback(user_query: str) -> str:
    """
    Provides a generic, conversational fallback if no intent is matched.
    """
    # 1. Try to use LLM
    if OPENAI_API_KEY:
        prompt = (
            f"You are a helpful airline assistant. The user said: '{user_query}'\n"
            "This query didn't match any specific tools (like booking, cancellation, or flight status).\n"
            "Respond conversationally (1-2 sentences). Ask for clarification or gently guide them towards tasks you *can* do (like check flight status, book a flight, or look up policies)."
        )
        llm_response = generate_llm_response(prompt)
        if llm_response:
            return llm_response
            
    # 2. Template fallback
    return "I'm sorry, I'm not sure how to help with that. I can assist with flight status, new bookings, cancellations, and airline policies. Could you please rephrase your request?"

