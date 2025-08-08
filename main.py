from __future__ import annotations

import base64
import importlib.util
import logging
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from google.adk.runners import InMemoryRunner
from google.genai import types

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("adk_practice.web")

# --- Load the e-commerce agent dynamically from file (folder name has a hyphen) ---
PROJECT_ROOT = Path(__file__).parent
ECOM_AGENT_PATH = PROJECT_ROOT / "e-commerce" / "agent.py"

_root_agent = None
if ECOM_AGENT_PATH.exists():
    spec = importlib.util.spec_from_file_location("e_commerce_agent_module", ECOM_AGENT_PATH)
    if spec and spec.loader:
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[attr-defined]
        _root_agent = getattr(mod, "root_agent", None)

if _root_agent is None:
    logger.error("Failed to load e-commerce root_agent from %s", ECOM_AGENT_PATH)

# --- FastAPI app ---
app = FastAPI(title="ADK Practice Search UI", version="0.1.0")


class QueryIn(BaseModel):
    query: str
    user_id: Optional[str] = "user-1"
    session_id: Optional[str] = "session-001"


def _extract_text_and_html(gen_content: Optional[types.Content]) -> tuple[str, str]:
    """Extract concatenated text and any HTML-like rendered content.
    Tries multiple known locations for rendered HTML returned by Gemini 2.
    """
    if not gen_content or not getattr(gen_content, "parts", None):
        return "", ""

    texts: list[str] = []
    htmls: list[str] = []
    for part in gen_content.parts:
        # Text parts
        txt = getattr(part, "text", None)
        if isinstance(txt, str) and txt:
            texts.append(txt)
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
    return ("\n".join(texts).strip(), "\n".join(htmls).strip())


@app.get("/")
async def index():
    # Simple UI that posts to /query and renders both text and HTML snippet
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
            <h2>Text / Markdown</h2>
            <div id="text"></div>
            <script>
              const f = document.getElementById('f');
              const q = document.getElementById('q');
              const status = document.getElementById('status');
              const html = document.getElementById('html');
              const text = document.getElementById('text');
              f.addEventListener('submit', async (e) => {
                e.preventDefault();
                status.textContent = 'Searching...';
                html.innerHTML = '';
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
    if _root_agent is None:
        raise HTTPException(status_code=500, detail="Agent not loaded")

    runner = InMemoryRunner(agent=_root_agent, app_name="adk-practice-web")

    # Build user message
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

    text, html = _extract_text_and_html(last_model_event_content)

    return {"text": text, "html": html}
