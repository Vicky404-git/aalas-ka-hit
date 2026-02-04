import json
import os
from datetime import date, timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, "logs")

FIVE_MIN_LOG = os.path.join(LOG_DIR, "5min.json")
ONE_HR_LOG = os.path.join(LOG_DIR, "1hr.json")

# --- MOVED FROM MAIN.PY ---
def load_tasks(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_log(path, default):
    if not os.path.exists(path):
        return default.copy()
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_log(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def get_week_start(d=None):
    d = d or date.today()
    return str(d - timedelta(days=d.weekday()))

def normalize_1hr_week(log):
    current_week = get_week_start()
    if log.get("week_start") != current_week:
        log["week_start"] = current_week
        log["weekly_count"] = 0
    return log

def load_5min_log():
    return load_log(FIVE_MIN_LOG, {
        "last_date": "",
        "last_shown_ts": 0,
        "daily_count": 0,
        "recent_tasks": [],
        "recent_tags": [],
        "last_task": None,
        "last_task_result": "unknown",
        "ignored_today": 0,
        "tag_scores": {}

    })

def load_1hr_log():
    log = load_log(ONE_HR_LOG, {
        "last_date": "",
        "week_start": "",
        "last_shown_ts": 0,
        "daily_count": 0,
        "weekly_count": 0,
        "recent_tasks": [],
        "last_task": None,
        "last_task_result": "unknown"
    })
    return normalize_1hr_week(log)