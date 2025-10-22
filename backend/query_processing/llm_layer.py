# backend/query_processing/llm_layer.py
import os

OPENAI_KEY = os.getenv("OPENAI_API_KEY")

def craft_flight_info_response(flight_info: dict, user_question: str = "") -> str:
    """
    If OPENAI_KEY available, call the API to create a natural response.
    Otherwise, return a templated response using available fields.
    """
    # Template fallback
    if not flight_info:
        return "I couldn't find any live information for that flight right now."

    template = []
    status = flight_info.get("status")
    airline = flight_info.get("airline")
    fn = flight_info.get("flight_number")
    dep = flight_info.get("departure_airport")
    arr = flight_info.get("arrival_airport")
    dep_est = flight_info.get("departure_estimated") or flight_info.get("departure_scheduled")
    arr_est = flight_info.get("arrival_estimated") or flight_info.get("arrival_scheduled")

    template.append(f"Flight {fn} ({airline}) is currently *{status}*.")
    if dep and arr:
        template.append(f"It operates from {dep} → {arr}.")
    if dep_est:
        template.append(f"Estimated departure: {dep_est}.")
    if arr_est:
        template.append(f"Estimated arrival: {arr_est}.")

    simple_answer = " ".join(template)

    # Try to use OpenAI if key exists (optional)
    if OPENAI_KEY:
        try:
            # Minimal OpenAI usage by calling requests to a simple endpoint if needed.
            # If you prefer the official client, replace with openai.ChatCompletion etc.
            import openai
            openai.api_key = OPENAI_KEY
            prompt = (
                f"User asked: {user_question}\n\n"
                f"Flight data: {flight_info}\n\n"
                "Compose a short clear helpful reply (1-2 sentences)."
            )
            resp = openai.ChatCompletion.create(
                model="gpt-4o-mini" if "gpt-4o-mini" in openai.Model.list() else "gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=200,
            )
            content = resp.choices[0].message.content.strip()
            return content
        except Exception as e:
            # fallback to template
            print("[LLM] error or no quota:", e)
            return simple_answer

    return simple_answer
