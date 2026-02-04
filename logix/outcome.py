import time
from logix.event_log import log_event

MIN_GAP = 30 * 60  # 30 minutes

# States that are considered "final" - we won't overwrite them
FINAL_RESULTS = {"done", "skipped", "ignored", "inferred_done"}

def infer_last_outcome(log, now_ts, task_type, log_to_csv=True):
    """
    Checks the previous task. If the user didn't click Done/Skip,
    this decides if it was 'ignored' (overwritten quickly) 
    or 'inferred_done' (left alone for a long time).
    """

    # If there's no task history, do nothing
    if not log.get("last_task") or not log.get("last_shown_ts"):
        return log

    # If already marked done/skip, don't change it
    if log.get("last_task_result") in FINAL_RESULTS:
        return log

    elapsed = now_ts - log["last_shown_ts"]

    # LOGIC:
    # If the script runs again very soon (<30 mins), the user likely "Ignored" the notification.
    # If the script runs much later (>30 mins), we assume they might have done it ("inferred_done").
    if elapsed < MIN_GAP:
        result = "ignored"
    else:
        result = "inferred_done"

    # Update in-memory state (so we know for next time)
    log["last_task_result"] = result

    # Log to CSV
    if log_to_csv:
        log_event(
            f"logs/{task_type}_history.csv",
            log["last_task"],
            "unknown",
            task_type,
            result,
            log.get("last_task_repeated", False)
        )

    return log