import os 
import logging
import asyncio
from google.adk.agents import LoopAgent, LlmAgent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.adk.tools import ToolContext, google_search
from google.genai import types
from dotenv import load_dotenv
import requests
import json
from typing import Any
load_dotenv()


logging.basicConfig(level=logging.INFO)
logging.getLogger("google.adk.runners").setLevel(logging.ERROR)
logging.getLogger("google.genai.types").setLevel(logging.ERROR)
APP_NAME = "e-commerce-agent"
USER_ID = "user-1"
SESSION_ID = "session-001"

#create a session
session_service = InMemorySessionService()
session = session_service.create_session(
    app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
)

# Define call_vector_search to call the vector search backend.
def call_vector_search(url,query, rows= None):
    """Calls the vector search backend fro querying
    Args: 
        url (str): The URL of the vector search backend.
        query (str): The search query.
        rows (int, optional): The number of results to return. Defaults to None.
        Returns:
        dict: the json response from the api"""
        
        #Build HTTP header and a payload
    headers = {'Content-Type': 'application/json'}
    payload = {
        "query": query,
        "rows": rows,
        "dataset_id": "mercari3m_mm",
        "use-dense": True,
        "use-sparse": True,
        "use_rerank": True,
        "rrf_alpha": 0.5,
        
        
        }
    #complete this code 
    try:
        if not url:
            raise ValueError("Vector search URL is required.")
        resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=20)
        resp.raise_for_status()
        return resp.json()
    except requests.Timeout:
        return {"error": "timeout", "message": "Vector search request timed out."}
    except requests.HTTPError as e:
        # Try to include server-provided error details
        try:
            detail = resp.json()
        except Exception:
            detail = resp.text
        return {"error": "http_error", "status_code": resp.status_code if 'resp' in locals() else None, "detail": detail, "message": str(e)}
    except Exception as e:
        return {"error": "unknown_error", "message": str(e)}
    
async def vector_search(query: str, tool_context: ToolContext, rows: int = 10) -> str:
    """Query the product vector search backend and return matched items as a JSON string.

    Parameters:
      - query: Natural language search query
      - rows: Number of results to return (default 10)
    """
    url = os.getenv("VECTOR_SEARCH_URL")
    result = call_vector_search(url, query, rows)
    return json.dumps(result)
 
# Configure tools based on available credentials
ENABLE_WEB_SEARCH = bool(os.getenv("GOOGLE_CSE_ID") and os.getenv("GOOGLE_SEARCH_API_KEY"))
 
# Research agent with web and image search capabilities
research_instruction = (
    "You are a research agent that can search the web and images to collect product info, comparisons, and visual references."
)
research_tools = []
if ENABLE_WEB_SEARCH:
    # Use built-in web search tool
    research_tools = [google_search]
 
research_agent = LlmAgent(
    name="research_agent",
    model='gemini-2.0-flash',
    description=("Searches the web and image sources to gather information and visual assets."),
    instruction=research_instruction,
    tools=research_tools,
)
 
# Shop agent finalized to use vector search backend and multi-query expansion
shop_instruction  = (
    "You are a shop search agent on an e-commerce site with millions of items. "
    "Use the vector_search tool for precise retrieval. Summarize the top matches for the user."
)
 
shop_agent = LlmAgent(
    name="shop_agent",
    model='gemini-2.0-flash',
    description=("Searches for items based on user queries and returns results."),
    instruction=shop_instruction,
    tools=[vector_search],
)
 
# Expose root_agent for ADK loader
e_commerce_root = LoopAgent(
    name="e_commerce_root",
    max_iterations=2,
    sub_agents=[
        shop_agent,
        research_agent,
    ],
)
 
root_agent  = e_commerce_root



