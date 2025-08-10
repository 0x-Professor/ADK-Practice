from __future__ import annotations

from .agent import root_agent

# Optional helpers for session-aware execution
try:
    from google.adk.sessions import InMemorySessionService  # type: ignore
    from google.adk.runners import Runner  # type: ignore

    APP_NAME = "multi-agent-manager"

    def get_runner(user_id: str = "user-1", session_id: str = "session-001"):
        service = InMemorySessionService()
        session = service.create_session(app_name=APP_NAME, user_id=user_id, session_id=session_id)
        return Runner(root_agent, session_service=service), session
except Exception:  # pragma: no cover
    # Provide names so importing doesn't fail during static checks
    InMemorySessionService = None  # type: ignore
    Runner = None  # type: ignore

__all__ = ["root_agent"]
