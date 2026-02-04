from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
import os
from dotenv import load_dotenv

load_dotenv()

llm = ChatGroq(
    temperature=0.55,
    groq_api_key=os.getenv("GROQ_API_KEY"),
    model_name="llama-3.3-70b-versatile"
)


def rephrase_task(task: str) -> str:
    prompt_text = """
Rewrite this task in a light, playful "soft dare" tone.

Vibe:
- Casual
- Slightly challenging
- Friendly nudge, not advice
- Feels like: "eh, try it"
- Low pressure, but not sleepy
- fun and engaging

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
        result = chain.invoke({"task": task}).content.strip()
        return result if result else task
    except Exception:
        return task
