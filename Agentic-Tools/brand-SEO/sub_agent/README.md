# Sub-agents (Brand SEO)

Overview
- This package groups the brand-SEO leaf agents used by the orchestrator:
  - keyword_finding: discovers keywords using google_search.
  - search_result: Selenium-powered SERP parser and insights.
  - comparison: comparison draft + critic to produce a final report.

Usage
- Called automatically by Agentic-Tools/brand-SEO/agent.py via sub_agents.
