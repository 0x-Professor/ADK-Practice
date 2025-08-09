from google.adk.agents import LoopAgent, LlmAgent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.adk.tools import google_search
from google.genai import types
from ...shared_libraries import constants
from . import prompt

search_result_agent = LlmAgent(
    model=constants.MODEL,
    name="search_result_agent",
    description="An agent to fetch search results for a given keyword and brand.",
    instruction=prompt.SEARCH_RESULT_AGENT_PROMPT,
    tools = [
        go_to_url,
        take_screenshot,
        find_element_with_text,
        click_element_with_text,
        enter_text_into_element,
        scroll_down_screen,
        load_artifacts_tool,
        analyze_webpage_and_determine_actions,
        
    ],
)