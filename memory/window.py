import csv
import time
from datetime import datetime, timedelta

WINDOW_SEC = 7 * 24 * 60 * 60  # 7 days

def load_last_7_days(csv_path):
    cutoff = time.time() - WINDOW_SEC
    rows = []

    try:
        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if int(row["timestamp"]) >= cutoff:
                    rows.append(row)
    except FileNotFoundError:
        pass

    return rows

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
