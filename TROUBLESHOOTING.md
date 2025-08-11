# Troubleshooting

This guide lists common issues and quick fixes when running this repo on Windows or via ADK Web.

General checks
- Python: use Python 3.13+ (`py --version`)
- Dependencies: run `pip show google-adk` (>= 1.10.0). If missing: `py -m pip install -e .` or `uv sync`
- Env vars: copy `.env.example` to `.env` and fill required keys. Confirm with `py -c "import os; print(os.getenv('GOOGLE_CSE_ID'))"`
- Network: corporate proxies/firewalls can block APIs; test with `curl`/`Invoke-WebRequest`

ADK Web
- If agents don’t load: ensure this repo root is opened; `main.py` is at the root
- If tools are missing: check env vars are loaded (ADK Web may not read `.env` in subfolders; prefer root `.env`)
- Session issues: try a fresh session id; some examples assume a new session on each run

Brand SEO (Selenium)
- Chrome not found: install Chrome/Chromium. webdriver-manager auto-installs ChromeDriver
- Headless mode: set `HEADLESS=1` in `.env` for servers/CI; set `HEADLESS=0` locally to see the browser
- Timeouts: slow networks may need more time; see `tools.py` (page load timeout is 30s). Re-run if blocked by captchas
- Blocked SERP: Google may throttle/deny automated access; retry later, reduce frequency, or test different keywords. The agent will return a safe fallback JSON if parsing fails

Google Custom Search (CSE)
- 403/400 errors: verify `GOOGLE_CSE_ID` and `GOOGLE_SEARCH_API_KEY`; confirm the CSE is enabled for your project
- Zero results: ensure your CSE is configured to search the full web (or add sites)
- Quotas: check Google Cloud Console for usage limits

LiteLLM / OpenRouter (Practice/3)
- Missing key: set `OPENROUTER_API_KEY` in `.env`
- Model errors: ensure the model name is supported by your OpenRouter plan

Persistent storage (Practice/6)
- SQLite locking on Windows: close other processes using the DB; avoid opening the DB file in editors; rerun `py Practice\6-persistant-storage\main.py`
- State not updating: check tool functions for exceptions; they return error dicts you can print

Networking and SSL
- SSL/Cert errors (Windows): update `certifi` (`py -m pip install -U certifi`); retry
- Proxy: set `HTTP_PROXY`/`HTTPS_PROXY` env vars if required by your network

Import/Module errors
- `ModuleNotFoundError: google.adk`: install deps (`py -m pip install -e .` or `uv sync`)
- Mixed Python installs: ensure you’re using the correct interpreter (`py -0p` lists installed Pythons)

Optional local web UIs
- Root UI: `py -m uvicorn main:app --reload` then open http://127.0.0.1:8000
- E-commerce UI: `py -m uvicorn Agentic-Tools.e-commerce.agent:app --reload`

Getting help
- Open an issue with:
  - OS and Python version
  - Exact command(s) used
  - Truncated logs and error messages
  - Whether you ran via ADK Web or shell
