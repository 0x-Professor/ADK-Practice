import os 
os.environ.setdefault("OTEL_SDK_DISABLED", "true")  # Disable OpenTelemetry SDK to suppress NoneType warnings
import logging
import asyncio
import base64
import re
from typing import Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
import requests
from google.adk.agents import LoopAgent, LlmAgent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.adk.tools import google_search
from google.genai import types
from dotenv import load_dotenv
import json
load_dotenv()


logging.basicConfig(level=logging.INFO)
logging.getLogger("opentelemetry").setLevel(logging.ERROR)
logging.getLogger("opentelemetry.sdk").setLevel(logging.ERROR)
logging.getLogger("opentelemetry.semconv").setLevel(logging.ERROR)
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

# Configure tools based on available credentials
ENABLE_WEB_SEARCH = bool(os.getenv("GOOGLE_CSE_ID") and os.getenv("GOOGLE_SEARCH_API_KEY"))
 
# Research agent with web and image search capabilities
research_instruction = (
    "You are a research agent that can search the web to collect product info, comparisons, and visual references. "
    "When users ask for products, also search for images (e.g., run google_search with '<query> images'). "
    "In your response, include an Images section that lists 1–3 representative image links per product using markdown, e.g., ![alt](image_url). "
    "Prefer direct image URLs or clearly labeled page links if image URLs are unavailable."
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
 
# Shop agent using only web search
shop_instruction  = (
    "You are a shop search agent on an e-commerce site with millions of items. "
    "Use web search to find relevant products and summarize the top matches for the user. "
    "Also include product images: perform an additional image-oriented search (e.g., '<product> images') and attach up to 3 image URLs per product using markdown image tags (![alt](url))."
)
 
shop_agent = LlmAgent(
    name="shop_agent",
    model='gemini-2.0-flash',
    description=("Searches for items based on user queries and returns results."),
    instruction=shop_instruction,
    tools=research_tools,
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

# --- FastAPI app to render search results with images (HTML + gallery fallback) ---
app = FastAPI(title="ADK E-commerce Search UI", version="0.1.0")

class QueryIn(BaseModel):
    query: str
    user_id: Optional[str] = "user-1"
    session_id: Optional[str] = "session-001"

def _extract_text_and_html(gen_content: Optional[types.Content]) -> tuple[str, str, list[str]]:
    """Extract text, rendered HTML, and image URLs parsed from markdown."""
    if not gen_content or not getattr(gen_content, "parts", None):
        return "", "", []
    texts: list[str] = []
    htmls: list[str] = []
    images: list[str] = []
    for part in gen_content.parts:
        txt = getattr(part, "text", None)
        if isinstance(txt, str) and txt:
            texts.append(txt)
            for m in re.findall(r"!\[[^\]]*\]\((https?[^\s)]+)\)", txt):
                images.append(m)
        for maybe_html_attr in ("rendered_content", "renderedContent", "html"):
            h = getattr(part, maybe_html_attr, None)
            if isinstance(h, str) and h:
                htmls.append(h)
        inline = getattr(part, "inline_data", None)
        if inline is not None:
            mt = getattr(inline, "mime_type", None)
            data = getattr(inline, "data", None)
            if mt in ("text/html", "application/html") and data:
                try:
                    if isinstance(data, (bytes, bytearray)):
                        htmls.append(data.decode("utf-8", errors="ignore"))
                    elif isinstance(data, str):
                        htmls.append(base64.b64decode(data).decode("utf-8", errors="ignore"))
                except Exception:
                    pass
    return ("\n".join(texts).strip(), "\n".join(htmls).strip(), images)

def _is_direct_image_url(u: str) -> bool:
    u = u.lower()
    return any(u.endswith(ext) for ext in (".jpg", ".jpeg", ".png", ".webp", ".gif"))

@app.get("/img")
def proxy_image(u: str):
    # Lightweight proxy to avoid hotlink issues. Not production-hardened.
    if not (u.startswith("http://") or u.startswith("https://")):
        raise HTTPException(status_code=400, detail="Invalid URL")
    try:
        resp = requests.get(u, timeout=10, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
        })
        ct = resp.headers.get("Content-Type", "application/octet-stream")
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail="Upstream error")
        if not ct.startswith("image/") and not _is_direct_image_url(u):
            raise HTTPException(status_code=415, detail="Not an image")
        return Response(content=resp.content, media_type=ct)
    except requests.Timeout:
        raise HTTPException(status_code=504, detail="Image fetch timeout")
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))

@app.get("/")
async def index():
    return (
        """
        <!doctype html>
        <html>
          <head>
            <meta charset="utf-8" />
            <title>ADK Search with Images</title>
            <style>
              body { font-family: system-ui, sans-serif; margin: 1.5rem; }
              #html { border: 1px solid #ddd; padding: 1rem; margin-top: 1rem; }
              #text { white-space: pre-wrap; border: 1px solid #eee; padding: 1rem; margin-top: 1rem; }
              #gallery { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 12px; margin-top: 1rem; }
              #gallery img { width: 100%; height: 140px; object-fit: cover; border: 1px solid #ddd; border-radius: 6px; }
            </style>
          </head>
          <body>
            <h1>Search Products (with Images)</h1>
            <form id="f">
              <input id="q" name="q" placeholder="e.g., budget gaming laptops images" style="width: 420px;" />
              <button>Search</button>
            </form>
            <div id="status"></div>
            <h2>Rendered HTML</h2>
            <div id="html"></div>
            <h2>Image Gallery (markdown fallback)</h2>
            <div id="gallery"></div>
            <h2>Text / Markdown</h2>
            <div id="text"></div>
            <script>
              const f = document.getElementById('f');
              const q = document.getElementById('q');
              const status = document.getElementById('status');
              const html = document.getElementById('html');
              const gallery = document.getElementById('gallery');
              const text = document.getElementById('text');
              f.addEventListener('submit', async (e) => {
                e.preventDefault();
                status.textContent = 'Searching...';
                html.innerHTML = '';
                gallery.innerHTML = '';
                text.textContent = '';
                try {
                  const resp = await fetch('/query', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query: q.value })
                  });
                  const data = await resp.json();
                  status.textContent = data.error ? ('Error: ' + data.error) : 'Done';
                  if (data.html) html.innerHTML = data.html; // Render HTML snippet with images
                  if (Array.isArray(data.images)) {
                    for (const u of data.images) {
                      const proxied = '/img?u=' + encodeURIComponent(u);
                      const a = document.createElement('a');
                      a.href = u; a.target = '_blank'; a.rel = 'noopener noreferrer';
                      const img = document.createElement('img');
                      img.loading = 'lazy'; img.decoding = 'async'; img.src = proxied; img.alt = 'product image';
                      a.appendChild(img);
                      gallery.appendChild(a);
                    }
                  }
                  if (data.text) text.textContent = data.text; // Fallback text/markdown
                } catch (err) {
                  status.textContent = 'Request failed';
                }
              });
            </script>
          </body>
        </html>
        """
    )

from google.adk.runners import InMemoryRunner

@app.post("/query")
async def query(body: QueryIn):
    if root_agent is None:
        raise HTTPException(status_code=500, detail="Agent not loaded")
    runner = InMemoryRunner(agent=root_agent, app_name="adk-ecommerce-web")
    user_msg = types.Content(role="user", parts=[types.Part(text=body.query)])
    last_model_event_content: Optional[types.Content] = None
    try:
        for event in runner.run(
            user_id=body.user_id or "user-1",
            session_id=body.session_id or "session-001",
            new_message=user_msg,
        ):
            if getattr(event, "author", None) and event.author != "user":
                last_model_event_content = getattr(event, "content", None)
    except Exception as e:
        logging.exception("Agent run failed")
        raise HTTPException(status_code=500, detail=str(e))
    text, html, images = _extract_text_and_html(last_model_event_content)
    return {"text": text, "html": html, "images": images}



