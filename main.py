import time, os, json, sys
from datetime import date
from winotify import Notification, audio

from logix.state import (
    load_5min_log, load_1hr_log,
    save_log, FIVE_MIN_LOG, ONE_HR_LOG
)
from logix.rules import can_show_1hr
from logix.selector import select_5min_task, select_1hr_task
from logix.outcome import infer_last_outcome
from logix.event_log import log_event
import psutil
try:
    from ai_brain import rephrase_task
except ImportError:
    # This runs if 'ai_brain.py' is deleted or missing
    def rephrase_task(task_text):
        return task_text

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

# ─────────────────────────────────────────────
# 2. HANDLE EXPLICIT ACTIONS (Button Clicks)
# ─────────────────────────────────────────────
if action:
    # Small delay to ensure file handles are free
    time.sleep(0.5)
    
    log5 = load_5min_log()
    log1 = load_1hr_log()

    def record_action(log, log_path, csv_path, t_type, act):
        log["last_task_result"] = act
        save_log(log_path, log)
        log_event(
            csv_path,
            log.get("last_task", "Unknown Task"),
            "unknown",
            t_type,
            act,
            log.get("last_task_repeated", False)
        )
        print(f"✅ Recorded {act.upper()} for {t_type}")

    # Decision Logic
    if target_type == "1hr":
        record_action(log1, ONE_HR_LOG, "logs/1hr_history.csv", "1hr", action)
    elif target_type == "5min":
        record_action(log5, FIVE_MIN_LOG, "logs/5min_history.csv", "5min", action)
    else:
        # Fallback if type wasn't passed
        ts5 = log5.get("last_shown_ts", 0)
        ts1 = log1.get("last_shown_ts", 0)
        if ts1 > ts5:
            record_action(log1, ONE_HR_LOG, "logs/1hr_history.csv", "1hr", action)
        else:
            record_action(log5, FIVE_MIN_LOG, "logs/5min_history.csv", "5min", action)

    # Cleanup .bat files after execution to keep folder clean
    try:
        if os.path.exists("_act_done.bat"): os.remove("_act_done.bat")
        if os.path.exists("_act_skip.bat"): os.remove("_act_skip.bat")
    except:
        pass

    sys.exit(0)

# ─────────────────────────────────────────────
# 3. STANDARD RUN (Select & Show Task)
# ─────────────────────────────────────────────
time.sleep(2) # System settle
now_ts = int(time.time())
today = str(date.today())

# Mock Context (Replace with real sensors later)
# ─────────────────────────────────────────────
# REAL SENSORS (Replaces Mock Context)
# ─────────────────────────────────────────────
battery = psutil.sensors_battery()

# Desktop users might not have a battery, so we fallback to 100%
if battery:
    battery_percent = battery.percent
    is_plugged = battery.power_plugged
else:
    battery_percent = 100
    is_plugged = True

# Awake time is complex to get via Python cross-platform. 
# Keeping this mocked for now, or you can use `psutil.boot_time()` 
# to calculate system uptime instead of user awake time.
awake_seconds = 3 * 60 * 60

# Load Data
with open("tasks/tasks.json", "r", encoding="utf-8") as f:
    min_tasks = json.load(f)
with open("tasks/deeptasks.json", "r", encoding="utf-8") as f:
    deep_tasks = json.load(f)

log5 = load_5min_log()
log1 = load_1hr_log()

# Infer outcomes of previous ignored tasks
log5 = infer_last_outcome(log5, now_ts, "5min")
log1 = infer_last_outcome(log1, now_ts, "1hr")

# Daily Reset
if log5.get("last_date") != today:
    log5["daily_count"] = 0
    log5["last_date"] = today
if log1.get("last_date") != today:
    log1["daily_count"] = 0
    log1["last_date"] = today

# Select New Task
selected_type = "5min"
current_task = {}

if can_show_1hr(log1, now_ts, battery_percent, awake_seconds, log1.get("last_task_result")):
    selected_type = "1hr"
    current_task, log1 = select_1hr_task(deep_tasks, log1)
    
    log1["daily_count"] += 1
    log1["weekly_count"] += 1
    log1["last_shown_ts"] = now_ts
    log1["last_date"] = today
    log1["last_task_result"] = None
    
    save_log(ONE_HR_LOG, log1)
    log_event("logs/1hr_history.csv", current_task["text"], current_task["tag"], "1hr", "shown", False)
else:
    selected_type = "5min"
    current_task, log5 = select_5min_task(min_tasks, log5)
    
    log5["daily_count"] += 1
    log5["last_shown_ts"] = now_ts
    log5["last_date"] = today
    log5["last_task_result"] = None
    
    save_log(FIVE_MIN_LOG, log5)
    log_event("logs/5min_history.csv", current_task["text"], current_task["tag"], "5min", "shown", log5.get("last_task_repeated", False))

# ─────────────────────────────────────────────
# 4. NOTIFICATION WITH BAT WRAPPERS
# ─────────────────────────────────────────────
try:
    final_text = rephrase_task(current_task["text"])
except Exception:
    final_text = current_task["text"]

python = sys.executable
script = os.path.abspath(__file__)

# --- BAT FILE GENERATION (The Fix) ---
# We create temporary batch files to handle the command execution.
# This avoids all issues with spaces in paths and quotes in XML.

bat_done_content = f'@echo off\n"{python}" "{script}" --done --type {selected_type}'
bat_skip_content = f'@echo off\n"{python}" "{script}" --skip --type {selected_type}'

with open("_act_done.bat", "w") as f: f.write(bat_done_content)
with open("_act_skip.bat", "w") as f: f.write(bat_skip_content)

bat_done_path = os.path.abspath("_act_done.bat")
bat_skip_path = os.path.abspath("_act_skip.bat")
# -------------------------------------

toast = Notification(
    app_id="aalas-ka-hit",
    title="if you've got time",
    msg=final_text,
    duration="short"
)

# Launch the BAT files instead of raw python commands
toast.add_actions(label="Done", launch=bat_done_path)
toast.add_actions(label="Skip", launch=bat_skip_path)

toast.set_audio(audio.Default, loop=False)
toast.show()

time.sleep(2)