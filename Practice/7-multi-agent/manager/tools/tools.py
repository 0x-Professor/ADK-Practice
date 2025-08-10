from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Optional

try:
    from zoneinfo import ZoneInfo  # Python 3.9+
except Exception:  # pragma: no cover
    ZoneInfo = None  # type: ignore


def get_current_time(fmt: str = "%Y-%m-%d %H:%M:%S %Z", tz: Optional[str] = None) -> str:
    """Return the current time formatted with optional timezone.

    Args:
        fmt: strftime-compatible format. Default includes timezone name.
        tz: IANA timezone string, e.g., "UTC", "America/New_York". If None or
            unavailable, falls back to local time or UTC when ZoneInfo is missing.

    Returns:
        A formatted datetime string.
    """
    # Resolve timezone
    dt: datetime
    if tz and ZoneInfo is not None:
        try:
            dt = datetime.now(ZoneInfo(tz))
        except Exception:
            # Fallback to UTC if invalid tz provided
            dt = datetime.now(timezone.utc)
    else:
        # Prefer local time; if ZoneInfo unavailable, naive local time
        try:
            dt = datetime.now().astimezone()
        except Exception:
            dt = datetime.now(timezone.utc)

    try:
        return dt.strftime(fmt)
    except Exception:
        # Fallback format if the provided one is invalid
        return dt.strftime("%Y-%m-%d %H:%M:%S %Z")