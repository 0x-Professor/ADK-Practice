from __future__ import annotations

import asyncio
import sys
import uuid
from typing import Optional

# Optional dotenv
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass

# Try to import ADK; provide safe fallbacks for static analysis
try:
    from google.adk.runners import Runner  # type: ignore
    from google.adk.sessions import InMemorySessionService  # type: ignore
    from google.genai import types  # type: ignore
    _ADK_AVAILABLE = True
except Exception:  # pragma: no cover
    _ADK_AVAILABLE = False

    class _DummyRunner:  # minimal stub
        def __init__(self, *_, **__):
            pass
        def run(self, *_, **__):
            return []

    class _DummyService:  # minimal stub
        async def create_session(self, *_, **__):
            return object()

    class _Part:
        def __init__(self, text: str):
            self.text = text

    class _Content:
        def __init__(self, role: str, parts: list[_Part]):
            self.role = role
            self.parts = parts

    class _Types:
        Part = _Part
        Content = _Content

    Runner = _DummyRunner  # type: ignore
    InMemorySessionService = _DummyService  # type: ignore
    types = _Types()  # type: ignore

from manager import root_agent

APP_NAME = "manager"
USER_ID = "demo-user"


async def run_once(message: str, session_id: Optional[str] = None) -> str:
    if not _ADK_AVAILABLE:
        return "google-adk is not installed. Install dependencies and try again."

    service = InMemorySessionService()
    sid = session_id or str(uuid.uuid4())
    await service.create_session(session_id=sid, user_id=USER_ID, app_name=APP_NAME)

    runner = Runner(agent=root_agent, session_service=service, app_name=APP_NAME)

    new_message = types.Content(role="user", parts=[types.Part(text=message)])

    response_text = ""
    for event in runner.run(user_id=USER_ID, session_id=sid, new_message=new_message):
        if getattr(event, "is_final_response", lambda: False)() and getattr(event, "content", None) and event.content.parts:
            response_text = event.content.parts[0].text or ""
    return response_text


async def interactive() -> None:
    if not _ADK_AVAILABLE:
        print("google-adk is not installed. Install dependencies and try again.")
        return

    service = InMemorySessionService()
    session_id = str(uuid.uuid4())
    await service.create_session(session_id=session_id, user_id=USER_ID, app_name=APP_NAME)

    runner = Runner(agent=root_agent, session_service=service, app_name=APP_NAME)

    print(f"Session started: {session_id}. Type 'exit' to quit.")
    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye")
            return
        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit"}:
            print("Bye")
            return
        new_message = types.Content(role="user", parts=[types.Part(text=user_input)])
        response_text = None
        for event in runner.run(user_id=USER_ID, session_id=session_id, new_message=new_message):
            if getattr(event, "is_final_response", lambda: False)() and getattr(event, "content", None) and event.content.parts:
                response_text = event.content.parts[0].text
        print(f"Agent: {response_text or ''}")


def main() -> None:
    # If a message is provided on the command line, run once; else start interactive loop
    if len(sys.argv) > 1:
        message = " ".join(sys.argv[1:])
        text = asyncio.run(run_once(message))
        print(text)
    else:
        asyncio.run(interactive())


if __name__ == "__main__":
    main()
