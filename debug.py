import json
import time
import os
from datetime import date
from winotify import Notification, audio

from logix import select_task, wait_for_network
from ai_brain import rephrase_task


# --- HARDEN PATHS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

print("🐞 DEBUG MODE STARTED")

now = int(time.time())
today = str(date.today())

print("⏱ Now (ts):", now)
print("📅 Today:", today)

# --- LOAD TASKS ---
with open("tasks/tasks.json", "r", encoding="utf-8") as f:
    tasks = json.load(f)

print(f"✅ Loaded {len(tasks)} tasks")

# --- LOAD STATE ---
with open("logs/state.json", "r", encoding="utf-8") as f:
    state = json.load(f)

print("📦 Initial state:")
print(json.dumps(state, indent=2))

# --- TEST DAILY RESET ---
if state.get("last_date") != today:
    print("🔁 New day detected → resetting daily counters")
    state["daily_5min_count"] = 0
    state["daily_1hr_count"] = 0
    state["last_date"] = today

# --- SELECT TASK ---
base_task = select_task(tasks)
print("🎯 Base task selected:", base_task)

# reload state (select_task modifies it)
with open("logs/state.json", "r", encoding="utf-8") as f:
    state = json.load(f)

print("📦 State after select_task:")
print(json.dumps(state, indent=2))

# --- NETWORK CHECK ---
network_ok = wait_for_network(timeout=10)
print("🌐 Network available:", network_ok)

# --- AI REPHRASE ---
if network_ok:
    final_task = rephrase_task(base_task)
    print("🧠 AI rephrased task:", final_task)
else:
    final_task = base_task
    print("⚠️ AI skipped, using base task")

# --- SHOW NOTIFICATION ---
toast = Notification(
    app_id="Tiny Task Debug",
    title="DEBUG: If you’ve got 3 minutes",
    msg=final_task,
    duration="long"
)

toast.set_audio(audio.Default, loop=False)
toast.show()
print("📣 Notification sent")

# --- SIMULATE STATE UPDATE ---
state["daily_5min_count"] = state.get("daily_5min_count", 0) + 1
state["last_shown_ts"] = now

with open("logs/state.json", "w", encoding="utf-8") as f:
    json.dump(state, f, indent=2)

print("💾 State after debug run:")
print(json.dumps(state, indent=2))

print("🐞 DEBUG MODE END")
