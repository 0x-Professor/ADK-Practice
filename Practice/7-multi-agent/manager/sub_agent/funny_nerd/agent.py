from __future__ import annotations

import os

try:
    from google.adk.agents import LlmAgent  # type: ignore
except Exception:  # pragma: no cover
    class LlmAgent:  # minimal stub
        def __init__(self, *args, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

MODEL = os.getenv("GOOGLE_API_KEY", "gemini-2.0-flash")

funny_nerd_agent = LlmAgent(
    model=MODEL,
    name="funny_nerd_agent",
    description="A witty, nerdy assistant for light-hearted explanations and fun facts.",
    instruction=(
        "You are a funny, nerdy assistant. Answer with concise, accurate info and sprinkle in"
        " light wordplay or geeky references. Avoid offensive humor. Keep responses under 120 words."
    ),
    output_key="answer",
)
