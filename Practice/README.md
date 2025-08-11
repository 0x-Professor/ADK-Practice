# Practice Projects

Overview
- A set of small examples demonstrating Google ADK agent patterns:
  1) 1-basic-agent: minimal LlmAgent that greets the user.
  2) 2-tool_agent: LlmAgent with custom professional tools (Wikipedia, finance, UTM builder, date).
  3) 3-litellm_agent: shows using LiteLLM (OpenRouter) with an agent tool to create a joke.
  4) 4-structured-output: Pydantic schema-constrained output (email JSON).
  5) 5-session-and-state: reading session state in responses and basic async Runner usage.
  6) 6-persistant-storage: persistent sessions using DatabaseSessionService (SQLite) + stateful reminder agent.
  7) 7-multi-agent: a manager agent orchestrating multiple sub-agents and a local tool.

Install
- From repo root: uv sync

How to run
- Each subfolder contains a main.py or an importable agent; see its README for details.
- Some examples are console-based; others expose only agents to import.

Environment
- GENAI_MODEL: default model override (gemini-2.0-flash used otherwise).
- OPENROUTER_API_KEY: required for 3-litellm_agent.
- GOOGLE_CSE_ID and GOOGLE_SEARCH_API_KEY: enable google_search in 2-tool_agent and some sub-agents in 7-multi-agent.
