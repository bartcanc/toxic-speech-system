import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# Ścieżka do Twojego wyuczonego modelu (cofamy się o jeden folder wyżej z 'app')
MODEL_PATH = "./ai_research/model"

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
    """Główna funkcja wnioskująca. Przyjmuje czysty tekst, zwraca słownik z wynikami."""
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=128, padding=True)
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)
        probabilities = torch.nn.functional.softmax(outputs.logits, dim=-1)
        
        predicted_class = torch.argmax(probabilities, dim=-1).item()
        confidence = probabilities[0][predicted_class].item() * 100

    verdict_label = "HEJT" if predicted_class == 1 else "OK"
    
    return {
        "verdict": verdict_label,
        "confidence": confidence
    }