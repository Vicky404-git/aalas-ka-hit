import csv
import os
import time
from datetime import datetime, timedelta

# --- constants ---
WINDOW_SEC = 7 * 24 * 60 * 60  # 7 days
LOG_PATHS = [
    "logs/5min_history.csv",
    "logs/1hr_history.csv",
]

# --------------------------------------------------
# Single-CSV helper (kept for compatibility)
# --------------------------------------------------
def load_last_7_days(csv_path):
    """
    Load rows from a single CSV from the last 7 days.
    """
    cutoff = time.time() - WINDOW_SEC
    rows = []

    try:
        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    if int(row["timestamp"]) >= cutoff:
                        rows.append(row)
                except (KeyError, ValueError):
                    continue
    except FileNotFoundError:
        pass

    return rows


# --------------------------------------------------
# Aggregated helper (USED BY RAG)
# --------------------------------------------------
def load_last_7_days_all():
    """
    Load rows from all history CSVs from the last 7 days.
    """
    cutoff = time.time() - WINDOW_SEC
    rows = []

    for path in LOG_PATHS:
        if not os.path.exists(path):
            continue

        with open(path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    ts = int(row["timestamp"])
                except (KeyError, ValueError):
                    continue

                if ts >= cutoff:
                    rows.append(row)

    return rows


# --------------------------------------------------
# Weekly window helper
# --------------------------------------------------
def get_last_full_week_range(today=None):
    """
    Returns (start_ts, end_ts) for last full Mon–Sun week.
    """
    today = today or datetime.now()

    last_sunday = today - timedelta(days=today.weekday() + 1)
    last_sunday = last_sunday.replace(hour=23, minute=59, second=59)

    last_monday = last_sunday - timedelta(days=6)
    last_monday = last_monday.replace(hour=0, minute=0, second=0)

    return int(last_monday.timestamp()), int(last_sunday.timestamp())
