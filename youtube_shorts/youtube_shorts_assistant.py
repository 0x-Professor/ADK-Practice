# filepath: u:\adk-Practice\youtube_shorts\youtube_shorts_assistant.py
from __future__ import annotations

from pathlib import Path

BASE_DIR = Path(__file__).parent


def load_instruction_from_file(filename: str) -> str:
    """Load an instruction prompt from a text file next to this module.

    If the file is missing, return a short, safe default so the app remains usable.
    """
    path = (BASE_DIR / filename).resolve()
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    # Fallback instructions keep the app functional even if files are not present
    if "scriptwriter" in filename.lower():
        return (
            "You are a concise, engaging YouTube Shorts scriptwriter. Create a 45–60s script "
            "on the given topic with a strong hook, 2–4 punchy facts, and a clear CTA at the end."
        )
    if "visualizer" in filename.lower():
        return (
            "Create a shot-by-shot visualization plan for the script: for each line, propose a short clip, "
            "B-roll, on-screen text, and any sound effect or transition cue. Keep it brief and dynamic."
        )
    return "Write a concise instruction-compliant response for YouTube Shorts."