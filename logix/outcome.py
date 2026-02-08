from logix.event_log import log_event
from logix.state import save_log, FIVE_MIN_LOG, ONE_HR_LOG # Imported for saving

MIN_GAP = 30 * 60  # 30 minutes
FINAL_RESULTS = {"done", "skipped", "ignored", "inferred_done"}

# --- MOVED FROM MAIN.PY ---
def process_user_action(log1, log5, action, target_type):
    """Updates logs, scores, and history based on user click."""
    
    def _record(log, log_path, csv_path, t_type):
        # 1. Apply Learning
        mock_task = {"tag": log.get("last_tag", "unknown")}
        update_tag_scores(log, mock_task, action)

        # 2. Update Result
        log["last_task_result"] = action
        
        # 3. Track Skips (Burnout prevention)
        if action == "skipped" and t_type == "5min":
            log["ignored_today"] = log.get("ignored_today", 0) + 1
        
        # 4. Save
        save_log(log_path, log)
        log_event(
            csv_path,
            log.get("last_task", "Unknown"),
            "unknown",
            t_type,
            action,
            log.get("last_task_repeated", False)
        )

    if target_type == "1hr":
        _record(log1, ONE_HR_LOG, "logs/1hr_history.csv", "1hr")
    else:
        _record(log5, FIVE_MIN_LOG, "logs/5min_history.csv", "5min")

    return log1, log5


def infer_last_outcome(log, now_ts, task_type, log_to_csv=True):
    if not log.get("last_task") or not log.get("last_shown_ts"):
        return log

    if log.get("last_task_result") in FINAL_RESULTS:
        return log

    elapsed = now_ts - log["last_shown_ts"]

    if elapsed < MIN_GAP:
        result = "ignored"
    else:
        result = "inferred_done"

    log["last_task_result"] = result

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

def update_tag_scores(log, task, outcome):
    tag_scores = log.setdefault("tag_scores", {})
    for tag in task.get("tag", [] if isinstance(task.get("tag"), list) else [task["tag"]]):
        tag_scores.setdefault(tag, 0)
        if outcome == "done":
            tag_scores[tag] += 1
        elif outcome == "ignored":
            tag_scores[tag] -= 1

        tag_scores[tag] = max(-3, min(3, tag_scores[tag]))