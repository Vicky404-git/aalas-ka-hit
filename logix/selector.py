import random


def select_5min_task(tasks, log):
    recent = set(log.get("recent_tasks", []))
    last_task = log.get("last_task")
    recent_tags = log.get("recent_tags", [])

    # 1. Try to find a truly new task
    candidates = [t for t in tasks if t["text"] not in recent]
    repeated = False

    # Prevent reset spam
    if recent_tags and recent_tags[-1] == "reset":
        candidates = [t for t in candidates if t["tag"] != "reset"]

    # 2. If no new tasks, exclude the last task
    if not candidates:
        candidates = [t for t in tasks if t["text"] != last_task]
        repeated = True

    # 3. Absolute fallback (single-task safety)
    if not candidates:
        candidates = tasks
        repeated = True

    task = random.choice(candidates)

    # Update log
    log["recent_tasks"].append(task["text"])
    log["recent_tasks"] = log["recent_tasks"][-20:]

    log["recent_tags"].append(task["tag"])
    log["recent_tags"] = log["recent_tags"][-3:]

    log["last_task"] = task["text"]
    log["last_task_repeated"] = repeated

    return task, log



def select_1hr_task(tasks, log):
    recent = set(log.get("recent_tasks", []))
    candidates = [t for t in tasks if t["text"] not in recent]

    if not candidates:
        candidates = tasks

    task = random.choice(candidates)

    log["recent_tasks"].append(task["text"])
    log["recent_tasks"] = log["recent_tasks"][-10:]

    log["last_task"] = task["text"]
    log["last_task_repeated"] = False


    return task, log
