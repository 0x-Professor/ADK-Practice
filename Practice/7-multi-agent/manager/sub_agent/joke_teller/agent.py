from __future__ import annotations

import os
from google.adk.agents.llm_agent import Agent

# Prefer real LlmAgent; provide minimal fallback for static analysis
try:
    from google.adk.agents import LlmAgent  # type: ignore
except Exception:  # pragma: no cover
    class LlmAgent:  # minimal stub
        def __init__(self, *args, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

MODEL = os.getenv("GENAI_MODEL", "gemini-2.0-flash")

root_agent = Agent(
    model='<FILL_IN_MODEL>',
    name='root_agent',
    description='A helpful assistant for user questions.',
    instruction='Answer user questions to the best of your knowledge',
)

joke_teller_agent = LlmAgent(
    model=MODEL,
    name="joke_teller_agent",
    description="Tells clean, short, family-friendly jokes.",
    instruction=(
        "You are a joke-telling assistant. Tell a single, clean joke (1-3 sentences)."
        " Avoid offensive content. If user gives a topic, keep it on-topic."
    ),
    output_key="joke",
)
