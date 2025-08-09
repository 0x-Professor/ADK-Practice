from google.adk.agents import LoopAgent, LlmAgent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
from ...shared_libraries import constants
from . import prompt

root_agent = LoopAgent(
    model=constants.MODEL,
    name=constants.ROOT_AGENT_NAME,
    description=constants.ROOT_AGENT_DESCRIPTION,
    instruction=constants.ROOT_AGENT_INSTRUCTION,
    sub_agents=[
        comparison_root_agent,
        search_result_agent,
        keyword_finding_agent
    ],
)
