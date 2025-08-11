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
- **Practice**: seven progressively more advanced samples showing agent patterns (tools, LiteLLM, schemas, state, persistence, orchestration).

## Quick start (Windows)
- Install Python 3.13+
- In PowerShell or CMD at repo root:
  - `py -m pip install -U pip`
  - `py -m pip install -r <(extract from pyproject)` or use `uv`: `pip install uv && uv sync`
- Copy `.env.example` to `.env` and fill the keys you need.

## Environment (.env.example)
- `GOOGLE_CSE_ID`, `GOOGLE_SEARCH_API_KEY`: enable google_search where used (e-commerce, brand-SEO keyword finder).
- `OPENROUTER_API_KEY`: required for Practice/3-litellm_agent.
- `GENAI_MODEL`: override the default model (gemini-2.0-flash).
- `HEADLESS`: 1 to run Selenium in headless mode (brand-SEO search_result).
- Optional extras: `WIKI_ACCESS_TOKEN`, `UPSTREAM_VECTOR_URL`.

## How to run
### ADK Web
- Open ADK Web and add this repo folder. Use the built-in runner to chat with agents.
- Agents to try: `ecommerce`, `brand-seo` (both are auto-loaded by main app logic), or practice sub-agents directly.

### Python scripts (Practice examples)
- Basic agent: `py Practice\1-basic-agent\main.py`
- Tool agent (Wikipedia/Finance): import `Practice\2-tool_agent\tool_agent\agent.py` in your own runner.
- LiteLLM example: `py Practice\3-litellm_agent\main.py` (requires `OPENROUTER_API_KEY`)
- Structured output (email): `py Practice\4-structured-output\main.py`
- Session/state demo: `py Practice\5-session-and-state\basic-stateful-session.py`
- Persistent storage (SQLite): `py Practice\6-persistant-storage\main.py`
- Multi-agent manager (interactive): `py Practice\7-multi-agent\main.py`

### Optional: start local web UIs with uvicorn
- Unified web UI (root FastAPI app):
  - `py -m uvicorn main:app --reload`
  - Then open [http://127.0.0.1:8000](http://127.0.0.1:8000) and choose a mode (E-commerce or Brand SEO)
- E-commerce standalone UI:
  - `py -m uvicorn Agentic-Tools.e-commerce.agent:app --reload`
  - [http://127.0.0.1:8000](http://127.0.0.1:8000)

## Projects overview
- `main.py`: a minimal FastAPI app that loads “ecommerce” and “brand-seo” agents and renders model text/HTML.
- `Agentic-Tools/e-commerce`: Research + Shop agents; UI exposes structured products and related links.
- `Agentic-Tools/brand-SEO`: Keyword finder (google_search), SERP parser (Selenium), and comparison orchestrator.
- `Agentic-Tools/youtube_shorts`: Short-form content pipeline (scriptwriter/visualizer/formatter).
- **Practice**: standalone examples for learning core ADK concepts.

## Screenshots / GIFs (placeholders)
- Add capture files under `docs/assets/` and link them here:
  - `docs/assets/home-ui.png` — root web UI
  - `docs/assets/ecommerce-products.png` — structured product list
  - `docs/assets/brand-seo-serp.png` — SERP insights
  - `docs/assets/multi-agent-cli.gif` — console demo

## Contributing
- Use concise, commented code and docstrings in tools.
- Prefer minimal dependencies; keep examples runnable on Windows.
- PRs: add or update README sections for any new examples.