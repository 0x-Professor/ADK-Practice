from google.adk.agents.llm_agent import Agent
from google.adk.tools import google_search
from dotenv import load_dotenv
import json
import re
from typing import Any, Dict, List, Optional
import time
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
import requests


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


def get_current_date() -> dict:
    """ Returns the current date in YYYY-MM-DD format. Used for logging or metadata purposes. """
    from datetime import datetime
    return {"current_date": datetime.now().strftime("%Y-%m-%d")}

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



root_agent = Agent(
    model='gemini-2.0-flash',
    name='root_agent',
    description='A helpful assistant for user questions.',
    instruction='Answer user questions to the best of your knowledge. If you need to perform a search, use the get_current_date tool.',
    #tools=[google_search],
    tools = [get_current_date],
    #add the above tool that you want to use
    
)
