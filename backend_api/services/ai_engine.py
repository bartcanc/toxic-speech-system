import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

from core.config import MODEL_PATH

# 1. Wybór sprzętu
if torch.cuda.is_available():
    device = torch.device("cuda")
elif torch.backends.mps.is_available():
    device = torch.device("mps")
else:
    device = torch.device("cpu")

print(f"Silnik AI uruchomiony na: {device}")

# 2. Inicjalizacja modelu w pamięci RAM/VRAM
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)
model.to(device)
model.eval()

def predict_toxicity(text: str) -> dict:
    """Wnioskowanie Multi-Label. Zwraca listę wykrytych zagrożeń i ich prawdopodobieństwa."""
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=128, padding=True)
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)
        probabilities = torch.sigmoid(outputs.logits)[0] 
        
    score_toxic = probabilities[0].item()
    score_scam = probabilities[1].item()
    score_grooming = probabilities[2].item()
    # score_cb = probabilities[3].item()

    THRESHOLDS = {
        "TOXIC": 0.97,
        "SCAM": 0.05,
        "GROOMING": 0.77,
        # "CYBERBULLYING": 0.5
    }
    detected_flags = []
    
    if score_toxic >= THRESHOLDS["TOXIC"]:
        detected_flags.append("TOXIC")
    if score_scam >= THRESHOLDS["SCAM"]:
        detected_flags.append("SCAM")
    if score_grooming >= THRESHOLDS["GROOMING"]:
        detected_flags.append("GROOMING")
    # if score_cb >= THRESHOLDS["CYBERBULLYING"]:
    #     detected_flags.append("CYBERBULLYING")
        
    is_safe = len(detected_flags) == 0

    return {
        "is_safe": is_safe,
        "detected_flags": detected_flags if not is_safe else ["OK"],
        "confidence_scores": {
            "toxic": round(score_toxic, 2),
            "scam": round(score_scam, 2),
            "grooming": round(score_grooming, 2)
            # "cyberbullying": round(score_cb, 2)
        }
    }