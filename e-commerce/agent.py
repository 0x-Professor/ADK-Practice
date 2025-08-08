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
    "You are a senior product research analyst. Produce accurate, source-backed findings with structured product links. "
    "Always: perform a general web search for authoritative sources, cross-check facts across >=2 reputable sources, and cite titles + URLs. "
    "Do NOT include any image URLs. If users ask for pictures, instead provide the correct product page links from manufacturers/retailers. "
    "Output format (in this exact order):\n"
    "1) Tailored Summary: Concise overview addressing the user’s intent.\n"
    "2) Detailed Findings: Bulleted key specs, pros/cons, and comparisons.\n"
    "3) Sources: Bulleted list of source titles with full URLs.\n"
    "4) Products (JSON): A fenced JSON block with key 'products' as an array of objects. Each object MUST include: "
    "   item_number (or sku if available), title, product_url, seller_or_brand, price (if available), key_specs (array), and any identifiers like upc/ean if present.\n"
    "5) RelatedURLs (JSON): Optionally include 'page_urls' as an array of relevant non-image links.\n"
    "Keep any rendered UI returned by tools (renderedContent) intact."
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
    "You are an e-commerce shopping advisor. Return professional, structured results with verified details. "
    "Do NOT include image URLs. Provide only correct product page links with item numbers/SKUs. "
    "Provide: (a) a buyer-focused summary; (b) a ranked list with prices, key specs, notable pros/cons; (c) a Sources list with URLs; "
    "(d) Products (JSON) as a fenced block: an array of objects with fields item_number (or sku), title, product_url, seller_or_brand, price, key_specs (array), rating if available. "
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

def _extract_text_and_html(gen_content: Optional[types.Content]) -> tuple[str, str, list[dict[str, Any]], list[str]]:
    """Extract text, rendered HTML, Products array (if provided in JSON), and related page URLs.
    - Parses fenced JSON blocks for key 'products' and optional 'page_urls'.
    - Also gathers non-image URLs from text parts into page_urls.
    """
    if not gen_content or not getattr(gen_content, "parts", None):
        return "", "", [], []
    texts: list[str] = []
    htmls: list[str] = []
    page_urls_set: set[str] = set()
    products: list[dict[str, Any]] = []
    for part in gen_content.parts:
        txt = getattr(part, "text", None)
        if isinstance(txt, str) and txt:
            texts.append(txt)
            # Try parse JSON fences for products/page_urls
            for fence in re.findall(r"```json\s*([\s\S]*?)```", txt, flags=re.IGNORECASE):
                try:
                    obj = json.loads(fence)
                    if isinstance(obj, dict):
                        if isinstance(obj.get("products"), list):
                            for p in obj.get("products", []) or []:
                                if isinstance(p, dict):
                                    products.append(p)
                        for u in obj.get("page_urls", []) or []:
                            if isinstance(u, str):
                                page_urls_set.add(u)
                except Exception:
                    pass
            # Generic URLs
            for u in re.findall(r"https?://[^\s)]+", txt):
                if not _is_direct_image_url(u):
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
        products,
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
            <title>ADK Chat</title>
            <style>
              :root {
                --bg: #ffffff;
                --bubble-user: #e6f0ff;
                --bubble-assistant: #f6f6f6;
                --text: #111;
                --muted: #666;
              }
              body { font-family: system-ui, sans-serif; margin: 0; background: var(--bg); color: var(--text); }
              header { position: sticky; top: 0; background: #fff; border-bottom: 1px solid #eee; padding: 12px 16px; }
              main { padding: 16px; display: grid; justify-content: center; }
              #chat { width: min(900px, 100%); display: flex; flex-direction: column; gap: 12px; }
              .msg { max-width: 80%; padding: 10px 12px; border-radius: 14px; line-height: 1.35; box-shadow: 0 1px 1px rgba(0,0,0,0.05); }
              .msg.user { align-self: flex-end; background: var(--bubble-user); }
              .msg.assistant { align-self: flex-start; background: var(--bubble-assistant); }
              .msg .role { font-size: 12px; color: var(--muted); margin-bottom: 4px; }
              .msg pre { margin: 6px 0 0; white-space: pre-wrap; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 13px; }
              .images { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 8px; margin-top: 8px; }
              .images a { display: block; }
              .images img { width: 100%; height: 140px; object-fit: cover; border-radius: 10px; border: 1px solid #ddd; background: #fff; }
              form#f { position: sticky; bottom: 0; background: #fff; border-top: 1px solid #eee; padding: 12px 16px; display: grid; grid-template-columns: 1fr auto; gap: 8px; }
              #q { padding: 10px 12px; border: 1px solid #ddd; border-radius: 10px; font-size: 14px; }
              button { padding: 10px 16px; border: 1px solid #2b6; background: #2b6; color: #fff; border-radius: 10px; cursor: pointer; }
              #status { font-size: 12px; color: var(--muted); margin-top: 6px; }
            </style>
          </head>
          <body>
            <header>
              <strong>ADK E-commerce Assistant</strong>
              <div id="status"></div>
            </header>
            <main>
              <div id="chat"></div>
            </main>
            <form id="f">
-              <input id="q" name="q" placeholder="Ask about products, include 'images' to see visuals" autocomplete="off" />
+              <input id="q" name="q" placeholder="Ask about products. I will return structured product links with item numbers/SKUs." autocomplete="off" />
               <button>Send</button>
             </form>
            <script>
              const chat = document.getElementById('chat');
              const f = document.getElementById('f');
              const q = document.getElementById('q');
              const status = document.getElementById('status');
 
              function addMsg(role, data) {
                const wrap = document.createElement('div');
                wrap.className = 'msg ' + (role === 'user' ? 'user' : 'assistant');
                const roleEl = document.createElement('div');
                roleEl.className = 'role';
                roleEl.textContent = role === 'user' ? 'You' : 'Assistant';
                wrap.appendChild(roleEl);
 
                if (data && data.html) {
                  const div = document.createElement('div');
                  div.innerHTML = data.html;
                  wrap.appendChild(div);
                }
                if (data && data.text) {
                  const pre = document.createElement('pre');
                  pre.textContent = data.text;
                  wrap.appendChild(pre);
                }
+                // Render structured products as a list (no image URLs)
+                if (data && Array.isArray(data.products) && data.products.length) {
+                  const list = document.createElement('div');
+                  for (const p of data.products) {
+                    const card = document.createElement('div');
+                    card.style.border = '1px solid #eee';
+                    card.style.borderRadius = '10px';
+                    card.style.padding = '8px 10px';
+                    card.style.marginTop = '8px';
+                    const title = document.createElement('div');
+                    const a = document.createElement('a');
+                    a.href = p.product_url || '#'; a.target = '_blank'; a.rel = 'noopener noreferrer';
+                    a.textContent = p.title || p.product_url || 'Product';
+                    title.appendChild(a);
+                    const meta = document.createElement('div');
+                    meta.style.fontSize = '12px'; meta.style.color = '#555';
+                    const parts = [];
+                    if (p.item_number || p.sku) parts.push('Item: ' + (p.item_number || p.sku));
+                    if (p.seller_or_brand) parts.push('Seller/Brand: ' + p.seller_or_brand);
+                    if (p.price) parts.push('Price: ' + p.price);
+                    if (p.rating) parts.push('Rating: ' + p.rating);
+                    meta.textContent = parts.join(' • ');
+                    const specs = document.createElement('ul');
+                    if (Array.isArray(p.key_specs)) {
+                      for (const s of p.key_specs) {
+                        const li = document.createElement('li'); li.textContent = s; specs.appendChild(li);
+                      }
+                    }
+                    card.appendChild(title);
+                    card.appendChild(meta);
+                    if (specs.childElementCount) card.appendChild(specs);
+                    list.appendChild(card);
+                  }
+                  wrap.appendChild(list);
+                }
+                // Related links (non-image URLs)
+                if (data && Array.isArray(data.page_urls) && data.page_urls.length) {
+                  const ul = document.createElement('ul');
+                  for (const u of data.page_urls) {
+                    const li = document.createElement('li');
+                    const a = document.createElement('a'); a.href = u; a.textContent = u; a.target = '_blank'; a.rel = 'noopener';
+                    li.appendChild(a); ul.appendChild(li);
+                  }
+                  wrap.appendChild(ul);
+                }
                 chat.appendChild(wrap);
                 window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
               }
 
               f.addEventListener('submit', async (e) => {
                 e.preventDefault();
                 const prompt = q.value.trim();
                 if (!prompt) return;
                 addMsg('user', { text: prompt });
                 q.value = '';
                 status.textContent = 'Working...';
                 try {
                   const resp = await fetch('/query', {
                     method: 'POST',
                     headers: { 'Content-Type': 'application/json' },
                     body: JSON.stringify({ query: prompt })
                   });
                   const data = await resp.json();
                   if (data && data.error) {
                     status.textContent = 'Error: ' + data.error;
                   } else {
                     status.textContent = '';
                     addMsg('assistant', data);
                   }
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
    text, html, products, page_urls = _extract_text_and_html(last_model_event_content)
    return {"text": text, "html": html, "products": products, "page_urls": page_urls}



