from __future__ import annotations

import os

# Prefer real ADK classes; define minimal fallbacks for static analysis if not installed
try:
    from google.adk.agents.llm_agent import Agent  # type: ignore
except Exception:  # pragma: no cover
    class Agent:  # minimal fallback stub
        def __init__(self, *args, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

try:
    from google.adk.tools.agent_tool import AgentTool  # type: ignore
except Exception:  # pragma: no cover
    class AgentTool:  # minimal fallback stub
        def __init__(self, name: str, description: str, tool):
            self.name = name
            self.description = description
            self.tool = tool

# Sub-agents
from .sub_agent.funny_nerd.agent import funny_nerd_agent
from .sub_agent.news_analyst.agent import news_analyst_agent
from .sub_agent.weather_forecaster.agent import weather_forecaster_agent
from .sub_agent.joke_teller.agent import joke_teller_agent

# Local tools
from .tools.tools import get_current_time

MODEL = os.getenv("GENAI_MODEL", "gemini-2.0-flash")

root_agent = Agent(
    model=MODEL,
    name="manager",
    description="Manager Agent",
    instruction=(
        "You are a manager agent that can assist users with various tasks.\n"
        "You can delegate tasks to sub-agents based on the user's request.\n"
        "You can also use tools to perform tasks that do not require sub-agents.\n"
        "If you don't know how to answer a question, you can delegate it to a sub-agent.\n"
        "If you don't know how to use a tool, ask the user for more information."
    ),
    sub_agents=[
        funny_nerd_agent,
        news_analyst_agent,
        weather_forecaster_agent,
        joke_teller_agent,
    ],
    tools=[
        # Register tool function directly per ADK API
        get_current_time,
    ],
)
