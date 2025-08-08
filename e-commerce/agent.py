import os 
import logging
import asyncio
from google.adk.agents import Agent, LoopAgent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.adk.tools.agent_tool import AgentTool
from google.genai import types
from dotenv import load_dotenv
import requests
import json
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

async def test_agent(query, agent):
    """Sends a query to the agent and prints the final response."""
    print(f"Query: {query}")
    
    #create a runner
    runner = Runner(
        session_service=session_service,
        agent=agent,
        app_name=APP_NAME,
        
    )
    content  = types.Content(role = 'user', parts = [types.Part(text=query)])
    
    final_response_text = None
    
    #we iterate through events from run_async to find the final answer
    async for event in runner.run_async(user_id=USER_ID, session_id=SESSION_ID, new_message=content):
        if event.is_final_response():
            if event.content and event.content.parts:
                final_response_text = event.content.parts[0].text
            break
    print(f"Final Response: {final_response_text}")

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
    
#add another research agent using the google search tool that must be capable of searching the web and also searching for the required image data 
from google.adk.tools import google_search

class GoogleImageSearchTool(AgentTool):
    name = "google_image_search"
    description = (
        "Search Google Custom Search for images related to a query. Returns a list of image results with URLs."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Query to search images for"},
            "num": {"type": "integer", "description": "Number of images to return (1-10)", "minimum": 1, "maximum": 10, "default": 5},
            "safe": {"type": "string", "enum": ["off", "medium", "high"], "default": "off"}
        },
        "required": ["query"]
    }

    async def run(self, query: str, num: int = 5, safe: str = "off"):
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

#finalize the shop agent to use the vector search backend
class VectorSearchTool(AgentTool):
    name = "vector_search"
    description = "Query the product vector search backend and return matched items."
    input_schema = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Natural language search query"},
            "rows": {"type": "integer", "description": "Number of results to return"}
        },
        "required": ["query"]
    }

    @staticmethod
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

    async def run(self, query: str, rows: int | None = None):
        url = os.getenv("VECTOR_SEARCH_URL")
        result = call_vector_search(url, query, rows)
        # Enrich with real images if missing and CSE creds available
        try:
            items = result.get("results") if isinstance(result, dict) else None
            if isinstance(items, list):
                for item in items:
                    # Common keys for title/name
                    title = item.get("title") or item.get("name") or item.get("product_title") or query
                    # Common keys that may hold image urls
                    image_url = item.get("image_url") or item.get("image") or item.get("thumbnail")
                    if not image_url:
                        fetched = self._fetch_image_for_title(str(title))
                        if fetched:
                            item["image_url"] = fetched
            return json.dumps(result)
        except Exception:
            # If enrichment fails, still return raw result
            return json.dumps(result)

# add the a tool that will generate 5 queries on the basis of the user query and then call the vector search backend to get the results
class MultiQueryVectorSearchTool(AgentTool):
    name = "multi_query_vector_search"
    description = (
        "Generate 5 diverse queries based on a user query and execute vector search for each. Returns aggregated results."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "user_query": {"type": "string", "description": "Original user query"},
            "rows": {"type": "integer", "description": "Results per query", "default": 5}
        },
        "required": ["user_query"]
    }

    @staticmethod
    def _expand_queries(q: str) -> list[str]:
        q = (q or "").strip()
        if not q:
            return []
        # Simple heuristic expansions to diversify intent
        base = q
        return [
            base,
            f"{base} best price",
            f"{base} latest model",
            f"{base} reviews",
            f"buy {base} online",
        ]

    async def run(self, user_query: str, rows: int = 5):
        url = os.getenv("VECTOR_SEARCH_URL")
        if not url:
            return json.dumps({"error": "missing_url", "message": "VECTOR_SEARCH_URL is not set."})
        queries = self._expand_queries(user_query)
        aggregated = []
        seen_ids = set()
        for q in queries:
            res = call_vector_search(url, q, rows)
            # Deduplicate by id/title to make it cleaner for production
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
    research_tools = [google_search, GoogleImageSearchTool]

research_agent = Agent(
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

shop_agent = Agent(
    name="shop_agent",
    model='gemini-2.0-flash',
    description=("Searches for items based on user queries and returns results."),
    instruction=shop_instruction,
    tools=[VectorSearchTool, MultiQueryVectorSearchTool],
)

# Expose root_agent for ADK loader
root_agent = LoopAgent(
    name="e_commerce_root",
    max_iterations=2,
    sub_agents=[
        shop_agent,
        research_agent,
    ],
)



