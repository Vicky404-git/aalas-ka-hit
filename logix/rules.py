from datetime import datetime, date, timedelta
import psutil
import time

def get_week_start(d=None):
    d = d or date.today()
    return str(d - timedelta(days=d.weekday()))

def is_weekend(now=None):
    now = now or datetime.now()
    return now.weekday() >= 5  # Sat/Sun

# --- MOVED FROM MAIN.PY ---
def get_system_stats():
    """Returns (battery_percent, awake_seconds)"""
    # Battery
    battery = psutil.sensors_battery()
    bat_pc = battery.percent if battery else 100
    
    # Awake time
    try:
        boot_time = psutil.boot_time()
        awake_sec = time.time() - boot_time
    except Exception:
        awake_sec = 3 * 60 * 60 # Fallback
        
    return bat_pc, awake_sec

def can_show_1hr(log, now_ts, battery_percent, awake_seconds, last_task_result):
    silent_until = log.get("silent_until")
    if silent_until and now_ts < silent_until:
        return False
    
    now = datetime.now()
    today = str(date.today())

    # Only evening or weekend
    if not is_weekend(now):
        if not (18 <= now.hour <= 22):
            return False

    # Awake long enough
    if awake_seconds < 2 * 60 * 60:
        return False

    # Battery guard
    if battery_percent < 30:
        return False

    # Only one per day
    if log.get("last_date") == today and log.get("daily_count", 0) >= 1:
        return False

    # Weekly limits
    if is_weekend(now):
        if log.get("weekly_count", 0) >= 2:
            return False
    else:
        if log.get("weekly_count", 0) >= 3:
            return False

    # If last deep task was ignored -> back off
    if last_task_result == "ignored":
        return False

    return True