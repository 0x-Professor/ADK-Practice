# 7-multi-agent

Purpose
- Demonstrates a manager agent orchestrating multiple sub-agents and a local time tool.

Run
- python main.py (interactive console)

Agents
- funny_nerd: light, nerdy responses.
- news_analyst: concise news summaries; optionally uses google_search when credentials exist.
- weather_forecaster: uses Open-Meteo tool get_weather.
- joke_teller: short, clean jokes.

Notes
- The manager registers get_current_time_tool for formatting current time with optional timezone.
- GENAI_MODEL can override the default model.
