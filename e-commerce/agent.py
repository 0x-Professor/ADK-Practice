import os 
import logging
import asyncio
from google.adk.agents import LoopAgent, LlmAgent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.adk.tools import ToolContext
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
    
"""
Custom function tools per ADK docs. Include optional tool_context: ToolContext to access context/actions when needed.
"""

async def google_image_search(query: str, num: int = 5, safe: str = "off", tool_context: ToolContext | None = None) -> str:
    """Search Google Custom Search for images related to a query. Returns JSON string with images."""
    cse_id = os.getenv("GOOGLE_CSE_ID")
    api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
    if not (cse_id and api_key):
        return json.dumps({"error": "missing_credentials", "message": "GOOGLE_CSE_ID and GOOGLE_SEARCH_API_KEY are required for image search."})
    params = {
        "q": query,
        "cx": cse_id,
        "key": api_key,
        "searchType": "image",
        "num": max(1, min(10, int(num))),
        "safe": safe,
    }
    try:
        r = requests.get("https://www.googleapis.com/customsearch/v1", params=params, timeout=20)
        r.raise_for_status()
        data = r.json()
        items = data.get("items", [])
        images = [
            {
                "title": it.get("title"),
                "link": it.get("link"),
                "contextLink": (it.get("image", {}) or {}).get("contextLink"),
                "thumbnailLink": (it.get("image", {}) or {}).get("thumbnailLink"),
            }
            for it in items
        ]
        return json.dumps({"query": query, "count": len(images), "images": images})
    except requests.HTTPError as e:
        return json.dumps({"error": "http_error", "status": r.status_code if 'r' in locals() else None, "detail": r.text if 'r' in locals() else str(e)})
    except Exception as e:
        return json.dumps({"error": "unknown_error", "message": str(e)})
 
async def google_web_search(query: str, num: int = 5, safe: str = "off", tool_context: ToolContext | None = None) -> str:
    """Search Google Programmable Search Engine for web results and return JSON string."""
    cse_id = os.getenv("GOOGLE_CSE_ID")
    api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
    if not (cse_id and api_key):
        return json.dumps({"error": "missing_credentials", "message": "GOOGLE_CSE_ID and GOOGLE_SEARCH_API_KEY are required for web search."})
    params = {
        "q": query,
        "cx": cse_id,
        "key": api_key,
        "num": max(1, min(10, int(num))),
        "safe": safe,
    }
    try:
        r = requests.get("https://www.googleapis.com/customsearch/v1", params=params, timeout=20)
        r.raise_for_status()
        data = r.json()
        items = data.get("items", [])
        results = [
            {
                "title": it.get("title"),
                "link": it.get("link"),
                "snippet": it.get("snippet"),
                "displayLink": it.get("displayLink"),
            }
            for it in items
        ]
        return json.dumps({"query": query, "count": len(results), "results": results})
    except requests.HTTPError as e:
        return json.dumps({"error": "http_error", "status": r.status_code if 'r' in locals() else None, "detail": r.text if 'r' in locals() else str(e)})
    except Exception as e:
        return json.dumps({"error": "unknown_error", "message": str(e)})
 
def _fetch_image_for_title(title: str) -> str | None:
    cse_id = os.getenv("GOOGLE_CSE_ID")
    api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
    if not (cse_id and api_key and title):
        return None
    params = {
        "q": f"{title} product image",
        "cx": cse_id,
        "key": api_key,
        "searchType": "image",
        "num": 1,
        "safe": "off",
    }
    try:
        r = requests.get("https://www.googleapis.com/customsearch/v1", params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        it = (data.get("items") or [None])[0]
        return it.get("link") if it else None
    except Exception:
        return None
 
async def vector_search(query: str, rows: int | None = None, tool_context: ToolContext | None = None) -> str:
    """Query the product vector search backend and return matched items as JSON string."""
    url = os.getenv("VECTOR_SEARCH_URL")
    result = call_vector_search(url, query, rows)
    # Enrich with real images if missing and CSE creds available
    try:
        items = result.get("results") if isinstance(result, dict) else None
        if isinstance(items, list):
            for item in items:
                title = item.get("title") or item.get("name") or item.get("product_title") or query
                image_url = item.get("image_url") or item.get("image") or item.get("thumbnail")
                if not image_url:
                    fetched = _fetch_image_for_title(str(title))
                    if fetched:
                        item["image_url"] = fetched
        return json.dumps(result)
    except Exception:
        return json.dumps(result)
 
def _expand_queries(q: str) -> list[str]:
    q = (q or "").strip()
    if not q:
        return []
    base = q
    return [
        base,
        f"{base} best price",
        f"{base} latest model",
        f"{base} reviews",
        f"buy {base} online",
    ]
 
async def multi_query_vector_search(user_query: str, rows: int = 5, tool_context: ToolContext | None = None) -> str:
    """Generate 5 diverse queries, run vector search for each, and aggregate results as JSON string."""
    url = os.getenv("VECTOR_SEARCH_URL")
    if not url:
        return json.dumps({"error": "missing_url", "message": "VECTOR_SEARCH_URL is not set."})
    queries = _expand_queries(user_query)
    aggregated = []
    seen_ids = set()
    for q in queries:
        res = call_vector_search(url, q, rows)
        results = (res or {}).get("results") if isinstance(res, dict) else None
        if isinstance(results, list):
            unique = []
            for it in results:
                uid = it.get("id") or it.get("title") or it.get("name")
                if uid and uid in seen_ids:
                    continue
                if uid:
                    seen_ids.add(uid)
                unique.append(it)
            res["results"] = unique
        aggregated.append({"query": q, "results": res})
    return json.dumps({"generated_queries": queries, "results_by_query": aggregated})
 
# Configure tools based on available credentials
ENABLE_WEB_SEARCH = bool(os.getenv("GOOGLE_CSE_ID") and os.getenv("GOOGLE_SEARCH_API_KEY"))
 
# Research agent with web and image search capabilities
research_instruction = (
    "You are a research agent that can search the web and images to collect product info, comparisons, and visual references."
)
research_tools = []
if ENABLE_WEB_SEARCH:
    research_tools = [google_web_search, google_image_search]
 
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
    "Use the vector_search tool for precise retrieval. When helpful, use multi_query_vector_search "
    "to broaden recall and then summarize the top matches for the user."
)
 
shop_agent = LlmAgent(
    name="shop_agent",
    model='gemini-2.0-flash',
    description=("Searches for items based on user queries and returns results."),
    instruction=shop_instruction,
    tools=[vector_search, multi_query_vector_search],
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



