import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate

from memory.promptemplates import build_prompt

load_dotenv()

llm = ChatGroq(
    temperature=0.55,
    groq_api_key=os.getenv("GROQ_API_KEY"),
    model_name="llama-3.3-70b-versatile"
)


def ask_ai(prompt: str) -> str:
    """Generic LLM query interface."""
    try:
        response = llm.invoke(prompt)
        return response.content.strip()
    except Exception as e:
        return f'{{"error": "AI query failed: {str(e)}"}}'


def rephrase_task(
    task_text: str,
    memory_context: str | None = None,
    mode: str = "reflect"
) -> str:
    """
    Language layer ONLY.

    - If memory_context is None → v0.2 behavior (simple rephrase)
    - If memory_context is provided → v0.3 RAG-based phrasing
    """

    # ─────────────────────────────────────
    # v0.2 MODE (no RAG, just rephrasing)
    # ─────────────────────────────────────
    if not memory_context:
        prompt_text = """
Rewrite this task in a light, playful "soft dare" tone.

Vibe:
- Casual
- Slightly challenging
- Friendly nudge, not advice
- Feels like: "eh, try it"
- Low pressure, but not sleepy
- Fun and engaging

Rules:
- Under 25 words
- Same meaning
- No motivational talk
- Humor allowed (dry, subtle)
- Emojis optional
- Do NOT repeat verbatim
- Start with "AI-generated:"

Task:
"{task}"

Output only the rewritten task.
"""
        prompt = PromptTemplate.from_template(prompt_text)
        chain = prompt | llm

        try:
            result = chain.invoke({"task": task_text}).content.strip()
            return result if result else task_text
        except Exception:
            return task_text

    # ─────────────────────────────────────
    # v0.3 MODE (RAG + prompt templates)
    # ─────────────────────────────────────
    prompt_text = build_prompt(
        mode=mode,
        memory_context=memory_context
    )

    prompt = PromptTemplate.from_template(prompt_text)
    chain = prompt | llm

    try:
        result = chain.invoke({}).content.strip()
        return result if result else task_text
    except Exception:
        return task_text
