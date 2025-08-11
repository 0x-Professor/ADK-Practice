# ADK Practice Monorepo (Education-Focused)

This repository is a learning lab for building agentic apps with Google ADK. It contains small, focused examples and production-like toolchains you can study, run, and adapt.

## Table of contents
- [What’s here](#whats-here)
- [Quick start (Windows)](#quick-start-windows)
- [Environment (.env.example)](#environment-envexample)
- [How to run](#how-to-run)
  - [ADK Web](#adk-web)
  - [Python scripts (Practice examples)](#python-scripts-practice-examples)
  - [Optional: start local web UIs with uvicorn](#optional-start-local-web-uis-with-uvicorn)
- [Projects overview](#projects-overview)
- [Screenshots / GIFs (placeholders)](#screenshots--gifs-placeholders)
- [Contributing](#contributing)

## What’s here
- **Agentic-Tools**
  - **e-commerce**: product research and shopping advisor with structured outputs, plus a simple FastAPI UI.
  - **brand-SEO**: orchestrated SEO workflow (keyword finder, Selenium SERP parser, comparison report).
  - **youtube_shorts**: 3-stage Shorts pipeline (scriptwriter, visualizer, formatter) with file-based prompts.
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