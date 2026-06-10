import os
import requests

AI_SERVICE_URL = os.getenv("ai_research_URL")

def predict_toxicity(text: str):
    try:
        response = requests.post(AI_SERVICE_URL, json={"text": text}, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"--> [SYSTEM ERROR] Błąd połączenia z silnikiem AI: {e}")
        return {"status": "error", "message": "Silnik AI jest tymczasowo niedostępny."}