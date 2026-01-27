import json
import random
import time
import socket
import os

STATE_FILE = "logs/state.json"
HISTORY_LIMIT = 20


def load_state():
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def select_task(tasks):
    state = load_state()
    recent = state.get("recent_tasks", [])

    # random sample of 50
    sample = random.sample(tasks, min(50, len(tasks)))

    # remove recent repeats
    filtered = [t for t in sample if t not in recent]

    final_task = random.choice(filtered if filtered else sample)

    # update history
    recent.append(final_task)
    state["recent_tasks"] = recent[-HISTORY_LIMIT:]

    save_state(state)
    return final_task


def wait_for_network(timeout=360, check_interval=5):
    start = time.time()

    while time.time() - start < timeout:
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except OSError:
            time.sleep(check_interval)

    return False
