import os 
os.environ.setdefault("OTEL_SDK_DISABLED", "true")  # Disable OpenTelemetry SDK to suppress NoneType warnings
import logging
from .shared_libraries import constants
from .sub_agent.comparison.agent import comparison_root_agent
from .sub_agent.search_result.agent import search_result_agent
from .sub_agent.keyword_finding.agent import keyword_finding_agent
from pydantic import BaseModel
import requests
from google.adk.agents import LoopAgent, LlmAgent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.adk.tools import google_search
from google.genai import types
from dotenv import load_dotenv
import json
from .import prompt
load_dotenv()


logging.basicConfig(level=logging.INFO)
logging.getLogger("opentelemetry").setLevel(logging.ERROR)
logging.getLogger("opentelemetry.sdk").setLevel(logging.ERROR)
logging.getLogger("opentelemetry.semconv").setLevel(logging.ERROR)
logging.getLogger("google.adk.runners").setLevel(logging.ERROR)
logging.getLogger("google.genai.types").setLevel(logging.ERROR)
APP_NAME = "brand-SEO"
USER_ID = "user-1"
SESSION_ID = "session-001"

#create a session
session_service = InMemorySessionService()
session = session_service.create_session(
    app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
)

# Configure tools based on available credentials
ENABLE_WEB_SEARCH = bool(os.getenv("GOOGLE_CSE_ID") and os.getenv("GOOGLE_SEARCH_API_KEY"))

root_agent = LlmAgent(
    model = constants.MODEL,
    name= constants.ROOT_AGENT_NAME,
    description=constants.ROOT_AGENT_DESCRIPTION,
    instruction=prompt.ROOT_AGENT_INSTRUCTION,
    sub_agents=[
        comparison_root_agent,
        search_result_agent,
        keyword_finding_agent
    ],
)
 