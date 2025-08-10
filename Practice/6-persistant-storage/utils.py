from __future__ import annotations

from typing import Optional, Any
from google.genai import types


def _fmt_state(state: dict | None) -> str:
    if not state:
        return "{}"
    try:
        import json
        return json.dumps(state, indent=2, ensure_ascii=False)
    except Exception:
        return str(state)


def _safe_get_session(session_service, app_name: str, user_id: str, session_id: str):
    try:
        # DatabaseSessionService has async get_session; InMemory may have sync. Try both.
        get_sess = getattr(session_service, "get_session", None)
        if get_sess is None:
            return None
        if callable(get_sess):
            # Could be coroutine or regular function
            import inspect
            if inspect.iscoroutinefunction(get_sess):
                # Call synchronously is not possible; caller should pass async service only here
                return None
            return get_sess(app_name=app_name, user_id=user_id, session_id=session_id)
    except Exception:
        return None


async def _safe_get_session_async(session_service, app_name: str, user_id: str, session_id: str):
    try:
        get_sess = getattr(session_service, "get_session", None)
        if get_sess is None:
            return None
        import inspect
        if inspect.iscoroutinefunction(get_sess):
            return await get_sess(app_name=app_name, user_id=user_id, session_id=session_id)
        # Fallback to sync call in async context
        return get_sess(app_name=app_name, user_id=user_id, session_id=session_id)
    except Exception:
        return None


async def call_agent_async(
    runner,
    user_id: str,
    session_id: str,
    user_input: str,
    *,
    session_service: Any,
    app_name: str,
) -> Optional[str]:
    """Send a user message to the agent runner (async) with rich logging.

    - Prints professional event logs
    - Shows session.state before and after each event
    - Returns the final response text
    """
    final_text: Optional[str] = None

    # Build a proper Content message for ADK Runner
    msg = types.Content(role="user", parts=[types.Part(text=user_input)])

    # Initial snapshot (before turn)
    session_before = await _safe_get_session_async(session_service, app_name, user_id, session_id)
    print("\n====== User Turn Start ======")
    print(f"User: {user_input}")
    if session_before is not None:
        print("-- Session (before) --")
        print(f"id: {getattr(session_before, 'id', session_id)} | app: {app_name} | user: {user_id}")
        print("state:")
        print(_fmt_state(getattr(session_before, 'state', {})))

    # Stream events
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=msg,
    ):
        # Per-event before snapshot
        evt_before = await _safe_get_session_async(session_service, app_name, user_id, session_id)
        print("\n--- Event ---------------------------------")
        etype = getattr(event, "__class__", type("_", (), {})).__name__
        author = getattr(event, "author", None)
        print(f"type: {etype} | author: {author or '-'}")
        # Tool calls/results summaries
        tool_name = getattr(event, "tool_name", None) or getattr(event, "name", None)
        if tool_name:
            print(f"tool: {tool_name}")
        # Model content summary
        content = getattr(event, "content", None)
        if content and getattr(content, "parts", None):
            texts = []
            for p in content.parts:
                t = getattr(p, "text", None)
                if isinstance(t, str) and t.strip():
                    texts.append(t.strip())
            if texts:
                snippet = ("\n".join(texts))
                if len(snippet) > 400:
                    snippet = snippet[:400] + "\n..."
                print("content:")
                print(snippet)
        # Before snapshot for this event
        if evt_before is not None:
            print("state(before event):")
            print(_fmt_state(getattr(evt_before, 'state', {})))

        # Track final response text
        if getattr(event, "is_final_response", lambda: False)():
            if content and getattr(content, "parts", None):
                for p in content.parts:
                    t = getattr(p, "text", None)
                    if isinstance(t, str) and t:
                        final_text = (final_text + "\n" if final_text else "") + t

        # After snapshot for this event
        evt_after = await _safe_get_session_async(session_service, app_name, user_id, session_id)
        if evt_after is not None:
            print("state(after event):")
            print(_fmt_state(getattr(evt_after, 'state', {})))

    # Final output
    print("\n====== Assistant Response ======")
    if final_text:
        print(final_text)
    else:
        print("(no text response)")

    # End-of-turn snapshot
    session_after = await _safe_get_session_async(session_service, app_name, user_id, session_id)
    if session_after is not None:
        print("\n====== Session (end of turn) ======")
        print(f"id: {getattr(session_after, 'id', session_id)} | app: {app_name} | user: {user_id}")
        print("state:")
        print(_fmt_state(getattr(session_after, 'state', {})))

    return final_text