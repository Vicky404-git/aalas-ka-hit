import os
import json
import numpy as np
from memory.window import get_last_full_week_range
from sentence_transformers import SentenceTransformer

MODEL = SentenceTransformer("all-MiniLM-L6-v2")
CACHE_DIR = "memory/_cache"
os.makedirs(CACHE_DIR, exist_ok=True)
import csv

def load_csv_range(start_ts, end_ts):
    """
    Load rows from both history CSVs within a timestamp range.
    """
    rows = []
    paths = [
        "logs/5min_history.csv",
        "logs/1hr_history.csv"
    ]

    for path in paths:
        if not os.path.exists(path):
            continue

        with open(path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    ts = int(row["timestamp"])
                except (KeyError, ValueError):
                    continue

                if start_ts <= ts <= end_ts:
                    rows.append(row)

    return rows


def get_memory_context(query, mode="rolling", k=3):
    """
    mode:
      - 'rolling' → last 7 days (no cache)
      - 'weekly'  → last full week (cached)
    """

    texts = load_texts(mode)
    if not texts:
        return ""

    if mode == "weekly":
        cache_key = get_week_key()
        emb_path = f"{CACHE_DIR}/{cache_key}.npy"
        txt_path = f"{CACHE_DIR}/{cache_key}.json"

        if os.path.exists(emb_path) and os.path.exists(txt_path):
            embeddings = np.load(emb_path)
            with open(txt_path, "r") as f:
                texts = json.load(f)
        else:
            embeddings = MODEL.encode(texts)
            np.save(emb_path, embeddings)
            with open(txt_path, "w") as f:
                json.dump(texts, f)
    else:
        embeddings = MODEL.encode(texts)

    q_emb = MODEL.encode([query])[0]
    scores = np.dot(embeddings, q_emb)
    top = scores.argsort()[-k:][::-1]

    return " | ".join(texts[i] for i in top)


def get_week_key():
    from datetime import date
    y, w, _ = date.today().isocalendar()
    return f"week_{y}_{w}"


def load_texts(mode):
    from memory.window import load_last_7_days, get_last_full_week_range

    rows = []
    if mode == "weekly":
        start, end = get_last_full_week_range()
        rows = load_csv_range(start, end)
    else:
        rows = load_last_7_days()

    return [
        f"Task: {r['task']} | Time: {r['time']} | Outcome: {r['status']}"
        for r in rows
    ]
