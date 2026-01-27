import json
import time
import os
from datetime import date
from winotify import Notification, audio

from logix import select_task, wait_for_network
from ai_brain import rephrase_task
import subprocess

# --- HARDEN PATHS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

# --- STARTUP DELAY ---
time.sleep(3)  # later: 300

# --- CONSTANTS ---
MIN_GAP = 30 * 60
MAX_5MIN_PER_DAY = 6

now = int(time.time())
today = str(date.today())

# --- LOAD TASKS ---
with open("tasks/tasks.json", "r", encoding="utf-8") as f:
    tasks = json.load(f)

# --- LOAD STATE ---
with open("logs/state.json", "r", encoding="utf-8") as f:
    state = json.load(f)

# --- WAKE / SLEEP SPAM GUARD ---
if now - state.get("last_shown_ts", 0) < MIN_GAP:
    exit()

# --- DAILY RESET ---
if state.get("last_date") != today:
    state["daily_5min_count"] = 0
    state["daily_1hr_count"] = 0
    state["last_date"] = today

    # save reset immediately
    with open("logs/state.json", "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

# --- DAILY QUOTA GUARD ---
if state.get("daily_5min_count", 0) >= MAX_5MIN_PER_DAY:
    exit()

# --- SELECT TASK ---
base_task = select_task(tasks)

# reload state (select_task updated it)
with open("logs/state.json", "r", encoding="utf-8") as f:
    state = json.load(f)

# --- AI (OPTIONAL) ---
network_ok = wait_for_network()
final_task = rephrase_task(base_task) if network_ok else base_task

# --- SHOW NOTIFICATION ---
toast = Notification(
    app_id="Tiny Task",
    title="If you’ve got 3 minutes",
    msg=final_task,
    duration="short"
)

toast.set_audio(audio.Default, loop=False)
toast.show()

# --- UPDATE STATE ---
state["daily_5min_count"] += 1
state["last_shown_ts"] = now

with open("logs/state.json", "w", encoding="utf-8") as f:
    json.dump(state, f, indent=2)


# --- LOG ---
# Run debug.py
subprocess.run(["python", "debug.py"], check=True)

