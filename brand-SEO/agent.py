from __future__ import annotations

# Thin wrapper to expose root_agent from the packaged implementation.
# The root FastAPI app loads this file by path.
from pathlib import Path
import importlib.util
import logging

logger = logging.getLogger(__name__)
_IMPL = Path(__file__).parent.parent / "Agentic-Tools" / "brand-SEO" / "agent.py"

root_agent = None
try:
    spec = importlib.util.spec_from_file_location("brand_seo_impl", _IMPL)
    if spec and spec.loader:
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[attr-defined]
        root_agent = getattr(mod, "root_agent", None)
    else:
        logger.error("Failed to load spec for %s", _IMPL)
except Exception:  # pragma: no cover
    logger.exception("Failed to import brand-SEO implementation from %s", _IMPL)
