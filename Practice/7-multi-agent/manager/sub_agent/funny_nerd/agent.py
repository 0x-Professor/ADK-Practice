from __future__ import annotations

import os

try:
    from google.adk.agents.llm_agent import Agent  # type: ignore
except Exception:  # pragma: no cover
    class Agent:  # minimal stub
        def __init__(self, *args, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

MODEL = os.getenv("GENAI_MODEL", "gemini-2.0-flash")

funny_nerd_agent = Agent(
    model=MODEL,
    name="funny_nerd",
    description="A witty, nerdy assistant for light-hearted explanations and fun facts.",
    instruction=(
        "You are a funny, nerdy assistant. Answer with concise, accurate info and sprinkle in"
        " light wordplay or geeky references. Avoid offensive humor. Keep responses under 120 words."
    ),
    output_key="answer",
)
