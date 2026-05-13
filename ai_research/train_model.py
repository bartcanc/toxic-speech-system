from datasets import load_dataset, Dataset, concatenate_datasets, Value
import pandas as pd
import torch
import numpy as np
import evaluate
from transformers import AutoTokenizer, AutoModelForSequenceClassification, TrainingArguments, Trainer
from torch.utils.data import DataLoader, WeightedRandomSampler
from config import MODEL_PATH, OUTPUT_DIR, CSV_PATH

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
# print("\n=== KROK 1: POBIERANIE ZBIORU DANYCH ===")

# dataset = load_dataset("ptaszynski/cdt")                                
# #   ta funkcja domyslnie laczy sie z hugging face zeby pobrac wskazany dataset                                
# #   https://huggingface.co/datasets/ptaszynski/cdt
# #   mozna tez lokalnie zczytywac np. load_dataset("csv", data_files="dane.csv")

# print("\nStruktura zbioru danych:")
# print(dataset)

# print("\nPrzykład z bazy treningowej:")
# przyklad = dataset['train'][0]
# print(f"Tekst: {przyklad['sentence']}")
# print(f"Etykieta (0=OK, 1=Hejt): {przyklad['target']}")

print("\n=== KROK 1: BUDOWA ZBIORU DANYCH ===")
# --- LOGIKA MAPOWANIA KLAS ---
# 0 = OK, 1 = HEJT, 2 = SCAM, 3 = GROOMING

def map_spam(example):
    # jesli spam (1) to zmienia na SCAM (2), jesli ham (0) zostawia (0)
    example["target"] = 2 if example["target"] == 1 else 0
    return example

def map_grooming(example):
    # jesli predator (1) to zmienia na GROOMING (3), jesli ok (0) zostawia (0)
    example["target"] = 3 if example["target"] == 1 else 0
    return example

# --- 1. ZBIÓR: HEJT (HEJT -> Klasa 1) ---
print("Ładowanie danych o hejcie (TweetEval)")
hejt_ds = load_dataset("tweet_eval", "hate", split="train")
hejt_ds = hejt_ds.rename_columns({"text": "sentence", "label": "target"})
hejt_ds = hejt_ds.select_columns(["sentence", "target"])

hejt_ds = hejt_ds.cast_column("target", Value("int64"))

# --- 2. ZBIÓR: WYŁUDZENIA (SCAM -> Klasa 2) ---
print("Ładowanie i mapowanie danych o wyłudzeniach (SMS Spam)")
spam_ds = load_dataset("sms_spam", split="train")
spam_ds = spam_ds.rename_columns({"sms": "sentence", "label": "target"})
spam_ds = spam_ds.select_columns(["sentence", "target"])

# zdejmujemy blokade klas, rzutujac na zwykla liczbe int64
spam_ds = spam_ds.cast_column("target", Value("int64"))
spam_ds = spam_ds.map(map_spam)

# --- 3. ZBIÓR: GROOMING (GROOMING -> Klasa 3) ---
print("Ładowanie i mapowanie danych o groomingu (PAN-12 CSV)")
groom_ds = load_dataset("csv", data_files=CSV_PATH, split="train")

groom_ds = groom_ds.cast_column("target", Value("int64"))
groom_ds = groom_ds.map(map_grooming)

# --- 4. CZYSZCZENIE I SKLEJANIE ---
print("Czyszczenie danych z pustych wierszy i wyrównywanie typów tekstu")
spam_ds = spam_ds.filter(lambda x: x["sentence"] is not None)
hejt_ds = hejt_ds.filter(lambda x: x["sentence"] is not None)
groom_ds = groom_ds.filter(lambda x: x["sentence"] is not None)

# rzutujemy teksty na string
spam_ds = spam_ds.cast_column("sentence", Value("string"))
hejt_ds = hejt_ds.cast_column("sentence", Value("string"))
groom_ds = groom_ds.cast_column("sentence", Value("string"))

print("Łączenie zbiorów w jeden autorski dataset...")
combined_ds = concatenate_datasets([spam_ds, hejt_ds, groom_ds])

# podział na train/test
print("Mieszanie i wydzielanie zbioru testowego (90% Train / 10% Test)")
combined_ds = combined_ds.shuffle(seed=42)
dataset = combined_ds.train_test_split(test_size=0.1)

print("\nStruktura zbioru POC:")
print(dataset)
print("\nPrzykład z bazy treningowej:")
przyklad = dataset['train'][0]
print(f"Tekst: {przyklad['sentence']}")
print(f"Etykieta (0=OK, 1=Zagrożenie): {przyklad['target']}")

"""
====================================================================================================================
"""
print("\n=== KROK 2: POBIERANIE SŁOWNIKA I TOKENIZACJA ===")
# model_name = "allegro/herbert-base-cased"
model_name = "roberta-base"
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
print("\n=== KROK 2.5: CZYSZCZENIE I BALANSOWANIE WIELOKLASOWE ===") 

train_df = tokenized_datasets["train"].to_pandas()

df_0 = train_df[train_df['target'] == 0] # OK
df_1 = train_df[train_df['target'] == 1] # HEJT
df_2 = train_df[train_df['target'] == 2] # SCAM
df_3 = train_df[train_df['target'] == 3] # GROOMING

print(f"Ilość przed balansem - OK: {len(df_0)}, HEJT: {len(df_1)}, SCAM: {len(df_2)}, GROOMING: {len(df_3)}")

TARGET_SAMPLES = 4000

df_0_sampled = df_0.sample(n=TARGET_SAMPLES, random_state=42, replace=(len(df_0) < TARGET_SAMPLES))
df_1_sampled = df_1.sample(n=TARGET_SAMPLES, random_state=42, replace=(len(df_1) < TARGET_SAMPLES))
df_2_sampled = df_2.sample(n=TARGET_SAMPLES, random_state=42, replace=(len(df_2) < TARGET_SAMPLES))
df_3_sampled = df_3.sample(n=TARGET_SAMPLES, random_state=42, replace=(len(df_3) < TARGET_SAMPLES))

balanced_train_df = pd.concat([df_0_sampled, df_1_sampled, df_2_sampled, df_3_sampled]).sample(frac=1, random_state=42)

tokenized_datasets["train"] = Dataset.from_pandas(balanced_train_df, preserve_index=False)

print(f"Zbiór treningowy: {len(tokenized_datasets['train'])} wierszy.")
tokenized_datasets["train"] = Dataset.from_pandas(balanced_train_df, preserve_index=False)

print(f"Train={len(tokenized_datasets['train'])}, Test={len(tokenized_datasets['test'])}")
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
model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=4, use_safetensors=True)
model.to(device)
"""
====================================================================================================================
"""
print("\n=== KROK 5: KONFIGURACJA TRENINGU ===")
training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,                              # gdzie zapisywać postępy
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

trainer.save_model(MODEL_PATH)
tokenizer.save_pretrained(MODEL_PATH)

print("Model jest gotowy")