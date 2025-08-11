# 2-tool_agent

Purpose
- Demonstrates a tool-rich LlmAgent with:
  - Wikipedia utilities: search, page summary/parse, raw HTML
  - Finance: currency conversion, mortgage calculator
  - Marketing: UTM URL builder
  - Misc: current date helper

Files
- tool_agent/agent.py: defines root_agent and tool implementations.

Usage
- Import tool_agent.agent.root_agent and run via Runner.
- Set GOOGLE_CSE_ID and GOOGLE_SEARCH_API_KEY to enable google_search (currently commented by default).

Notes
- Wikipedia tools respect API usage policy via headers. Optional bearer token from WIKI_ACCESS_TOKEN env.
- For HTML parsing, BeautifulSoup (bs4) and lxml are used if available.
