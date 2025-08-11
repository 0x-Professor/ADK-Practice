# Keyword Finding Sub-agent

Purpose
- Discovers brand-related keywords using the google_search tool and returns a ranked JSON list.

Files
- agent.py: keyword_finding_agent.
- prompt.py: JSON-only instruction with scoring and intent classification.

Output
- keyword_finding_agent -> keyword_research (JSON).

Env
- GOOGLE_CSE_ID, GOOGLE_SEARCH_API_KEY must be set to enable google_search.
