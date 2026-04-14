import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

print("=== TESTOWANIE MODELU ===")
MODEL_PATH = "./ai_research/model"
"""
=== KROK 1: ZAŁADOWANIE MODELU  ===
"""
print("Ładowanie modelu z dysku...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)

if torch.cuda.is_available():
    device = torch.device("cuda")
    print(f"Wykryto GPU NVIDIA: {torch.cuda.get_device_name(0)}")
elif torch.backends.mps.is_available():
    device = torch.device("mps")
    print("Wykryto akcelerator Apple Silicon (Metal/MPS).")
else:
    device = torch.device("cpu")
    print("Brak sprzętowego wsparcia GPU. System użyje procesora (CPU).")

model.to(device)
print(f"Model gotowy i załadowany\n")
"""
=== KROK 2: FUNKCJA OCENY TEKSTU  ===
"""
def eval_text(tekst):
    inputs = tokenizer(tekst, return_tensors="pt", truncation=True, max_length=128, padding=True)
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        
        # Obliczanie prawdopodobieństwa
        probabilities = torch.nn.functional.softmax(logits, dim=-1)
        
        # 0 = OK, 1 = Hejt
        predicted_class = torch.argmax(probabilities, dim=-1).item()
        
        # Pewność modelu dla wybranego werdyktu
        confidence = probabilities[0][predicted_class].item() * 100

    etykieta = "HEJT" if predicted_class == 1 else "OK"
    print(f"Tekst: '{tekst}'")
    print(f"Werdykt: {etykieta} (Pewność modelu: {confidence:.2f}%)\n")

"""
=== KROK 3: TEST  ===
"""
print("Rozpoczynamy skanowanie przykładowych zdań:\n")

eval_text("Ale masz super projekt, świetnie to wygląda!")
eval_text("Ale z ciebie kretyn.")
eval_text("Wydaje mi się, że dzisiaj będzie padać deszcz.")
eval_text("Idź się zabić.")