# Brand SEO Orchestrator

Overview
- Orchestrates three sub-agents in order:
  1) keyword_finding_agent: discovers keywords via google_search tool.
  2) search_result_agent: parses SERP using Selenium with reusable Chrome session; extracts domains, snippets, intent.
  3) comparison_root_agent: drafts and critiques a competitor comparison report.
- The root agent enforces the sequence and summarizes results to the user.

Requirements
- Python 3.13+
- Chrome/Chromium available on PATH (Selenium)
- Dependencies: google-adk, selenium, webdriver-manager (declared in pyproject)

Environment
- GOOGLE_CSE_ID and GOOGLE_SEARCH_API_KEY: enable google_search for keyword_finding_agent.
- HEADLESS: "1" (default) for headless browser; set 0 locally to view.
- GENAI_MODEL: override model (defaults to gemini-2.0-flash).

How to run
- Via the root FastAPI UI in repository main.py: select "Brand SEO" mode.
- The sub-agent search_result stores screenshots and HTML under sub_agent/search_result/artifacts/ (gitignored).

Notes
- Selenium driver is managed by webdriver-manager automatically.
- The search_result_agent returns a JSON object (serp_analysis) with rank, title, url, domain, snippet, content_type, plus insights like competitor_domains.
- The comparison orchestrator runs a self-critique step to ensure JSON schema compliance.
