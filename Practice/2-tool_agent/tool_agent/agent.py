from google.adk.agents.llm_agent import Agent
from google.adk.tools import google_search
from dotenv import load_dotenv
import json
import re
from typing import Any, Dict, List, Optional
import time
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
import requests
import os

# New imports for Wikipedia tooling
from urllib.parse import quote as urlquote


load_dotenv()

#helper funcitons
def _ok(data: Dict[str, Any]) -> Dict[str, Any]:
    data.setdefault("ok", True)
    return data


def _err(msg: str, **extra) -> Dict[str, Any]:
    d = {"ok": False, "error": msg}
    d.update(extra)
    return d


def _domain(u: str) -> str:
    try:
        return urlparse(u).netloc.lower()
    except Exception:
        return ""


# --- Date / Misc ---

def get_current_date() -> dict:
    """ Returns the current date in YYYY-MM-DD format. Used for logging or metadata purposes. """
    from datetime import datetime
    return {"current_date": datetime.now().strftime("%Y-%m-%d")}


# --- Finance / Marketing (existing) ---

def currency_convert(amount: float, from_currency: str, to_currency: str) -> Dict[str, Any]:
    """Convert currency using exchangerate.host (no key required)."""
    try:
        amt = float(amount)
    except Exception:
        return _err("invalid_amount")

    from_c = (from_currency or "").upper().strip()
    to_c = (to_currency or "").upper().strip()
    if not from_c or not to_c:
        return _err("invalid_currency")

    url = f"https://api.exchangerate.host/convert?{urlencode({'from': from_c, 'to': to_c, 'amount': amt})}"
    try:
        r = requests.get(url, timeout=8)
        j = r.json()
        if not j.get("success", True):
            return _err("conversion_failed", raw=j)
        return _ok({"amount": amt, "from": from_c, "to": to_c, "rate": j.get("info", {}).get("rate"), "result": j.get("result")})
    except requests.Timeout:
        return _err("timeout")
    except Exception as e:
        return _err(str(e))


def mortgage_calculator(principal: float, annual_rate_pct: float, years: int) -> Dict[str, Any]:
    """Calculate monthly payment and totals for a fixed-rate mortgage."""
    try:
        P = float(principal)
        r_annual = float(annual_rate_pct)
        n_years = int(years)
    except Exception:
        return _err("invalid_inputs")

    n = n_years * 12
    if n <= 0 or P < 0:
        return _err("invalid_term_or_principal")
    r = (r_annual / 100.0) / 12.0
    if r == 0:
        m = P / n
    else:
        m = P * r * (1 + r) ** n / ((1 + r) ** n - 1)
    total = m * n
    interest = total - P
    return _ok({"monthly_payment": round(m, 2), "total_payment": round(total, 2), "total_interest": round(interest, 2)})


def build_utm(url: str, source: str, medium: str, campaign: str, term: Optional[str] = None, content: Optional[str] = None) -> Dict[str, Any]:
    """Append UTM parameters to a URL for campaign tracking."""
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return _err("invalid_url")
        q = dict(parse_qsl(parsed.query, keep_blank_values=True))
        q.update({
            "utm_source": source,
            "utm_medium": medium,
            "utm_campaign": campaign,
        })
        if term:
            q["utm_term"] = term
        if content:
            q["utm_content"] = content
        new = parsed._replace(query=urlencode(q))
        return _ok({"url": urlunparse(new)})
    except Exception as e:
        return _err(str(e))


# --- Wikipedia Professional Tools ---

_WIKI_DEFAULT_UA = "ADK-WikiTools/1.0 (+https://example.local)"


def _wiki_headers() -> Dict[str, str]:
    # Respect Wikimedia API policy
    h = {
        "User-Agent": _WIKI_DEFAULT_UA,
        "Accept": "application/json, text/html;q=0.8",
    }
    # Optional OAuth2 bearer, if provided via env; do not log or expose
    token = os.getenv("WIKI_ACCESS_TOKEN")
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def _wiki_get(url: str, params: Optional[Dict[str, Any]] = None, max_retries: int = 2, timeout: float = 10.0) -> requests.Response:
    last_exc: Optional[Exception] = None
    for i in range(max_retries + 1):
        try:
            resp = requests.get(url, params=params or {}, headers=_wiki_headers(), timeout=timeout)
            # Handle 429 with simple backoff
            if resp.status_code == 429 and i < max_retries:
                time.sleep(0.6 * (i + 1))
                continue
            return resp
        except Exception as e:
            last_exc = e
            time.sleep(0.2 * (i + 1))
    if last_exc:
        raise last_exc
    raise RuntimeError("wiki_get_failed")


def wiki_search(query: str, lang: str = "en", limit: int = 5) -> Dict[str, Any]:
    """Search Wikipedia pages by title/keywords via REST. Returns compact list of pages with ids, titles, descriptions, and URLs."""
    if not query or not isinstance(query, str):
        return _err("invalid_query")
    try:
        url = f"https://{lang}.wikipedia.org/w/rest.php/v1/search/page"
        r = _wiki_get(url, params={"q": query, "limit": int(limit)})
        if r.status_code != 200:
            return _err("http_error", status=r.status_code)
        j = r.json()
        pages = []
        for it in (j.get("pages") or [])[: int(limit)]:
            title = it.get("title")
            id_ = it.get("id")
            desc = (it.get("description") or it.get("excerpt") or "").strip()
            pages.append({
                "id": id_,
                "title": title,
                "description": desc,
                "url": f"https://{lang}.wikipedia.org/wiki/{urlquote(title or '')}",
                "lang": lang,
            })
        return _ok({"query": query, "results": pages})
    except requests.Timeout:
        return _err("timeout")
    except Exception as e:
        return _err(str(e))


def _abs_img(src: str, lang: str) -> str:
    if not src:
        return src
    if src.startswith("//"):
        return "https:" + src
    if src.startswith("/"):
        return f"https://{lang}.wikipedia.org" + src
    return src


def wiki_get_page(title: str, lang: str = "en", include_html: bool = False, max_images: int = 12, max_refs: int = 20) -> Dict[str, Any]:
    """Fetch a Wikipedia page summary + parse HTML to extract infobox, sections, lead, images, and references."""
    if not title:
        return _err("invalid_title")
    try:
        # Summary/basic metadata
        sum_url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{urlquote(title)}"
        rs = _wiki_get(sum_url)
        if rs.status_code == 404:
            return _err("not_found")
        if rs.status_code != 200:
            return _err("http_error", status=rs.status_code)
        sj = rs.json()
        canonical = sj.get("content_urls", {}).get("desktop", {}).get("page") or f"https://{lang}.wikipedia.org/wiki/{urlquote(title)}"
        page_title = sj.get("title") or title
        page_id = sj.get("pageid") or sj.get("id")
        description = sj.get("description")
        extract = sj.get("extract")
        thumbnail = (sj.get("thumbnail") or {}).get("source")

        # Fetch HTML for parsing (sections/infobox/images/refs)
        html_url = f"https://{lang}.wikipedia.org/api/rest_v1/page/html/{urlquote(page_title)}"
        rh = _wiki_get(html_url)
        if rh.status_code != 200:
            return _err("http_error", status=rh.status_code)
        html = rh.text

        # Lazy import BeautifulSoup
        try:
            from bs4 import BeautifulSoup  # type: ignore
        except Exception:
            return _err("missing_dependency", package="beautifulsoup4")

        # Prefer lxml, fallback to built-in parser
        try:
            soup = BeautifulSoup(html, "lxml")
        except Exception:
            try:
                soup = BeautifulSoup(html, "html.parser")
            except Exception as e:
                return _err(str(e))

        # Lead paragraphs (before first h2)
        lead_paras: List[str] = []
        content_div = soup.find("div", attrs={"id": "content"}) or soup
        for p in content_div.find_all("p", recursive=True):
            # Stop at the first section heading
            prev_h2 = p.find_previous(lambda t: t.name in ("h2", "section"))
            if prev_h2 is None:
                text = p.get_text(strip=True)
                if text:
                    lead_paras.append(text)
            else:
                break
        if not lead_paras:
            # Fallback: first two paragraphs anywhere
            lead_paras = [p.get_text(strip=True) for p in soup.find_all("p")[:2] if p.get_text(strip=True)]

        # Infobox key-value extraction
        infobox: Dict[str, str] = {}
        inf = soup.find("table", class_=lambda c: c and "infobox" in c)
        if inf:
            for row in inf.find_all("tr"):
                th = row.find("th")
                td = row.find("td")
                if th and td:
                    k = th.get_text(" ", strip=True)
                    v = td.get_text(" ", strip=True)
                    if k and v:
                        infobox[k] = v

        # Sections (h2/h3)
        sections: List[Dict[str, Any]] = []
        for h in soup.find_all(["h2", "h3"]):
            title_txt = h.get_text(" ", strip=True)
            if not title_txt:
                continue
            anchor = h.get("id") or (h.find("span", attrs={"id": True}) or {}).get("id")
            sections.append({"tag": h.name, "title": title_txt, "anchor": anchor})

        # Images (src)
        imgs: List[str] = []
        for img in soup.find_all("img"):
            src = img.get("src")
            if src:
                imgs.append(_abs_img(src, lang))
            if len(imgs) >= int(max_images):
                break

        # References (simple)
        refs: List[str] = []
        for li in soup.select("ol.references li cite, section#References cite, .references cite"):
            t = li.get_text(" ", strip=True)
            if t:
                refs.append(t)
            if len(refs) >= int(max_refs):
                break

        data = {
            "ok": True,
            "title": page_title,
            "page_id": page_id,
            "lang": lang,
            "url": canonical,
            "description": description,
            "extract": extract,
            "thumbnail": thumbnail,
            "lead_paragraphs": lead_paras,
            "infobox": infobox,
            "sections": sections,
            "images": imgs,
            "references": refs,
        }
        if include_html:
            data["html"] = html
        return data
    except requests.Timeout:
        return _err("timeout")
    except Exception as e:
        return _err(str(e))


def wiki_get_html(title: str, lang: str = "en") -> Dict[str, Any]:
    """Fetch sanitized HTML for a Wikipedia page via REST. Useful when the LLM needs raw HTML."""
    if not title:
        return _err("invalid_title")
    try:
        url = f"https://{lang}.wikipedia.org/api/rest_v1/page/html/{urlquote(title)}"
        r = _wiki_get(url)
        if r.status_code != 200:
            return _err("http_error", status=r.status_code)
        return _ok({"title": title, "lang": lang, "html": r.text, "url": f"https://{lang}.wikipedia.org/wiki/{urlquote(title)}"})
    except requests.Timeout:
        return _err("timeout")
    except Exception as e:
        return _err(str(e))


root_agent = Agent(
    model='gemini-2.0-flash',
    name='root_agent',
    description='A helpful assistant for user questions.',
    instruction=(
        'Answer user questions to the best of your knowledge.\n'
        'When the user asks about encyclopedic topics, ALWAYS use wiki_search first, then wiki_get_page for details (summary, infobox, sections, images).\n'
        'Use currency_convert for FX math and mortgage_calculator for payments. Build tracking links with build_utm.\n'
        'Prefer concise answers and include key fields from tool outputs when they validate facts.'
    ),
    tools=[
        # Wikipedia professional tools
        wiki_search,
        wiki_get_page,
        wiki_get_html,
        # General web search (optional)
        #google_search,
        # Finance/Marketing
        currency_convert,
        mortgage_calculator,
        build_utm,
        # Misc
        get_current_date,
    ],
    # you can use the custom tool only or the built in tools like google_search at once but not the both because they give error
)
