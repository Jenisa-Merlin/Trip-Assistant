# backend/nlp_pipeline/llm_response.py
from openai import OpenAI
import os

class LLMResponder:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def generate(self, intent: str, entities: dict, db_result: dict):
        prompt = f"""
        User intent: {intent}
        Entities: {entities}
        Database result: {db_result}

        Compose a helpful airline-related response in plain English.
        """
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        return response.choices[0].message.content
