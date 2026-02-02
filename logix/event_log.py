import csv
import os
import time
from datetime import datetime

def log_event(path, task, tag, task_type, status, repeated=False):
    exists = os.path.exists(path)

    now = time.time()
    dt = datetime.fromtimestamp(now)

    row = [
        int(now),
        dt.date().isoformat(),
        dt.strftime("%H:%M:%S"),
        task,
        tag,
        task_type,
        status,
        repeated
    ]

    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not exists:
            writer.writerow([
                "timestamp", "date", "time",
                "task", "tag", "type",
                "status", "repeated"
            ])
        writer.writerow(row)
