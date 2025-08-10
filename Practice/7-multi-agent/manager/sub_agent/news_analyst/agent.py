from __future__ import annotations

import os

# Prefer real LlmAgent; provide minimal fallback to satisfy static analysis
try:
    from google.adk.agents import LlmAgent  # type: ignore
except Exception:  # pragma: no cover
    class LlmAgent:  # minimal stub
        def __init__(self, *args, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

# Optional google search tool
TOOLS = []
try:
    from google.adk.tools import google_search  # type: ignore
    if os.getenv("GOOGLE_CSE_ID") and os.getenv("GOOGLE_SEARCH_API_KEY"):
        TOOLS = [google_search]
except Exception:
    TOOLS = []

MODEL = os.getenv("GENAI_MODEL", "gemini-2.0-flash")

news_analyst_agent = LlmAgent(
    model=MODEL,
    name="news_analyst_agent",
    description="Analyzes recent news and provides concise, source-aware summaries.",
    instruction=(
        "You are a news analyst. Provide brief, neutral summaries with key facts and context."
        " If tools are available, cross-check at least 2 sources and cite titles + URLs."
        " Keep responses under 150 words. Avoid speculation."
    ),
    tools=TOOLS,
    output_key="news_summary",
)
