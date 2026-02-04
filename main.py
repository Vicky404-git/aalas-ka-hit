import os
import sys
import time
from datetime import date
from pathlib import Path
from winotify import Notification, audio

from logix.state import (
    load_5min_log, load_1hr_log, save_log, load_tasks,
    FIVE_MIN_LOG, ONE_HR_LOG
)
from logix.rules import can_show_1hr, get_system_stats
from logix.selector import select_5min_task, select_1hr_task
from logix.outcome import infer_last_outcome, process_user_action
from logix.event_log import log_event

try:
    from ai_brain import rephrase_task
except ImportError:
    def rephrase_task(t): return t

MAX_IGNORES = 3
BASE_DIR = Path(__file__).parent
os.chdir(BASE_DIR)
print("NO WORRIES AALAS-ka -HIT is working; HELL YEAA \n and saving ")



def main():
    # 1. HANDLE BUTTON CLICKS
    action = "done" if "--done" in sys.argv else "skipped" if "--skip" in sys.argv else None
    target_type = sys.argv[sys.argv.index("--type") + 1] if "--type" in sys.argv else None
    
    if action:
        time.sleep(0.5)
        process_user_action(load_1hr_log(), load_5min_log(), action, target_type)
        # Cleanup
        for f in ["_act_done.bat", "_act_skip.bat"]:
            if os.path.exists(f): os.remove(f)
            
        sys.exit(0)

    # 2. STANDARD RUN
    time.sleep(2)
    now_ts = int(time.time())
    today = str(date.today())

    #log5 = load_5min_log()
    #log1 = load_1hr_log()

    log1, log5 = process_user_action(
    load_1hr_log(), load_5min_log(), action, target_type
)


    # Silent Mode Check
    silent_until = log5.get("silent_until") or log1.get("silent_until")
    if silent_until and now_ts < silent_until:
        sys.exit(0)

    # Infer Outcomes & Reset Daily Stats
    log5 = infer_last_outcome(log5, now_ts, "5min")
    log1 = infer_last_outcome(log1, now_ts, "1hr")

    for log in [log5, log1]:
        if log.get("last_date") != today:
            log.update({"daily_count": 0, "ignored_today": 0, "last_date": today})

    # Burnout Check
    if log5.get("ignored_today", 0) >= MAX_IGNORES:
        silence_ts = now_ts + (8 * 60 * 60)
        log5["silent_until"] = silence_ts
        log1["silent_until"] = silence_ts
        save_log(FIVE_MIN_LOG, log5)
        save_log(ONE_HR_LOG, log1)
        sys.exit(0)

    # 3. SELECT TASK
    bat_pc, awake_sec = get_system_stats()
    
    if can_show_1hr(log1, now_ts, bat_pc, awake_sec, log1.get("last_task_result")):
        selected_type = "1hr"
        tasks = load_tasks(BASE_DIR / "tasks" / "deeptasks.json")
        current_task, log1 = select_1hr_task(tasks, log1)
        
        log1.update({
            "daily_count": log1["daily_count"] + 1,
            "weekly_count": log1.get("weekly_count", 0) + 1,
            "last_shown_ts": now_ts,
            "last_task_result": None,
            "last_tag": current_task.get("tag", "deep")
        })
        save_log(ONE_HR_LOG, log1)
        log_event("logs/1hr_history.csv", current_task["text"], current_task.get("tag"), "1hr", "shown")
    else:
        selected_type = "5min"
        tasks = load_tasks(BASE_DIR / "tasks" / "tasks.json")
        current_task, log5 = select_5min_task(tasks, log5)
        
        log5.update({
            "daily_count": log5["daily_count"] + 1,
            "last_shown_ts": now_ts,
            "last_task_result": None,
            "last_tag": current_task.get("tag", "quick")
        })
        save_log(FIVE_MIN_LOG, log5)
        log_event("logs/5min_history.csv", current_task["text"], current_task.get("tag"), "5min", "shown", log5.get("last_task_repeated", False))

    # 4. SHOW NOTIFICATION
    final_text = rephrase_task(current_task["text"])
    python = sys.executable
    script = os.path.abspath(__file__)

    # Create temporary callback scripts
    for act in ["done", "skip"]:
        with open(f"_act_{act}.bat", "w") as f:
            f.write(f'@echo off\n"{python}" "{script}" --{act} --type {selected_type}')

    toast = Notification(app_id="aalas-ka-hit", title="if you've got time", msg=final_text, duration="short")
    toast.add_actions(label="Done", launch=os.path.abspath("_act_done.bat"))
    toast.add_actions(label="Skip", launch=os.path.abspath("_act_skip.bat"))
    toast.set_audio(audio.Default, loop=False)
    toast.show()
    time.sleep(5)


if __name__ == "__main__":
    main()