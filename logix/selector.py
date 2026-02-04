import random


def _get_tags(task):
    """Normalize tag field to list"""
    tag = task.get("tag", [])
    if isinstance(tag, str):
        return [tag]
    return tag


def _task_score(task, tag_scores):
    """Score task based on tag history"""
    return sum(tag_scores.get(tag, 0) for tag in _get_tags(task))


def select_5min_task(tasks, log):
    tag_scores = log.get("tag_scores", {})

    # Defensive defaults
    log.setdefault("recent_tasks", [])
    log.setdefault("recent_tags", [])
    log.setdefault("last_task", None)

    recent_tasks = set(log["recent_tasks"])
    last_task = log["last_task"]
    recent_tags = log["recent_tags"]

    # 1. Prefer tasks not done recently
    candidates = [t for t in tasks if t["text"] not in recent_tasks]
    repeated = False

    # Prevent reset spam
    if recent_tags and any(t == "reset" for t in recent_tags[-1:]):
        candidates = [t for t in candidates if t.get("tag") != "reset"]

    # 2. If nothing left, avoid immediate repeat
    if not candidates:
        candidates = [t for t in tasks if t["text"] != last_task]
        repeated = True

    # 3. Absolute fallback
    if not candidates:
        candidates = tasks
        repeated = True

    # 4. Rank candidates by tag score
    ranked = sorted(
        candidates,
        key=lambda t: _task_score(t, tag_scores),
        reverse=True
    )

    # 5. Pick from top few (keeps randomness)
    pick_pool = ranked[: min(3, len(ranked))]
    task = random.choice(pick_pool)

    # 6. Update log (selection only, no scoring)
    log["recent_tasks"].append(task["text"])
    log["recent_tasks"] = log["recent_tasks"][-20:]

    task_tags = _get_tags(task)
    log["recent_tags"].extend(task_tags)
    log["recent_tags"] = log["recent_tags"][-3:]

    log["last_task"] = task["text"]
    log["last_task_repeated"] = repeated

    return task, log


def select_1hr_task(tasks, log):
    tag_scores = log.get("tag_scores", {})

    log.setdefault("recent_tasks", [])
    log.setdefault("last_task", None)

    recent_tasks = set(log["recent_tasks"])

    # Avoid recent repeats
    candidates = [t for t in tasks if t["text"] not in recent_tasks]
    if not candidates:
        candidates = tasks

    # Rank by tag score
    ranked = sorted(
        candidates,
        key=lambda t: _task_score(t, tag_scores),
        reverse=True
    )

    pick_pool = ranked[: min(3, len(ranked))]
    task = random.choice(pick_pool)

    log["recent_tasks"].append(task["text"])
    log["recent_tasks"] = log["recent_tasks"][-10:]

    log["last_task"] = task["text"]
    log["last_task_repeated"] = False

    return task, log
