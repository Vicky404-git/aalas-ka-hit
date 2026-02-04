import time
import json
import sys
import os
from datetime import date
from winotify import Notification, audio

# ─────────────────────────────────────────────
# IMPORTS
# ─────────────────────────────────────────────
from logix.state import (
    load_5min_log,
    load_1hr_log,
    save_log,
    FIVE_MIN_LOG,
    ONE_HR_LOG
)
from logix.rules import can_show_1hr
from logix.selector import select_5min_task, select_1hr_task
from logix.outcome import infer_last_outcome
from logix.event_log import log_event

# ─────────────────────────────────────────────
# DEBUG CONFIG
# ─────────────────────────────────────────────
SIMULATE_STATE_WRITE = True   # Writes to JSON state files
SIMULATE_CSV_WRITE   = True   # Writes to CSV history
STARTUP_DELAY = 1

# ─────────────────────────────────────────────
# 1. PARSE ARGUMENTS
# ─────────────────────────────────────────────
action = None
target_type = None

if "--done" in sys.argv:
    action = "done"
elif "--skip" in sys.argv:
    action = "skipped"

if "--type" in sys.argv:
    try:
        idx = sys.argv.index("--type")
        target_type = sys.argv[idx + 1]
    except IndexError:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

print("\n🐞 DEBUG MODE STARTED")
print("=" * 60)

time.sleep(STARTUP_DELAY)

now_ts = int(time.time())
today = str(date.today())

print(f"⏱ Now TS : {now_ts}")
print(f"📅 Today : {today}")
print(f"🧪 CSV logging: {'ON' if SIMULATE_CSV_WRITE else 'OFF'}\n")

# ─────────────────────────────────────────────
# 2. HANDLE EXPLICIT ACTIONS (Button Clicks)
# ─────────────────────────────────────────────
if action:
    log5 = load_5min_log()
    log1 = load_1hr_log()

    # Helper to clean up code
    def record_debug_action(log, log_path, csv_path, t_type, act):
        log["last_task_result"] = act
        if SIMULATE_STATE_WRITE:
            save_log(log_path, log)
        
        if SIMULATE_CSV_WRITE:
            log_event(
                csv_path,
                log.get("last_task", "Unknown"),
                "unknown",
                t_type,
                act,
                log.get("last_task_repeated", False)
            )
        print(f"✔ Recorded {act.upper()} for {t_type}")

    # DECISION LOGIC: Use type if available, else fallback to timestamps
    if target_type == "1hr":
        record_debug_action(log1, ONE_HR_LOG, "logs/1hr_history.csv", "1hr", action)
    elif target_type == "5min":
        record_debug_action(log5, FIVE_MIN_LOG, "logs/5min_history.csv", "5min", action)
    else:
        # Fallback heuristic
        ts5 = log5.get("last_shown_ts", 0)
        ts1 = log1.get("last_shown_ts", 0)
        if ts1 > ts5:
            record_debug_action(log1, ONE_HR_LOG, "logs/1hr_history.csv", "1hr", action)
        else:
            record_debug_action(log5, FIVE_MIN_LOG, "logs/5min_history.csv", "5min", action)

    # Cleanup temporary bat files
    try:
        if os.path.exists("_debug_done.bat"): os.remove("_debug_done.bat")
        if os.path.exists("_debug_skip.bat"): os.remove("_debug_skip.bat")
    except:
        pass

    print("\n🐞 DEBUG MODE END")
    print("=" * 60)
    sys.exit(0)

# ─────────────────────────────────────────────
# 3. STANDARD RUN (Load Logs & Show State)
# ─────────────────────────────────────────────
log5 = load_5min_log()
log1 = load_1hr_log()

print("📦 5-MIN LOG:")
print(json.dumps(log5, indent=2), "\n")

print("📦 1-HR LOG:")
print(json.dumps(log1, indent=2), "\n")

# Infer outcomes
log5 = infer_last_outcome(log5, now_ts, "5min", log_to_csv=SIMULATE_CSV_WRITE)
log1 = infer_last_outcome(log1, now_ts, "1hr", log_to_csv=SIMULATE_CSV_WRITE)

# Mock Context
battery_percent = 80
awake_seconds = 3 * 60 * 60

# ─────────────────────────────────────────────
# 4. DECIDE TASK TYPE
# ─────────────────────────────────────────────
selected_type = "5min"
can_1hr = can_show_1hr(
    log1,
    now_ts,
    battery_percent,
    awake_seconds,
    log1.get("last_task_result")
)

if can_1hr:
    print("🎯 1-hour task WOULD be shown\n")
    selected_type = "1hr"

    with open("tasks/deeptasks.json", "r", encoding="utf-8") as f:
        deep_tasks = json.load(f)

    task, log1 = select_1hr_task(deep_tasks, log1)

    log1["last_shown_ts"] = now_ts
    log1["daily_count"] += 1
    log1["weekly_count"] += 1
    log1["last_date"] = today

    if SIMULATE_STATE_WRITE:
        save_log(ONE_HR_LOG, log1)

    if SIMULATE_CSV_WRITE:
        log_event("logs/1hr_history.csv", task["text"], task["tag"], "1hr", "shown", False)

    title = "DEBUG: 1-hour task"

else:
    print("⛔ 1-hour blocked → fallback 5-min\n")
    selected_type = "5min"

    with open("tasks/tasks.json", "r", encoding="utf-8") as f:
        min_tasks = json.load(f)

    task, log5 = select_5min_task(min_tasks, log5)

    log5["last_shown_ts"] = now_ts
    log5["daily_count"] += 1
    log5["last_date"] = today

    if SIMULATE_STATE_WRITE:
        save_log(FIVE_MIN_LOG, log5)

    if SIMULATE_CSV_WRITE:
        log_event("logs/5min_history.csv", task["text"], task["tag"], "5min", "shown", log5.get("last_task_repeated", False))

    title = "DEBUG: 5-minute task"

# ─────────────────────────────────────────────
# 5. SHOW NOTIFICATION (WITH BAT FIX)
# ─────────────────────────────────────────────
python = sys.executable
script = os.path.abspath(__file__)

# --- BAT FILE GENERATION ---
# Creates temporary batch files to handle the click securely
bat_done_content = f'@echo off\n"{python}" "{script}" --done --type {selected_type}'
bat_skip_content = f'@echo off\n"{python}" "{script}" --skip --type {selected_type}'

with open("_debug_done.bat", "w") as f: f.write(bat_done_content)
with open("_debug_skip.bat", "w") as f: f.write(bat_skip_content)

bat_done_path = os.path.abspath("_debug_done.bat")
bat_skip_path = os.path.abspath("_debug_skip.bat")
# ---------------------------

toast = Notification(
    app_id="aalas-ka-hit (DEBUG)",
    title=title,
    msg=task["text"],
    duration="short"
)

# Launch the BAT files instead of raw python commands
toast.add_actions(label="Done", launch=bat_done_path)
toast.add_actions(label="Skip", launch=bat_skip_path)

toast.set_audio(audio.Default, loop=False)
toast.show()

time.sleep(2)

print("📣 Notification sent")
print("\n🐞 DEBUG MODE END")
print("=" * 60)