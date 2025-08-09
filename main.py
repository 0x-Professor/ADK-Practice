from __future__ import annotations

import base64
import importlib.util
import logging
from pathlib import Path
from typing import Optional
import re
import os

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
import urllib.parse
import requests
from dotenv import load_dotenv

from google.adk.runners import InMemoryRunner
from google.genai import types

# Load environment variables from .env
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("adk_practice.web")

PROJECT_ROOT = Path(__file__).parent

# --- Dynamically load both agents (folders may contain hyphens) ---
AGENTS: dict[str, object] = {}

# e-commerce
try:
    ecom_path = PROJECT_ROOT / "e-commerce" / "agent.py"
    if ecom_path.exists():
        spec = importlib.util.spec_from_file_location("e_commerce_agent_module", ecom_path)
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)  # type: ignore[attr-defined]
            root = getattr(mod, "root_agent", None)
            if root is not None:
                AGENTS["ecommerce"] = root
            else:
                logger.warning("e-commerce root_agent not found in %s", ecom_path)
    else:
        logger.info("e-commerce agent file not found: %s", ecom_path)
except Exception:
    logger.exception("Failed to load e-commerce agent")

# brand-SEO
try:
    bseo_path = PROJECT_ROOT / "brand-SEO" / "agent.py"
    if bseo_path.exists():
        spec = importlib.util.spec_from_file_location("brand_seo_agent_module", bseo_path)
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)  # type: ignore[attr-defined]
            root = getattr(mod, "root_agent", None)
            if root is not None:
                AGENTS["brand-seo"] = root
            else:
                logger.warning("brand-SEO root_agent not found in %s", bseo_path)
    else:
        logger.info("brand-SEO agent file not found: %s", bseo_path)
except Exception:
    logger.exception("Failed to load brand-SEO agent")

if not AGENTS:
    logger.error("No agents loaded. Check project files.")

DEFAULT_MODE = os.getenv("APP_AGENT", "ecommerce").lower()
if DEFAULT_MODE not in AGENTS:
    # Fallback to any available agent
    DEFAULT_MODE = next(iter(AGENTS.keys()))
    logger.warning("APP_AGENT not available; defaulting to %s", DEFAULT_MODE)

# Proactive env guidance
if "brand-seo" in AGENTS:
    if not (os.getenv("GOOGLE_CSE_ID") and os.getenv("GOOGLE_SEARCH_API_KEY")):
        logger.warning("[brand-seo] GOOGLE_CSE_ID/GOOGLE_SEARCH_API_KEY not set; keyword_finding and SERP tools may be limited.")
    if os.getenv("HEADLESS") in (None, "",):
        logger.info("[brand-seo] HEADLESS defaults to 1 for Selenium. Set HEADLESS=1 on servers without display.")

# --- FastAPI app ---
app = FastAPI(title="ADK Practice Search UI", version="0.2.0")


class QueryIn(BaseModel):
    query: str
    mode: Optional[str] = None  # "ecommerce" | "brand-seo"
    user_id: Optional[str] = "user-1"
    session_id: Optional[str] = "session-001"


def _extract_text_and_html(gen_content: Optional[types.Content]) -> tuple[str, str, list[str]]:
    """Extract concatenated text and any HTML-like rendered content.
    Tries multiple known locations for rendered HTML returned by Gemini 2.
    """
    if not gen_content or not getattr(gen_content, "parts", None):
        return "", "", []

    texts: list[str] = []
    htmls: list[str] = []
    images: list[str] = []
    for part in gen_content.parts:
        # Text parts
        txt = getattr(part, "text", None)
        if isinstance(txt, str) and txt:
            texts.append(txt)
            # Parse markdown images: ![alt](url)
            for m in re.findall(r"!\[[^\]]*\]\((https?[^\s)]+)\)", txt):
                images.append(m)
        # Possible rendered HTML in known fields
        for maybe_html_attr in ("rendered_content", "renderedContent", "html"):
            h = getattr(part, maybe_html_attr, None)
            if isinstance(h, str) and h:
                htmls.append(h)
        # Inline data that could be HTML
        inline = getattr(part, "inline_data", None)
        if inline is not None:
            mt = getattr(inline, "mime_type", None)
            data = getattr(inline, "data", None)
            if mt in ("text/html", "application/html") and data:
                try:
                    if isinstance(data, (bytes, bytearray)):
                        htmls.append(data.decode("utf-8", errors="ignore"))
                    elif isinstance(data, str):
                        # Some SDKs may base64 encode to str
                        htmls.append(base64.b64decode(data).decode("utf-8", errors="ignore"))
                except Exception:
                    # Ignore decoding errors; fallback on text only
                    pass
    return ("\n".join(texts).strip(), "\n".join(htmls).strip(), images)


def _is_direct_image_url(u: str) -> bool:
    u = u.lower()
    return any(u.endswith(ext) for ext in (".jpg", ".jpeg", ".png", ".webp", ".gif"))


@app.get("/img")
def proxy_image(u: str):
    # Very small proxy to avoid hotlink restrictions. Not production-hardened.
    if not (u.startswith("http://") or u.startswith("https://")):
        raise HTTPException(status_code=400, detail="Invalid URL")
    try:
        resp = requests.get(u, timeout=10, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
        })
        ct = resp.headers.get("Content-Type", "application/octet-stream")
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail="Upstream error")
        # Only serve images
        if not ct.startswith("image/") and not _is_direct_image_url(u):
            raise HTTPException(status_code=415, detail="Not an image")
        return Response(content=resp.content, media_type=ct)
    except requests.Timeout:
        raise HTTPException(status_code=504, detail="Image fetch timeout")
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/")
async def index():
    # Simple UI that posts to /query and renders both text and HTML snippet; includes mode selector
    return (
        """
        <!doctype html>
        <html>
          <head>
            <meta charset="utf-8" />
            <title>ADK Search UI</title>
            <style>
              body { font-family: system-ui, sans-serif; margin: 1.5rem; }
              #html { border: 1px solid #ddd; padding: 1rem; margin-top: 1rem; }
              #text { white-space: pre-wrap; border: 1px solid #eee; padding: 1rem; margin-top: 1rem; }
              #gallery { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 12px; margin-top: 1rem; }
              #gallery img { width: 100%; height: 140px; object-fit: cover; border: 1px solid #ddd; border-radius: 6px; }
              .row { display: flex; gap: 8px; align-items: center; margin-bottom: 10px; }
              select, input { padding: 6px 8px; }
            </style>
          </head>
          <body>
            <h1>ADK Assistant</h1>
            <form id="f">
              <div class="row">
                <label for="mode">Mode:</label>
                <select id="mode" name="mode">
                  <option value="ecommerce">E-commerce</option>
                  <option value="brand-seo">Brand SEO</option>
                </select>
                <input id="q" name="q" placeholder="Ask a question..." style="width: 420px;" />
                <button>Send</button>
              </div>
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
              const mode = document.getElementById('mode');
              const status = document.getElementById('status');
              const html = document.getElementById('html');
              const gallery = document.getElementById('gallery');
              const text = document.getElementById('text');
              // Default selection from server-side env (best-effort via dataset or URL param not available; leave default order)
              f.addEventListener('submit', async (e) => {
                e.preventDefault();
                status.textContent = 'Working...';
                html.innerHTML = '';
                gallery.innerHTML = '';
                text.textContent = '';
                try {
                  const resp = await fetch('/query', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query: q.value, mode: mode.value })
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
                      img.loading = 'lazy'; img.decoding = 'async'; img.src = proxied; img.alt = 'image';
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


@app.post("/query")
async def query(body: QueryIn):
    if not AGENTS:
        raise HTTPException(status_code=500, detail="No agents loaded")

    mode = (body.mode or DEFAULT_MODE).lower()
    agent = AGENTS.get(mode)
    if agent is None:
        raise HTTPException(status_code=400, detail=f"Unknown mode: {mode}")

    # Hints for brand-SEO runtime dependencies
    if mode == "brand-seo":
        if not (os.getenv("GOOGLE_CSE_ID") and os.getenv("GOOGLE_SEARCH_API_KEY")):
            logger.warning("[brand-seo] Missing Google CSE env; keyword_finding/search tools may be limited.")
        # Selenium defaults headless true in tools; just log guidance
        logger.info("[brand-seo] Ensure Chrome/Chromium is installed or HEADLESS=1 for server environments.")

    runner = InMemoryRunner(agent=agent, app_name=f"adk-practice-web:{mode}")

    user_msg = types.Content(role="user", parts=[types.Part(text=body.query)])

    last_model_event_content: Optional[types.Content] = None
    try:
        for event in runner.run(
            user_id=body.user_id or "user-1",
            session_id=body.session_id or "session-001",
            new_message=user_msg,
        ):
            if getattr(event, "author", None) and event.author != "user":
                # Keep the last non-user content as candidate for display
                last_model_event_content = getattr(event, "content", None)
    except Exception as e:
        logger.exception("Agent run failed")
        raise HTTPException(status_code=500, detail=str(e))

    text, html, images = _extract_text_and_html(last_model_event_content)

    return {"text": text, "html": html, "images": images}
