# 6-persistant-storage

Purpose
- Demonstrates persistent sessions using DatabaseSessionService (SQLite) and a stateful reminder agent with ToolContext.

Files
- main.py: interactive console app that creates/loads a stateful session and streams events.
- utils.py: pretty event/state logging helpers for async runs.
- memory_agent/: reminder tools and agent definition.

Usage
- python main.py
- The first run creates memory_agent.db and seeds initial state; subsequent runs reuse the session.

Notes
- Tools add/view/update/delete reminders via ToolContext-backed session state.
- Change db_url in main.py to use a different SQLite path or RDBMS.
