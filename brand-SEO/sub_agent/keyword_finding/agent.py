from google.adk.agents import LoopAgent, LlmAgent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.adk.tools import google_search
from google.genai import types
from ...shared_libraries import constants
from . import prompt

keyword_finding_agent = LlmAgent(
    model = constants.MODEL,
    name = "keyword_finding_agent",
    description= "A helpful agent to find keywords",
    instruction=prompt.KEYWORD_FINDING_AGENT_PROMPT,
    tools=[google_search]
)