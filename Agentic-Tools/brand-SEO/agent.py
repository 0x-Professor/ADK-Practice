import os 
os.environ.setdefault("OTEL_SDK_DISABLED", "true")  # Disable OpenTelemetry SDK to suppress NoneType warnings
import logging
from .shared_libraries import constants
from .sub_agent.comparison.agent import comparison_root_agent
from .sub_agent.search_result.agent import search_result_agent
from .sub_agent.keyword_finding.agent import keyword_finding_agent
from google.adk.agents import LlmAgent
from dotenv import load_dotenv
from . import prompt
load_dotenv()


logging.basicConfig(level=logging.INFO)
logging.getLogger("opentelemetry").setLevel(logging.ERROR)
logging.getLogger("opentelemetry.sdk").setLevel(logging.ERROR)
logging.getLogger("opentelemetry.semconv").setLevel(logging.ERROR)
logging.getLogger("google.adk.runners").setLevel(logging.ERROR)
logging.getLogger("google.genai.types").setLevel(logging.ERROR)

# Root LLM orchestrator that MUST call all sub-agents in order per prompt
root_agent = LlmAgent(
    name=constants.ROOT_AGENT_NAME,
    model=constants.MODEL,
    description=constants.ROOT_AGENT_DESCRIPTION,
    instruction=prompt.ROOT_AGENT_INSTRUCTION,
    sub_agents=[
        # discovery -> SERP -> comparison sequence
        keyword_finding_agent,
        search_result_agent,
        comparison_root_agent,
    ],
)
