from __future__ import annotations

import os
import requests
from typing import Any, Dict, Optional
from google.adk.agents.llm_agent import Agent

# Prefer real LlmAgent; provide minimal fallback for static checks
try:
    from google.adk.agents import LlmAgent  # type: ignore
except Exception:  # pragma: no cover
    class LlmAgent:  # minimal stub
        def __init__(self, *args, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

DEFAULT_UNITS = os.getenv("WEATHER_UNITS", "metric")  # metric|imperial


def _geocode_city(city: str) -> Optional[Dict[str, float]]:
    """Geocode city name to lat/lon using Open-Meteo geocoding (no API key)."""
    try:
        r = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1, "language": "en", "format": "json"},
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()
        if not data or not data.get("results"):
            return None
        top = data["results"][0]
        return {"lat": float(top["latitude"]), "lon": float(top["longitude"]) }
    except Exception:
        return None


def get_weather(city: str, days: int = 1, units: str = DEFAULT_UNITS) -> Dict[str, Any]:
    """Fetch a simple daily forecast for a city using Open-Meteo.

    Args:
        city: City name to forecast.
        days: Number of days (1-7) of forecast.
        units: "metric" or "imperial".

    Returns:
        Dict with city, unit labels, and daily summaries.
    """
    days = max(1, min(int(days or 1), 7))
    geo = _geocode_city(city)
    if not geo:
        return {"ok": False, "city": city, "error": "geocoding_failed"}

    temp_unit = "celsius" if units == "metric" else "fahrenheit"
    wind_unit = "kmh" if units == "metric" else "mph"

    try:
        r = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": geo["lat"],
                "longitude": geo["lon"],
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max",
                "forecast_days": days,
                "temperature_unit": temp_unit,
                "wind_speed_unit": wind_unit,
                "timezone": "auto",
            },
            timeout=12,
        )
        r.raise_for_status()
        data = r.json() or {}
        daily = (data.get("daily") or {})
        out = []
        times = daily.get("time") or []
        tmax = daily.get("temperature_2m_max") or []
        tmin = daily.get("temperature_2m_min") or []
        prec = daily.get("precipitation_sum") or []
        wind = daily.get("wind_speed_10m_max") or []
        for i in range(min(days, len(times))):
            out.append({
                "date": times[i],
                "t_max": tmax[i] if i < len(tmax) else None,
                "t_min": tmin[i] if i < len(tmin) else None,
                "precipitation": prec[i] if i < len(prec) else None,
                "wind_max": wind[i] if i < len(wind) else None,
            })
        return {
            "ok": True,
            "city": city,
            "units": units,
            "days": len(out),
            "forecast": out,
        }
    except Exception as e:
        return {"ok": False, "city": city, "error": str(e)}


MODEL = os.getenv("GENAI_MODEL", "gemini-2.0-flash")

root_agent = Agent(
    model='<FILL_IN_MODEL>',
    name='root_agent',
    description='A helpful assistant for user questions.',
    instruction='Answer user questions to the best of your knowledge',
)

weather_forecaster_agent = LlmAgent(
    model=MODEL,
    name="weather_forecaster_agent",
    description="Provides quick weather forecasts using Open-Meteo tool.",
    instruction=(
        "You are a weather assistant. When asked for weather, call the get_weather tool"
        " with the provided city and desired days (default 1). Then summarize concisely"
        " with highs/lows and precipitation. Keep it under 80 words."
    ),
    tools=[get_weather],
    output_key="forecast",
)
