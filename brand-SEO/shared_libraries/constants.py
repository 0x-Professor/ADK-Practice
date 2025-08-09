"""Define Constants for the brand-SEO application."""

import os
from dotenv import load_dotenv
load_dotenv()

# Agent names must be valid identifiers (letters, digits, underscores)
ROOT_AGENT_NAME = "brand_seo_root_agent"
ROOT_AGENT_DESCRIPTION = "This agent manages the brand SEO tasks including comparison, search results, and keyword finding."
# Use a model name, not an API key. Allow override via GENAI_MODEL env.
MODEL = os.getenv("GENAI_MODEL", "gemini-2.0-flash")
ROOT_AGENT_INSTRUCTION = (
    """You are a Brand SEO Root Agent. Your task is to manage sub-agents that handle comparison, search results, and keyword finding. 
    You will coordinate these tasks and provide insights based on the results from the sub-agents.
    Ensure that the sub-agents are utilized effectively to achieve the best SEO outcomes for the brand.
    You will also handle any errors or issues that arise during the execution of these tasks.
    If you encounter any problems, please log them and provide a summary of the issue."""
)