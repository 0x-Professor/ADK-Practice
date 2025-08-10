from __future__ import annotations

from typing import Optional
from google.genai import types

async def call_agent_async(runner, user_id: str, session_id: str, user_input: str) -> Optional[str]:
    """Send a user message to the agent runner (async) and print the final response.

    Returns the final response text (if any) for convenience.
    """
    final_text: Optional[str] = None
    # Build a proper Content message for ADK Runner
    msg = types.Content(role="user", parts=[types.Part(text=user_input)])

    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=msg,
    ):
        if getattr(event, "is_final_response", lambda: False)():
            content = getattr(event, "content", None)
            if content and getattr(content, "parts", None):
                for p in content.parts:
                    if getattr(p, "text", None):
                        final_text = (final_text + "\n" if final_text else "") + p.text
    if final_text:
        print(f"Memory Agent: {final_text}")
    return final_text