from datasets import load_dataset, Dataset
import pandas as pd
import torch
import numpy as np
import evaluate
from transformers import AutoTokenizer, AutoModelForSequenceClassification, TrainingArguments, Trainer
from torch.utils.data import DataLoader, WeightedRandomSampler
"""
====================================================================================================================
"""
print("=== WERYFIKACJA SYSTEMU ===")

if torch.cuda.is_available():
    device = torch.device("cuda")
    print(f"Wykryto GPU NVIDIA: {torch.cuda.get_device_name(0)}")
elif torch.backends.mps.is_available():
    device = torch.device("mps")
    print("Wykryto akcelerator Apple Silicon (Metal/MPS).")
else:
    device = torch.device("cpu")
    print("Brak sprzętowego wsparcia GPU. System użyje procesora (CPU).")
"""
====================================================================================================================
"""
print("\n=== KROK 1: POBIERANIE ZBIORU DANYCH ===")

dataset = load_dataset("ptaszynski/cdt")                                
#   ta funkcja domyslnie laczy sie z hugging face zeby pobrac wskazany dataset                                
#   https://huggingface.co/datasets/ptaszynski/cdt
#   mozna tez lokalnie zczytywac np. load_dataset("csv", data_files="dane.csv")

print("\nStruktura zbioru danych:")
print(dataset)

print("\nPrzykład z bazy treningowej:")
przyklad = dataset['train'][0]
print(f"Tekst: {przyklad['sentence']}")
print(f"Etykieta (0=OK, 1=Hejt): {przyklad['target']}")
"""
====================================================================================================================
"""
print("\n=== KROK 2: POBIERANIE SŁOWNIKA (HerBERT) I TOKENIZACJA ===")
model_name = "allegro/herbert-base-cased"
print(f"Pobieranie tokenizatora dla modelu: {model_name}...")

# Pobieramy słownik z chmury
tokenizer = AutoTokenizer.from_pretrained(model_name)

# --- EKSPERYMENT (jak AI widzi tekst) ---
test_sentence = przyklad['sentence']
tokens = tokenizer.tokenize(test_sentence)
token_ids = tokenizer.encode(test_sentence)

print("\nJak Sztuczna Inteligencja widzi Twój tekst?")
print(f"Oryginał: {test_sentence}")
print(f"Tokeny (Pocięte słowa): {tokens}")
print(f"ID Tokenów (Liczby dla karty graficznej): {token_ids}")

# --- WŁAŚCIWA TOKENIZACJA CAŁEJ BAZY ---
print("\nPrzetwarzanie (tokenizacja) całych 11 000 tekstów...")

def tokenize_function(examples):
    return tokenizer(examples["sentence"], padding="max_length", truncation=True, max_length=128)

tokenized_datasets = dataset.map(tokenize_function, batched=True)

print("\nZbiór danych został ztokenizowany i jest gotowy do wstrzyknięcia do modelu")
"""
====================================================================================================================
"""
print("\n=== KROK 2.5: CZYSZCZENIE I BALANSOWANIE ===")                             #   dopóki nie zostanie przygotowany właściwy dataset, ograniczamy obecny do takiej samej liczby próbek dla obu przypadków
tokenized_datasets = tokenized_datasets.filter(lambda x: x["target"] in [0, 1])

# 2. TERAZ BALANSUJEMY TYLKO ZBIÓR TRENINGOWY
train_df = tokenized_datasets["train"].to_pandas()
hejt_df = train_df[train_df['target'] == 1]
ok_df = train_df[train_df['target'] == 0]

n_hejt = len(hejt_df)
print(f"Wykryto {n_hejt} przykładów hejtu. Balansowanie treningu...")

ok_sampled_df = ok_df.sample(n=n_hejt, random_state=42)
balanced_train_df = pd.concat([hejt_df, ok_sampled_df]).sample(frac=1, random_state=42)

# 3. PODMIENIAMY ZBIORY W OBIEKCIE
tokenized_datasets["train"] = Dataset.from_pandas(balanced_train_df, preserve_index=False)

print(f"Finał: Train={len(tokenized_datasets['train'])}, Test={len(tokenized_datasets['test'])}")
"""
====================================================================================================================
"""
print("\n=== KROK 3: FORMATOWANIE DANYCH DLA KARTY GRAFICZNEJ ===")
tokenized_datasets = tokenized_datasets.rename_column("target", "labels")
tokenized_datasets = tokenized_datasets.remove_columns(["sentence"])
tokenized_datasets.set_format("torch")
"""
====================================================================================================================
"""
print("\n=== KROK 4: POBRANIE MODELU ===")
model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=2, use_safetensors=True)
model.to(device)
"""
====================================================================================================================
"""
print("\n=== KROK 5: KONFIGURACJA TRENINGU ===")
training_args = TrainingArguments(
    output_dir="./training_results",        # gdzie zapisywać postępy
    eval_strategy="epoch",                              # po każdej epoce model jest ewaluowany
    save_strategy="epoch",                              # do epokę zapisywane jest postęp
    learning_rate=2e-5,                                 # prędkość nauki
    per_device_train_batch_size=8,                      # ile próbek na raz ładowane jest do VRAM karty
    per_device_eval_batch_size=8,
    num_train_epochs=3,                                 # ile razy model przeczyta całą książkę
    weight_decay=0.01,
)

# Narzędzie do sprawdzania skuteczności
metric = evaluate.load("accuracy")

def compute_metrics(eval_pred):
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)
    return metric.compute(predictions=predictions, references=labels)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_datasets["train"],
    eval_dataset=tokenized_datasets["test"],
    compute_metrics=compute_metrics,
)
"""
====================================================================================================================
"""
print("\n=== KROK 6: TRENING I ZAPISYWANIE MODELU ===")
print("\nROZPOCZĘCIE FINE TUNINGU...)")
trainer.train()

trainer.save_model("./model")
tokenizer.save_pretrained("./model")

print("Model jest gotowy")