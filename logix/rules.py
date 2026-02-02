from datetime import datetime, date, timedelta
def get_week_start(d=None):
    d = d or date.today()
    return str(d - timedelta(days=d.weekday()))


def is_weekend(now=None):
    now = now or datetime.now()
    return now.weekday() >= 5  # Sat/Sun


def can_show_1hr(
    log,
    now_ts,
    battery_percent,
    awake_seconds,
    last_task_result
):
    now = datetime.now()
    today = str(date.today())

    # only evening or weekend
    if not is_weekend(now):
        if not (18 <= now.hour <= 22):
            return False

    # awake long enough
    if awake_seconds < 2 * 60 * 60:
        return False

    # battery guard
    if battery_percent < 30:
        return False

    # only one per day
    if log.get("last_date") == today and log.get("daily_count", 0) >= 1:
        return False

    # weekly limits
    if is_weekend(now):
        if log.get("weekly_count", 0) >= 2:
            return False
    else:
        if log.get("weekly_count", 0) >= 3:
            return False

    # if last deep task was ignored → back off
    if last_task_result == "ignored":
        return False

    return True
