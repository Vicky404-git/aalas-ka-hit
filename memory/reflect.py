import sys
from memory.rag import get_memory_context
from ai_brain import rephrase_task

# ─── Modes and what they do ───
MODES = {
    "reflect": "What patterns do I show in my behavior?",
    "advise": "What small adjustment could help me?",
    "roast": "Roast my recent behavior lightly.",
    "mirror": "Summarize my recent behavior honestly."
}

# ─── Time windows ───
WINDOWS = {"rolling", "weekly"}


def print_help():
    print("""
Usage:
  python -m memory.reflect <mode> [window]

Modes:
  reflect   - neutral pattern reflection
  advise    - gentle suggestion
  roast     - light, friendly roast
  mirror    - one-line honest summary

Windows:
  rolling   - recent activity (default)
  weekly    - last 7 days

Examples:
  python -m memory.reflect reflect
  python -m memory.reflect roast weekly
""")


def main():
    # ─── Require at least mode ───
    if len(sys.argv) < 2:
        print_help()
        return

    mode = sys.argv[1]
    window = sys.argv[2] if len(sys.argv) > 2 else "rolling"

    # ─── Validate inputs ───
    if mode not in MODES:
        print(f"Unknown mode: {mode}")
        print_help()
        return

    if window not in WINDOWS:
        print(f"Unknown window: {window}")
        print_help()
        return

    # ─── RAG only runs because user explicitly asked ───
    memory = get_memory_context(
        query=MODES[mode],
        mode=window
    )

    if not memory:
        print("Not enough data yet to reflect.")
        return

    text = rephrase_task(
        task_text="Reflection:",
        memory_context=memory,
        mode=mode
    )

    print(text)


if __name__ == "__main__":
    main()
