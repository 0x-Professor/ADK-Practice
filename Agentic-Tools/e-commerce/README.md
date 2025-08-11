# E-commerce Assistant

Features
- Shopping advisor and research agent with structured product links, specs, and sources.
- Optional google_search tool for web-backed answers (no image URLs returned).
- Built-in FastAPI UI for quick testing.

Run (standalone UI)
- uvicorn Agentic-Tools.e-commerce.agent:app --reload
- Open http://127.0.0.1:port

Env vars
- GOOGLE_CSE_ID, GOOGLE_SEARCH_API_KEY: enable web search tool.
- OTEL_SDK_DISABLED=true: already set in code to silence OpenTelemetry warnings.

API
- GET /: Minimal chat UI. Shows text, any model-rendered HTML, and structured products list.
- POST /query: { query, user_id?, session_id? } -> { text, html, products[], page_urls[] }
- GET /img?u=: Simple image proxy for thumbnails (accepts direct image URLs only).

Notes
- Products are expected in a fenced JSON block the model returns; the frontend parses and renders them.
- For a unified root UI, see repository main.py. If not loading, run this module directly.
