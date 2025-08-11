# Agentic-Tools

This folder contains production-like agents grouped by capability:
- e-commerce: product research and shopping advisor (FastAPI app included).
- brand-SEO: multi-agent SEO orchestrator (keyword finding, SERP analysis via Selenium, competitor comparison).
- youtube_shorts: 3-stage pipeline for Shorts (scriptwriter, visualizer, formatter).

Install
- uv sync (root workspace)

Notes
- GOOGLE_CSE_ID and GOOGLE_SEARCH_API_KEY enable google_search where used.
- For brand-SEO Selenium tasks, install Chrome/Chromium; use HEADLESS=1 on servers.
