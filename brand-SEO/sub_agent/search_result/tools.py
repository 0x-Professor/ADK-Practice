import os
import base64
import time
from typing import Any, Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# Reusable webdriver (single session per process)
_DRIVER: Optional[webdriver.Chrome] = None


def _artifact_dir() -> str:
    d = os.path.join(os.path.dirname(__file__), "artifacts")
    os.makedirs(d, exist_ok=True)
    return d


def _get_driver() -> webdriver.Chrome:
    global _DRIVER
    if _DRIVER is not None:
        return _DRIVER
    headless = os.getenv("HEADLESS", "1") not in ("0", "false", "False")
    opts = ChromeOptions()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1366,900")
    # Be a bit stealthy
    opts.add_argument("--disable-blink-features=AutomationControlled")
    _DRIVER = webdriver.Chrome(ChromeDriverManager().install(), options=opts)
    _DRIVER.set_page_load_timeout(30)
    return _DRIVER


# -------------------- TOOL FUNCTIONS --------------------

def go_to_url(url: str, wait_selector: Optional[str] = None, timeout: float = 15) -> dict[str, Any]:
    """Navigate to URL and optionally wait for a CSS selector to appear."""
    drv = _get_driver()
    drv.get(url)
    if wait_selector:
        try:
            WebDriverWait(drv, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, wait_selector))
            )
        except TimeoutException:
            return {"ok": False, "url": url, "error": f"Timeout waiting for selector: {wait_selector}"}
    return {"ok": True, "url": drv.current_url, "title": drv.title}


def take_screenshot(name: Optional[str] = None) -> dict[str, Any]:
    """Capture a PNG screenshot and return both path and base64."""
    drv = _get_driver()
    if not name:
        name = f"screenshot_{int(time.time()*1000)}.png"
    if not name.lower().endswith(".png"):
        name += ".png"
    path = os.path.join(_artifact_dir(), name)
    drv.save_screenshot(path)
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return {"ok": True, "path": path, "base64": b64}


def _find_elements_by_text(text: str, tag: Optional[str] = None, exact: bool = False):
    drv = _get_driver()
    # XPath matches text content; normalize-space removes excess whitespace
    if exact:
        xp_text = f"normalize-space(text())='{text.strip()}') or normalize-space(.)='{text.strip()}'"
        xpath = f".//*[{xp_text}]"
    else:
        # contains on either direct text node or any descendant text
        xpath = f".//*[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text.strip().lower()}')]"
    if tag:
        xpath = xpath.replace(".//*", f".//{tag}")
    return drv.find_elements(By.XPATH, xpath)


def find_element_with_text(text: str, tag: Optional[str] = None, exact: bool = False, timeout: float = 5) -> dict[str, Any]:
    """Find the first element containing given text and return summary info."""
    drv = _get_driver()
    end = time.time() + timeout
    elems = []
    while time.time() < end and not elems:
        elems = _find_elements_by_text(text, tag=tag, exact=exact)
        if elems:
            break
        time.sleep(0.2)
    if not elems:
        return {"ok": False, "error": "not_found", "text": text}
    el = elems[0]
    try:
        outer = el.get_attribute("outerHTML")
    except Exception:
        outer = ""
    return {
        "ok": True,
        "text": text,
        "tag": el.tag_name,
        "location": el.location,
        "size": el.size,
        "outer_html": outer[:3000],  # truncate
    }


def click_element_with_text(text: str, tag: Optional[str] = None, exact: bool = False, timeout: float = 8) -> dict[str, Any]:
    """Click the first element matching text. Scroll into view before clicking."""
    drv = _get_driver()
    end = time.time() + timeout
    last_err: Optional[str] = None
    while time.time() < end:
        try:
            elems = _find_elements_by_text(text, tag=tag, exact=exact)
            if not elems:
                time.sleep(0.2)
                continue
            el = elems[0]
            drv.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
            el.click()
            return {"ok": True, "clicked_text": text}
        except Exception as e:
            last_err = str(e)
            time.sleep(0.25)
    return {"ok": False, "error": last_err or "click_failed", "text": text}


def enter_text_into_element(selector: str, text: str, clear: bool = True, submit: bool = False, timeout: float = 8) -> dict[str, Any]:
    """Type text into element located by CSS selector. Optionally submit (Enter)."""
    from selenium.webdriver.common.keys import Keys

    drv = _get_driver()
    try:
        el = WebDriverWait(drv, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        )
    except TimeoutException:
        return {"ok": False, "error": f"Timeout locating selector: {selector}"}
    try:
        drv.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
        if clear:
            el.clear()
        el.send_keys(text)
        if submit:
            el.send_keys(Keys.ENTER)
        return {"ok": True, "selector": selector, "typed": len(text)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def scroll_down_screen(times: int = 2, pause_sec: float = 0.6) -> dict[str, Any]:
    """Scroll down the page a few times to load more content."""
    drv = _get_driver()
    last_y = 0
    for i in range(max(1, times)):
        drv.execute_script("window.scrollBy(0, Math.max(400, window.innerHeight * 0.8));")
        time.sleep(pause_sec)
        y = drv.execute_script("return window.scrollY || document.documentElement.scrollTop || 0;")
        if y == last_y:
            break
        last_y = y
    return {"ok": True, "scrolled_times": i + 1, "final_y": last_y}


def load_artifacts_tool(include_html: bool = True) -> dict[str, Any]:
    """Return current page artifacts such as URL, title, HTML snapshot (truncated)."""
    drv = _get_driver()
    html = drv.page_source if include_html else ""
    if html and len(html) > 500_000:
        html = html[:500_000] + "\n<!-- truncated -->"
    return {
        "ok": True,
        "url": drv.current_url,
        "title": drv.title,
        "html": html,
    }


def _extract_domain(url: str) -> str:
    try:
        from urllib.parse import urlparse
        netloc = urlparse(url).netloc
        return netloc.lower()
    except Exception:
        return ""


def analyze_webpage_and_determine_actions(max_results: int = 15) -> dict[str, Any]:
    """Parse a Google SERP to extract result items (rank, title, url, snippet).
    This is a lightweight DOM parser using common selectors that work for most locales.
    """
    drv = _get_driver()
    items: list[dict[str, Any]] = []

    # Try multiple selector strategies as Google HTML varies.
    candidates = drv.find_elements(By.CSS_SELECTOR, "div#search div.g")
    if not candidates:
        candidates = drv.find_elements(By.CSS_SELECTOR, "div#search div[data-sokoban-container]")
    if not candidates:
        candidates = drv.find_elements(By.CSS_SELECTOR, "main div.g")

    rank = 1
    seen = set()
    for c in candidates:
        if len(items) >= max_results:
            break
        try:
            link = c.find_element(By.CSS_SELECTOR, "a")
            title_el = None
            # prefer h3
            try:
                title_el = c.find_element(By.CSS_SELECTOR, "h3")
            except NoSuchElementException:
                try:
                    title_el = link
                except Exception:
                    title_el = None
            url = link.get_attribute("href") or ""
            if not url or url.startswith("/search?"):
                continue
            domain = _extract_domain(url)
            if (domain, url) in seen:
                continue
            seen.add((domain, url))
            snippet = ""
            try:
                snippet = c.find_element(By.CSS_SELECTOR, "div.VwiC3b, div[data-content-feature='1']").text
            except NoSuchElementException:
                try:
                    snippet = c.text[:300]
                except Exception:
                    snippet = ""
            title = (title_el.text if title_el else "").strip()
            if not title:
                # fallback from anchor title attribute
                title = (link.get_attribute("title") or "").strip()
            if not title:
                title = domain
            # Simple content type heuristic
            ct = "page"
            lower = url.lower()
            if any(p in lower for p in ("/category/", "/c/", "/collections/", "/departments/")):
                ct = "category"
            elif any(p in lower for p in ("/product/", "/p/", "/dp/", "/sku/")):
                ct = "product"
            elif any(p in lower for p in ("/blog/", "/article/", "/insights/", "/news/")):
                ct = "blog"
            elif any(p in lower for p in ("/forum/", "/community/", "/thread/")):
                ct = "forum"
            elif any(p in lower for p in ("youtube.com/", "/video/")):
                ct = "video"
            items.append({
                "rank": rank,
                "title": title,
                "url": url,
                "domain": domain,
                "snippet": snippet,
                "content_type": ct,
            })
            rank += 1
        except Exception:
            continue

    return {"ok": True, "results": items}
