from datasets import load_dataset, Dataset, concatenate_datasets, Value
import pandas as pd
import torch
import numpy as np
import evaluate
from transformers import AutoTokenizer, AutoModelForSequenceClassification, TrainingArguments, Trainer, EarlyStoppingCallback
from torch.utils.data import DataLoader, WeightedRandomSampler
from config import MODEL_PATH, OUTPUT_DIR, CB_CSV_PATH, SPAM_CSV_PATH, TOXIC_CSV_PATH, GROOMING_CSV_PATH
from sklearn.metrics import f1_score, precision_score, recall_score

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


# dataset = load_dataset("ptaszynski/cdt")                                
#   ta funkcja domyslnie laczy sie z hugging face zeby pobrac wskazany dataset                                
#   https://huggingface.co/datasets/ptaszynski/cdt
#   mozna tez lokalnie zczytywac np. load_dataset("csv", data_files="dane.csv")

print("=== KROK 1: BUDOWA ZBIORU DANYCH ===")
"""
                --- LOGIKA MAPOWANIA KLAS ---
                        0 = OK, 
                        1 = HEJT I CYBERBULLYING (TOXIC), 
                        2 = SCAM, 
                        3 = GROOMING
"""

"""
    ============= PRZYJĘTA STRUKTURA DATASETÓW =============
                    SENTENCE  |   TARGET
    --------------------------------------------------------
                    (String)  |   (Int32)
    --------------------------------------------------------
                "sample text" |   (0, 1, 2, 3)

"""

def map_spam(example):
    example["target"] = 2 if example["target"] == 1 else 0
    return example

def map_grooming(example):
    example["target"] = 3 if example["target"] == 1 else 0
    return example

# def map_cb(example):
#     example["target"] = 4 if example["target"] == 1 else 0
#     return example

# --- 2. ZBIÓR: TOXIC (HEJT + CYBERBULLYING) (TOXIC -> Klasa 1) ---
print("Ładowanie danych o hejcie (Jigsaw Toxic)")
hejt_ds = load_dataset("csv", data_files=TOXIC_CSV_PATH, split="train")
hejt_ds = hejt_ds.cast_column("target", Value("int64"))

print("Ładowanie i mapowanie danych o cyberbullyingu (Cyberbullying Classification)")
cb_ds = load_dataset("csv", data_files=CB_CSV_PATH, split="train")
cb_ds = cb_ds.cast_column("target", Value("int64"))

# --- 2. ZBIÓR: WYŁUDZENIA (SCAM -> Klasa 2) ---
print("Ładowanie i mapowanie danych o wyłudzeniach (SMS Spam)")
spam_ds = load_dataset("csv", data_files=SPAM_CSV_PATH, split="train")
spam_ds = spam_ds.cast_column("target", Value("int64"))
spam_ds = spam_ds.map(map_spam)

# --- 3. ZBIÓR: GROOMING (GROOMING -> Klasa 3) ---
print("Ładowanie i mapowanie danych o groomingu (PAN-12 CSV)")
groom_ds = load_dataset("csv", data_files=GROOMING_CSV_PATH, split="train")
groom_ds = groom_ds.cast_column("target", Value("int64"))
groom_ds = groom_ds.map(map_grooming)


# --- 4. CZYSZCZENIE I SKLEJANIE ---
print("Czyszczenie danych z pustych wierszy i wyrównywanie typów tekstu")
spam_ds = spam_ds.filter(lambda x: x["sentence"] is not None)
hejt_ds = hejt_ds.filter(lambda x: x["sentence"] is not None)
groom_ds = groom_ds.filter(lambda x: x["sentence"] is not None)
cb_ds = cb_ds.filter(lambda x: x["sentence"] is not None)

# rzutujemy teksty na string
spam_ds = spam_ds.cast_column("sentence", Value("string"))
hejt_ds = hejt_ds.cast_column("sentence", Value("string"))
groom_ds = groom_ds.cast_column("sentence", Value("string"))
cb_ds = cb_ds.cast_column("sentence", Value("string"))

print("Łączenie zbiorów...")
combined_ds = concatenate_datasets([spam_ds, hejt_ds, groom_ds, cb_ds])

# podział na train/test
print("Mieszanie i wydzielanie zbioru testowego")
combined_ds = combined_ds.shuffle(seed=42)
dataset = combined_ds.train_test_split(test_size=0.2)


print("=== KROK 2: POBIERANIE SŁOWNIKA I TOKENIZACJA ===")
# model_name = "allegro/herbert-base-cased"
model_name = "roberta-base"
print(f"Pobieranie tokenizatora dla modelu: {model_name}...")

# Pobieramy słownik z chmury
tokenizer = AutoTokenizer.from_pretrained(model_name)

# --- WŁAŚCIWA TOKENIZACJA CAŁEJ BAZY ---
print(f"Przetwarzanie (tokenizacja) całych {len(combined_ds)} tekstów...")

def tokenize_function(examples):
    return tokenizer(examples["sentence"], padding="max_length", truncation=True, max_length=128)

tokenized_datasets = dataset.map(tokenize_function, batched=True)

print("Zbiór danych został ztokenizowany i jest gotowy do wstrzyknięcia do modelu")

print("=== KROK 2.5: CZYSZCZENIE I BALANSOWANIE WIELOKLASOWE ===") 

train_df = tokenized_datasets["train"].to_pandas()

df_0 = train_df[train_df['target'] == 0] # OK
df_1 = train_df[train_df['target'] == 1] # TOXIC (HEJT I CYBERBULLYING)
df_2 = train_df[train_df['target'] == 2] # SCAM
df_3 = train_df[train_df['target'] == 3] # GROOMING
# df_4 = train_df[train_df['target'] == 4] # CYBERBULLYING

print(f"Ilość przed balansem - OK: {len(df_0)}, TOXIC: {len(df_1)}, SCAM: {len(df_2)}, GROOMING: {len(df_3)}")

TARGET_SAMPLES = 150000

df_0_sampled = df_0.sample(n=TARGET_SAMPLES, random_state=42, replace=(len(df_0) < TARGET_SAMPLES))
df_1_sampled = df_1
df_2_sampled = df_2
df_3_sampled = df_3
# df_4_sampled = df_4

balanced_train_df = pd.concat([df_0_sampled, df_1_sampled, df_2_sampled, df_3_sampled]).sample(frac=1, random_state=42)

tokenized_datasets["train"] = Dataset.from_pandas(balanced_train_df, preserve_index=False)

print(f"Zbiór treningowy: {len(tokenized_datasets['train'])} wierszy.")
tokenized_datasets["train"] = Dataset.from_pandas(balanced_train_df, preserve_index=False)

print(f"Train={len(tokenized_datasets['train'])}, Test={len(tokenized_datasets['test'])}")


print("=== KROK 3: FORMATOWANIE DANYCH DLA KARTY GRAFICZNEJ (MULTI-LABEL) ===")

def convert_to_multilabel(examples):
    multilabel_list = []
    for t in examples["target"]:
        # Wektor: [TOXIC, SCAM, GROOMING]. Jeśli 0 (OK), zostają same zera.
        vec = [0.0, 0.0, 0.0]
        if t == 1: vec[0] = 1.0
        elif t == 2: vec[1] = 1.0
        elif t == 3: vec[2] = 1.0
        # elif t == 4: vec[3] = 1.0
        multilabel_list.append(vec)
    return {"labels": multilabel_list}

tokenized_datasets["train"] = tokenized_datasets["train"].map(convert_to_multilabel, batched=True)
tokenized_datasets["test"] = tokenized_datasets["test"].map(convert_to_multilabel, batched=True)

# Usuwamy stare kolumny i ustawiamy format pod PyTorcha
tokenized_datasets = tokenized_datasets.remove_columns(["sentence", "target"])
tokenized_datasets.set_format("torch")


print("=== KROK 4: POBRANIE MODELU ===")
model = AutoModelForSequenceClassification.from_pretrained(
    model_name, 
    num_labels=3, 
    problem_type="multi_label_classification", 
    use_safetensors=True
)
model.to(device)


print("=== KROK 5: KONFIGURACJA TRENINGU ===")
training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,                              # gdzie zapisywać postępy
    eval_strategy="epoch",                              # po każdej epoce model jest ewaluowany
    save_strategy="epoch",                              # do epokę zapisywane jest postęp
    learning_rate=2e-5,                                 # prędkość nauki
    per_device_train_batch_size=16,                     # ile próbek na raz ładowane jest do VRAM karty do treningu
    per_device_eval_batch_size=8,                       # ile próbek na raz ładowane jest do VRAM karty do ewaluacji
    num_train_epochs=10,                                # ile razy model przeczyta całą książkę
    weight_decay=0.1,
    logging_strategy="steps",
    logging_steps=50,
    report_to="tensorboard",
    load_best_model_at_end=True,
    metric_for_best_model="f1_macro",
    lr_scheduler_type="cosine",
    warmup_steps=500
)

# Narzędzie do sprawdzania skuteczności
metric = evaluate.load("accuracy")

def compute_metrics(eval_pred):
    logits, labels = eval_pred
    probs = 1 / (1 + np.exp(-logits))
    predictions = (probs >= 0.75).astype(int)
    
    return {
        "f1_macro": f1_score(labels, predictions, average="macro", zero_division=0),
        "precision": precision_score(labels, predictions, average="macro", zero_division=0),
        "recall": recall_score(labels, predictions, average="macro", zero_division=0)
    }

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_datasets["train"],
    eval_dataset=tokenized_datasets["test"],
    compute_metrics=compute_metrics,
    callbacks=[EarlyStoppingCallback(early_stopping_patience=1)]
)


print("=== KROK 6: TRENING I ZAPISYWANIE MODELU ===")
print("ROZPOCZĘCIE FINE TUNINGU...)")
trainer.train()

trainer.save_model(MODEL_PATH)
tokenizer.save_pretrained(MODEL_PATH)

print("Model jest gotowy")