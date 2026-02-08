"""
Prompt templates for v0.3 reflective memory (RAG).

Each template assumes:
- memory_context = text retrieved from last 7 days
- model should NOT invent facts
- tone matters as much as content
"""

PROMPT_TEMPLATES = {

    "reflect": """
Context (recent behavior):
{memory_context}

Instruction:
Based only on the behavior above, describe the patterns you notice.
Be factual, neutral, and calm.
Do not give advice. Do not judge.
""",

    "advise": """
Context (recent behavior):
{memory_context}

Instruction:
Suggest ONE small, low-pressure adjustment that might help.
No motivation talk. No discipline lectures.
Keep it gentle and practical.
""",

    "roast": """
Context (recent behavior):
{memory_context}

Instruction:
Roast this behavior lightly like a close friend would.
Be funny, honest, and kind.
No insults. No shame.
One short paragraph.
""",

    "reality_check": """
Context (recent behavior):
{memory_context}

Instruction:
If someone claimed they were being very productive,
compare that claim with the behavior above
and point out any mismatch honestly.
""",

    "pattern_name": """
Context (recent behavior):
{memory_context}

Instruction:
Name the main behavior pattern you see here,
as if it were a habit or tendency.
Explain it in one sentence.
""",

    "time_insight": """
Context (recent behavior):
{memory_context}

Instruction:
Focus only on time-of-day patterns.
When does the user tend to succeed?
When do they tend to avoid or skip tasks?
""",

    "energy_check": """
Context (recent behavior):
{memory_context}

Instruction:
What does this behavior suggest about energy levels?
Be careful not to assume laziness or lack of willpower.
""",

    "consistency": """
Context (recent behavior):
{memory_context}

Instruction:
Identify ONE thing the user is surprisingly consistent at,
even if it seems small or unimpressive.
""",

    "anti_advice": """
Context (recent behavior):
{memory_context}

Instruction:
Based on this behavior, what advice would clearly NOT work
for this person right now?
Explain briefly.
""",

    "one_line_mirror": """
Context (recent behavior):
{memory_context}

Instruction:
Summarize this week of behavior in ONE honest sentence.
No sugarcoating. No motivation.
"""
}


def build_prompt(mode: str, memory_context: str) -> str:
    """
    Returns a formatted prompt for the given mode.
    Falls back to 'reflect' if mode is unknown.
    """
    template = PROMPT_TEMPLATES.get(mode, PROMPT_TEMPLATES["reflect"])
    return template.format(memory_context=memory_context)
