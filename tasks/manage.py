import argparse
import json
import os
import re
import sys
from pathlib import Path

# Paths to task banks
BASE_DIR = Path(__file__).resolve().parent.parent
TASKS_5MIN = BASE_DIR / "tasks" / "tasks.json"
TASKS_1HR = BASE_DIR / "tasks" / "deeptasks.json"

# Import ai_brain if available
try:
    from ai_brain import ask_ai
    HAS_AI = True
except ImportError:
    HAS_AI = False


def load_tasks(filepath):
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def save_tasks(filepath, tasks):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=4)


def tokenize(text):
    """Normalizes text into a set of lowercased words."""
    return set(re.findall(r"\w+", text.lower()))


def calculate_overlap(new_tokens, existing_tokens):
    """Calculates word overlap ratio between two token sets."""
    if not new_tokens or not existing_tokens:
        return 0.0
    intersection = new_tokens.intersection(existing_tokens)
    return len(intersection) / float(min(len(new_tokens), len(existing_tokens)))


def check_ai_duplicate(new_text, existing_text):
    """LLM semantic equivalence check using ai_brain."""
    prompt = f"""Compare these two tasks and determine if they are semantically identical or asking to do the exact same action:

Task 1: "{new_text}"
Task 2: "{existing_text}"

Respond ONLY in valid JSON format:
{{"is_duplicate": true/false, "reason": "brief 1-sentence reason"}}"""

    return ask_ai(prompt)


def cmd_add(args):
    filepath = TASKS_1HR if args.deep else TASKS_5MIN
    tasks = load_tasks(filepath)
    new_text = args.text.strip()
    new_tokens = tokenize(new_text)

    exact_scrambled = []
    partial_matches = []

    # 1. Similarity Check Engine
    for task in tasks:
        existing_tokens = tokenize(task["text"])
        overlap = calculate_overlap(new_tokens, existing_tokens)

        if new_tokens == existing_tokens:
            exact_scrambled.append(task)
        elif overlap >= 0.5:
            partial_matches.append((task, round(overlap * 100)))

    # 2. Output Similarity Results
    if exact_scrambled:
        print("\n❌ [EXACT / SCRAMBLED DUPLICATE FOUND]")
        for t in exact_scrambled:
            print(f'   └─ Existing: "{t["text"]}" (Tag: {t.get("tag", "no-tag")})')
        if not args.force:
            print("Aborted. Use --force to add anyway.\n")
            return

    elif partial_matches:
        print("\n⚠️ [POSSIBLE DUPLICATES FOUND (>50% Overlap)]")
        for t, pct in partial_matches:
            print(f'   └─ [{pct}% overlap] "{t["text"]}" (Tag: {t.get("tag", "no-tag")})')

        # 3. Optional AI Check
        if args.ai:
            if not HAS_AI:
                print("\n⚠️ AI brain not detected or missing ask_ai(). Skipping AI verification.")
            else:
                print("\n🤖 [AI Brain Duplicate Check]")
                for t, _ in partial_matches:
                    ai_res = check_ai_duplicate(new_text, t["text"])
                    print(f'   └─ Comparing against: "{t["text"]}"')
                    print(f'      {ai_res}')

        if not args.force:
            confirm = input("\nDo you still want to add this task? (y/N): ").strip().lower()
            if confirm != "y":
                print("Cancelled.\n")
                return

    # 4. Save Task
    new_task = {"text": new_text, "tag": args.tag}
    tasks.append(new_task)
    save_tasks(filepath, tasks)
    target_name = "deeptasks.json" if args.deep else "tasks.json"
    print(f'\n✅ Successfully added to {target_name}: "{new_text}" [tag: {args.tag}]\n')


def cmd_list(args):
    filepath = TASKS_1HR if args.deep else TASKS_5MIN
    tasks = load_tasks(filepath)
    target_name = "deeptasks.json" if args.deep else "tasks.json"

    print(f"\n📋 Task List ({target_name}) - Total: {len(tasks)}")
    print("-" * 55)
    for idx, t in enumerate(tasks, 1):
        print(f'{idx:2d}. [{t.get("tag", "no-tag")}] {t["text"]}')
    print()


def cmd_delete(args):
    filepath = TASKS_1HR if args.deep else TASKS_5MIN
    tasks = load_tasks(filepath)
    target_name = "deeptasks.json" if args.deep else "tasks.json"

    target_idx = None
    if args.query.isdigit():
        idx = int(args.query) - 1
        if 0 <= idx < len(tasks):
            target_idx = idx
    else:
        for idx, t in enumerate(tasks):
            if args.query.lower() in t["text"].lower():
                target_idx = idx
                break

    if target_idx is None:
        print(f'\n❌ Could not find task matching "{args.query}" in {target_name}.\n')
        return

    removed = tasks.pop(target_idx)
    save_tasks(filepath, tasks)
    print(f'\n🗑️ Removed from {target_name}: "{removed["text"]}"\n')


def cmd_edit(args):
    filepath = TASKS_1HR if args.deep else TASKS_5MIN
    tasks = load_tasks(filepath)
    target_name = "deeptasks.json" if args.deep else "tasks.json"

    target_idx = None
    if args.query.isdigit():
        idx = int(args.query) - 1
        if 0 <= idx < len(tasks):
            target_idx = idx

    if target_idx is None:
        print(f'\n❌ Invalid task index "{args.query}" in {target_name}.\n')
        return

    old_text = tasks[target_idx]["text"]
    tasks[target_idx]["text"] = args.new_text
    if args.tag:
        tasks[target_idx]["tag"] = args.tag

    save_tasks(filepath, tasks)
    print(f'\n✏️ Updated task #{target_idx + 1} in {target_name}:')
    print(f'   Old: "{old_text}"')
    print(f'   New: "{args.new_text}" [tag: {tasks[target_idx].get("tag", "no-tag")}]\n')


def main():
    parser = argparse.ArgumentParser(description="Task Management CLI for aalas-ka-hit")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # ADD
    p_add = subparsers.add_parser("add", help="Add a new task")
    p_add.add_argument("text", type=str, help="Task text")
    p_add.add_argument("--tag", type=str, default="code", help="Tag for the task (default: code)")
    p_add.add_argument("--deep", action="store_true", help="Target deeptasks.json (1hr) instead of tasks.json")
    p_add.add_argument("--ai", action="store_true", help="Run AI brain check on candidates with >50% overlap")
    p_add.add_argument("--force", action="store_true", help="Skip confirmation prompts")

    # LIST
    p_list = subparsers.add_parser("list", help="List tasks")
    p_list.add_argument("--deep", action="store_true", help="Target deeptasks.json (1hr)")

    # DELETE
    p_del = subparsers.add_parser("delete", help="Delete task by index or substring")
    p_del.add_argument("query", type=str, help="Index number or text query")
    p_del.add_argument("--deep", action="store_true", help="Target deeptasks.json (1hr)")

    # EDIT
    p_edit = subparsers.add_parser("edit", help="Edit task by index")
    p_edit.add_argument("query", type=str, help="Index number of the task")
    p_edit.add_argument("new_text", type=str, help="New task text")
    p_edit.add_argument("--tag", type=str, help="Optional new tag")
    p_edit.add_argument("--deep", action="store_true", help="Target deeptasks.json (1hr)")

    args = parser.parse_args()

    if args.command == "add":
        cmd_add(args)
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "delete":
        cmd_delete(args)
    elif args.command == "edit":
        cmd_edit(args)


if __name__ == "__main__":
    main()
