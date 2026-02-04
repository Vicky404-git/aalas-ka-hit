import time
import sys
import os
from datetime import date
from winotify import Notification, audio

# ─────────────────────────────────────────────
# IMPORTS (Aligned with modular structure)
# ─────────────────────────────────────────────
from logix.state import (
    load_5min_log,
    load_1hr_log,
    save_log,
    load_tasks,      # <--- Now using the shared loader
    FIVE_MIN_LOG,
    ONE_HR_LOG
)
from logix.rules import can_show_1hr
from logix.selector import select_5min_task, select_1hr_task
from logix.outcome import infer_last_outcome, update_tag_scores
from logix.event_log import log_event

# ─────────────────────────────────────────────
# DEBUG CONFIGURATION
# ─────────────────────────────────────────────
SIMULATE_STATE_WRITE = True   # Set False to run without saving changes to JSON
SIMULATE_CSV_WRITE   = True   # Set False to avoid CSV logging
STARTUP_DELAY        = 1

# MOCK SENSORS (Change these to test rules)
MOCK_BATTERY     = 80            # %
MOCK_AWAKE_HOURS = 3             # Hours (Needs > 2 for Deep Tasks)

# ─────────────────────────────────────────────
# 1. SETUP & PARSE ARGUMENTS
# ─────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

print("\n🐞 DEBUG MODE STARTED")
print("=" * 60)

# Parse CLI flags
action = "done" if "--done" in sys.argv else "skipped" if "--skip" in sys.argv else None
target_type = None
if "--type" in sys.argv:
    try:
        target_type = sys.argv[sys.argv.index("--type") + 1]
    except IndexError:
        pass

time.sleep(STARTUP_DELAY)
now_ts = int(time.time())
today = str(date.today())

print(f"⏱  Now Timestamp : {now_ts}")
print(f"📅 Today         : {today}")
print(f"💾 Write Mode    : {'ENABLED' if SIMULATE_STATE_WRITE else 'READ-ONLY'}")
print(f"🔋 Mock Battery  : {MOCK_BATTERY}%")
print(f"⏰ Mock Awake    : {MOCK_AWAKE_HOURS}h\n")

# ─────────────────────────────────────────────
# 2. HANDLE ACTIONS (Done/Skip Logic)
# ─────────────────────────────────────────────
if action:
    print(f"⚡ ACTION RECEIVED: {action.upper()} on {target_type}")
    
    log5 = load_5min_log()
    log1 = load_1hr_log()

    # We manually replicate 'process_user_action' here to respect SIMULATE flags
    def record_debug_action(log, log_path, csv_path, t_type, act):
        # 1. Apply Learning (Score Update)
        last_tag = log.get("last_tag", "unknown")
        mock_task = {"tag": last_tag}
        
        update_tag_scores(log, mock_task, act)
        print(f"   └─ 🧠 Learning updated for tag: '{last_tag}'")

        # 2. Update Result
        log["last_task_result"] = act
        
        # 3. Track Skips
        if act == "skipped" and t_type == "5min":
            log["ignored_today"] = log.get("ignored_today", 0) + 1
            print(f"   └─ ⚠️ Ignored count: {log['ignored_today']}")

        # 4. Save (If enabled)
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
        print(f"✔ Saved state for {t_type}")

    if target_type == "1hr":
        record_debug_action(log1, ONE_HR_LOG, "logs/1hr_history.csv", "1hr", action)
    elif target_type == "5min":
        record_debug_action(log5, FIVE_MIN_LOG, "logs/5min_history.csv", "5min", action)
    else:
        print("❌ Error: No type specified for action.")

    # Cleanup .bat files
    for f in ["_act_done.bat", "_act_skip.bat", "_debug_done.bat", "_debug_skip.bat"]:
        if os.path.exists(f): os.remove(f)

    print("\n🐞 DEBUG ACTION FINISHED")
    sys.exit(0)

# ─────────────────────────────────────────────
# 3. STANDARD RUN (Task Selection)
# ─────────────────────────────────────────────
log5 = load_5min_log()
log1 = load_1hr_log()

print("📦 CURRENT STATE LOADED")
# Infer outcomes
log5 = infer_last_outcome(log5, now_ts, "5min", log_to_csv=SIMULATE_CSV_WRITE)
log1 = infer_last_outcome(log1, now_ts, "1hr", log_to_csv=SIMULATE_CSV_WRITE)

# ─────────────────────────────────────────────
# 4. DECIDE TASK TYPE
# ─────────────────────────────────────────────
selected_type = "5min"
can_1hr = can_show_1hr(
    log1,
    now_ts,
    MOCK_BATTERY,
    MOCK_AWAKE_HOURS * 3600,
    log1.get("last_task_result")
)

if can_1hr:
    print("\n🎯 DECISION: Show 1-HOUR Task")
    selected_type = "1hr"
    
    tasks = load_tasks("tasks/deeptasks.json") # Using new loader
    task, log1 = select_1hr_task(tasks, log1)

    # CRITICAL UPDATES
    log1["daily_count"] += 1
    log1["weekly_count"] = log1.get("weekly_count", 0) + 1
    log1["last_shown_ts"] = now_ts
    log1["last_date"] = today
    log1["last_tag"] = task.get("tag", "deep")
    log1["last_task_result"] = None

    if SIMULATE_STATE_WRITE: save_log(ONE_HR_LOG, log1)
    if SIMULATE_CSV_WRITE:   log_event("logs/1hr_history.csv", task["text"], task.get("tag"), "1hr", "shown")

else:
    print("\n⚡ DECISION: Show 5-MIN Task")
    selected_type = "5min"
    
    tasks = load_tasks("tasks/tasks.json") # Using new loader
    task, log5 = select_5min_task(tasks, log5)

    # CRITICAL UPDATES
    log5["daily_count"] += 1
    log5["last_shown_ts"] = now_ts
    log5["last_date"] = today
    log5["last_tag"] = task.get("tag", "quick")
    log5["last_task_result"] = None

    if SIMULATE_STATE_WRITE: save_log(FIVE_MIN_LOG, log5)
    if SIMULATE_CSV_WRITE:   log_event("logs/5min_history.csv", task["text"], task.get("tag"), "5min", "shown", log5.get("last_task_repeated", False))

print(f"   ├─ Task: {task['text']}")
print(f"   └─ Tag : {task.get('tag')}")

# ─────────────────────────────────────────────
# 5. SEND NOTIFICATION
# ─────────────────────────────────────────────
python = sys.executable
script = os.path.abspath(__file__)

# Generate debug .bat files
bat_done_content = f'@echo off\n"{python}" "{script}" --done --type {selected_type}'
bat_skip_content = f'@echo off\n"{python}" "{script}" --skip --type {selected_type}'

with open("_debug_done.bat", "w") as f: f.write(bat_done_content)
with open("_debug_skip.bat", "w") as f: f.write(bat_skip_content)

toast = Notification(
    app_id="aalas-ka-hit (DEBUG)",
    title=f"DEBUG: {selected_type} task",
    msg=task["text"],
    duration="short"
)

toast.add_actions(label="Done", launch=os.path.abspath("_debug_done.bat"))
toast.add_actions(label="Skip", launch=os.path.abspath("_debug_skip.bat"))

toast.set_audio(audio.Default, loop=False)
toast.show()

print("\n📣 Notification Sent. Waiting for interaction...")
print("=" * 60)