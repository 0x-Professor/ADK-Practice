# 5-session-and-state

Purpose
- Demonstrates session state usage with InMemorySessionService and async Runner APIs.

Files
- basic-stateful-session.py: seeds session state and asks a question; prints final response and state snapshot.
- question_answering/: contains question_answering_agent used in the example.

Usage
- python basic-stateful-session.py

Notes
- The agent reads a provided session_state (user_name, user_preferences) and personalizes answers.
