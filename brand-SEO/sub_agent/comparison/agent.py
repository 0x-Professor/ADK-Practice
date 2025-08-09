from google.adk.agents import LlmAgent
from ...shared_libraries import constants
from . import prompt

# Leaf agents
comparison_agent = LlmAgent(
    model=constants.MODEL,
    name="comparison_agent",
    description="Analyzes brand vs competitors for a keyword and outputs a JSON report.",
    instruction=prompt.COMPARISON_AGENT_PROMPT,
)

comparison_critic_agent = LlmAgent(
    model=constants.MODEL,
    name="comparison_critic_agent",
    description="Critiques and minimally revises a comparison report to ensure quality and schema compliance.",
    instruction=prompt.COMPARISON_CRITIC_AGENT_PROMPT,
)

# Orchestrator for comparison
comparison_root_agent = LlmAgent(
    model=constants.MODEL,
    name="comparison_root_agent",
    description="Orchestrates comparison and critique to produce a final comparison report.",
    instruction=prompt.COMPARISON_ROOT_AGENT_PROMPT,
    sub_agents=[comparison_agent, comparison_critic_agent],
)
