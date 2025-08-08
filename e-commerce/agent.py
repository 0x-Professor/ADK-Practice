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
    "You are a senior product research analyst using web search to produce accurate, source-backed findings with visuals. "
    "Always perform: (1) a general web search for authoritative sources; (2) an image-focused search using queries like '<topic> images'. "
    "Cross-check facts across at least 2 reputable sources. Cite titles and URLs. Avoid speculation. If uncertain, say so. "
    "Output format (in this exact order):\n"
    "1) Tailored Summary: A concise overview for the user’s query and intent.\n"
    "2) Detailed Findings: Bullet points with key specs, pros/cons, and comparisons.\n"
    "3) Sources: Bullet list of source titles with full URLs.\n"
    "4) DirectImageURLs (JSON): Provide a JSON object with 'image_urls' (<=6 direct .jpg/.png/.webp links) and 'page_urls' (<=6 related product/article URLs)." 
    " If a direct image is unavailable, include the closest page URL instead.\n"
    "5) Keep any rendered UI returned by tools (renderedContent) intact."
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
    "You are an e-commerce shopping advisor. Return professional, structured results with verified details and imagery. "
    "Use web search for candidates and a separate image-focused search ('<product> images'). "
    "Provide: (a) a buyer-focused summary; (b) a ranked list with prices, key specs, notable pros/cons; (c) a Sources list with URLs; "
    "(d) DirectImageURLs (JSON) containing 'image_urls' and 'page_urls' as separate arrays for UI use; prefer direct image links (.jpg/.jpeg/.png/.webp). "
    "Do not invent data."
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

def _extract_text_and_html(gen_content: Optional[types.Content]) -> tuple[str, str, list[str], list[str]]:
    """Extract text, rendered HTML, image URLs (direct), and page URLs.
    - Parses markdown images and generic URLs from text parts.
    - Attempts to read a JSON block with keys image_urls/page_urls if present.
    """
    if not gen_content or not getattr(gen_content, "parts", None):
        return "", "", [], []
    texts: list[str] = []
    htmls: list[str] = []
    image_urls_set: set[str] = set()
    page_urls_set: set[str] = set()
    for part in gen_content.parts:
        txt = getattr(part, "text", None)
        if isinstance(txt, str) and txt:
            texts.append(txt)
            # Parse markdown image URLs: ![alt](url)
            for m in re.findall(r"!\[[^\]]*\]\((https?[^\s)]+)\)", txt):
                image_urls_set.add(m)
            # Try parse JSON block with image_urls/page_urls
            for fence in re.findall(r"```json\s*([\s\S]*?)```", txt, flags=re.IGNORECASE):
                try:
                    obj = json.loads(fence)
                    if isinstance(obj, dict):
                        for u in obj.get("image_urls", []) or []:
                            if isinstance(u, str):
                                image_urls_set.add(u)
                        for u in obj.get("page_urls", []) or []:
                            if isinstance(u, str):
                                page_urls_set.add(u)
                except Exception:
                    pass
            # Generic URLs
            for u in re.findall(r"https?://[^\s)]+", txt):
                if _is_direct_image_url(u):
                    image_urls_set.add(u)
                else:
                    page_urls_set.add(u)
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
    return (
        "\n".join(texts).strip(),
        "\n".join(htmls).strip(),
        list(image_urls_set),
        list(page_urls_set),
    )

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
              .url-list { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 12px; }
              .url-list li { margin: 2px 0; }
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
            <h2>Image Gallery (markdown/JSON fallback)</h2>
            <div id="gallery"></div>
            <h2>Direct image URLs</h2>
            <ul id="imageUrls" class="url-list"></ul>
            <h2>Product/article URLs</h2>
            <ul id="pageUrls" class="url-list"></ul>
            <h2>Text / Markdown</h2>
            <div id="text"></div>
            <script>
              const f = document.getElementById('f');
              const q = document.getElementById('q');
              const status = document.getElementById('status');
              const html = document.getElementById('html');
              const gallery = document.getElementById('gallery');
              const imageUrls = document.getElementById('imageUrls');
              const pageUrls = document.getElementById('pageUrls');
              const text = document.getElementById('text');
              f.addEventListener('submit', async (e) => {
                e.preventDefault();
                status.textContent = 'Searching...';
                html.innerHTML = '';
                gallery.innerHTML = '';
                imageUrls.innerHTML = '';
                pageUrls.innerHTML = '';
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
                  const imgs = Array.isArray(data.image_urls) ? data.image_urls : (Array.isArray(data.images) ? data.images : []);
                  if (imgs.length) {
                    for (const u of imgs) {
                       const proxied = '/img?u=' + encodeURIComponent(u);
                       const a = document.createElement('a');
                       a.href = u; a.target = '_blank'; a.rel = 'noopener noreferrer';
                       const img = document.createElement('img');
                       img.loading = 'lazy'; img.decoding = 'async'; img.src = proxied; img.alt = 'product image';
                       a.appendChild(img);
                       gallery.appendChild(a);
                     }
                   }
                  // URL lists
                  (Array.isArray(data.image_urls) ? data.image_urls : []).forEach(u => {
                    const li = document.createElement('li');
                    const a = document.createElement('a'); a.href = u; a.textContent = u; a.target = '_blank'; a.rel = 'noopener';
                    li.appendChild(a); imageUrls.appendChild(li);
                  });
                  (Array.isArray(data.page_urls) ? data.page_urls : []).forEach(u => {
                    const li = document.createElement('li');
                    const a = document.createElement('a'); a.href = u; a.textContent = u; a.target = '_blank'; a.rel = 'noopener';
                    li.appendChild(a); pageUrls.appendChild(li);
                  });
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
    text, html, image_urls, page_urls = _extract_text_and_html(last_model_event_content)
    return {"text": text, "html": html, "images": image_urls, "image_urls": image_urls, "page_urls": page_urls}



