from __future__ import annotations

import os

# Prefer real LlmAgent; provide minimal fallback for static analysis
try:
    from google.adk.agents import LlmAgent  # type: ignore
except Exception:  # pragma: no cover
    class LlmAgent:  # minimal stub
        def __init__(self, *args, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

MODEL = os.getenv("GENAI_MODEL", "gemini-2.0-flash")

joke_teller_agent = LlmAgent(
    model=MODEL,
    name="joke_teller",
    description="Tells clean, short, family-friendly jokes.",
    instruction=(
        "You are a joke-telling assistant. Tell a single, clean joke (1-3 sentences)."
        " Avoid offensive content. If user gives a topic, keep it on-topic."
    ),
    output_key="joke",
)
