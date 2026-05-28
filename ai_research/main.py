from fastapi import FastAPI
from pydantic import BaseModel
import torch
import os
from transformers import AutoTokenizer, AutoModelForSequenceClassification

app = FastAPI(title="Toxic Speech AI Engine")

MODEL_PATH = os.getenv("MODEL_PATH")

if not MODEL_PATH:
    raise ValueError("Brak zmiennej MODEL_PATH. Sprawdź docker-compose.yml!")

print("Ładowanie modelu i tokenizatora z dysku...")
device = torch.device("cpu")
model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH).to(device)
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
print("Model gotowy do pracy!")

# progi (thresholds)
THRESHOLDS = {
    "TOXIC": 0.48,
    "SCAM": 0.09,
    "GROOMING": 0.35
}

class TextRequest(BaseModel):
    text: str

@app.post("/analyze")
def analyze_text(request: TextRequest):
    text = request.text
    
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=128).to(device)
    
    with torch.no_grad():
        outputs = model(**inputs)
        raw_logits = outputs.logits[0]

    probs = torch.sigmoid(raw_logits).tolist()
    
    score_toxic = probs[0]
    score_scam = probs[1]
    score_grooming = probs[2]
    
    detected_flags = []
    if score_toxic >= THRESHOLDS["TOXIC"]:
        detected_flags.append("TOXIC")
    if score_scam >= THRESHOLDS["SCAM"]:
        detected_flags.append("SCAM")
    if score_grooming >= THRESHOLDS["GROOMING"]:
        detected_flags.append("GROOMING")
        
    is_safe = len(detected_flags) == 0
    if is_safe:
        detected_flags.append("OK")
        
    return {
        "status": "success",
        "text_analyzed": text,
        "results": {
            "is_safe": is_safe,
            "detected_flags": detected_flags,
            "confidence_scores": {
                "toxic": round(score_toxic, 4),
                "scam": round(score_scam, 4),
                "grooming": round(score_grooming, 4)
            }
        }
    }