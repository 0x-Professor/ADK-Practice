# Search Result Sub-agent

Purpose
- Uses Selenium to open a SERP, parse top results, infer search intent, and output a JSON summary.

Files
- agent.py: search_result_agent wiring and tool registry.
- prompt.py: strict JSON-only instruction for SERP extraction and insights.
- tools.py: Selenium helpers (navigate, screenshot, find/click, scroll, DOM parsing).

Artifacts
- Screenshots and HTML snapshots are saved under artifacts/ (gitignored).
