# ADK Practice Monorepo

Overview
- E-commerce Assistant: product research and shopping advisor with structured results. Optional web search via google_search.
- Brand SEO Orchestrator: multi-agent workflow for keyword finding, SERP analysis (Selenium), and competitor comparison.
- YouTube Shorts Pipeline: scriptwriter, visualizer, and formatter agents.
- Practice: learning projects showing basic agent patterns, tools, structured outputs, sessions/state, persistence, and multi-agent orchestration.

Quick start
- Requirements: Python 3.13+, uv or pip, Chrome/Chromium for Selenium tasks (brand-SEO), credentials where applicable.
- Install deps (recommended):
  - uv sync
- Run the unified FastAPI app (root):
  - uvicorn main:app --reload
  - Open http://127.0.0.1:8000 to use the simple UI. Choose mode: ecommerce or brand-seo.

Environment variables
- GOOGLE_CSE_ID and GOOGLE_SEARCH_API_KEY: enable google_search tool (used by e-commerce and brand-SEO’s keyword finder). Optional; features degrade gracefully.
- HEADLESS: "1" (default) runs Selenium headless for brand-SEO. Set 0 locally to see the browser.
- UPSTREAM_VECTOR_URL: optional proxy target for Agentic-Tools/e-commerce/vector_service.py.
- GENAI_MODEL: override default model (gemini-2.0-flash) for practice/manager sub-agents.
- OPENROUTER_API_KEY: needed for Practice/3-litellm_agent example.

Project layout (high level)
- main.py: FastAPI UI that dynamically loads the selected agent (ecommerce, brand-seo) and renders text + any returned HTML. Includes a tiny /img proxy for thumbnails.
- Agentic-Tools/
  - e-commerce/: Shop + Research sub-agents with web search; includes a standalone FastAPI app in agent.py for a chat-like UI.
  - brand-SEO/: Orchestrator that calls keyword_finding, search_result (Selenium), and comparison sub-agents in order.
  - youtube_shorts/: Scriptwriter, Visualizer, Formatter with file-based instructions and safe fallbacks.
- Practice/: Self-contained examples (1-basic-agent, tools, LiteLLM, structured output, session/state, persistence, multi-agent manager).

Running each component
- E-commerce (root UI): Select “E-commerce” in the root UI.
- Brand SEO (root UI): Select “Brand SEO” in the root UI. Ensure Chrome/Chromium installed; HEADLESS=1 on servers.
- Standalone (optional): Agentic-Tools/e-commerce/agent.py defines its own FastAPI app; run uvicorn Agentic-Tools.e-commerce.agent:app --reload.

Notes
- Agent discovery: the root UI expects ./e-commerce/agent.py and ./brand-SEO/agent.py in the repo root. If your agents live under Agentic-Tools/, run those apps directly or adapt main.py.
- The UI tries to show HTML returned by the model (renderedContent) and also parses text for URLs.
- The brand-SEO flow relies on Selenium (webdriver-manager installs ChromeDriver on demand). On CI/servers, keep HEADLESS=1.
- Practice projects are intended as reference and learning aids; some are console programs.

Contributing
- Use uv for dependency management; see pyproject.toml workspaces.
- Keep agents minimal, stateless unless a session example; add tool docstrings for automatic function schemas.

License
- For educational/demo purposes.