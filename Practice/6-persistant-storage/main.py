from google.adk.agents.llm_agent import Agent
from google.adk.sessions import DatabaseSessionService
from memory_agent.agent import memory_agent
from google.adk.runners import Runner
from utils import call_agent_async
from dotenv import load_dotenv
import uuid
load_dotenv()

db_url = "sqlite:///memory_agent.db"
session_service = DatabaseSessionService(db_url=db_url)

initial_state = {
    "user_name": "Alice",
    "reminders": [],
}

async def main_asyncio():
    APP_NAME = "memory_agent"
    USER_ID = "user123"
    
    existing_sessions = await session_service.list_session(
        app_name = APP_NAME,
        user_id = USER_ID,
    )
    
    if existing_sessions and len(existing_sessions) > 0:
       SESSION_ID = existing_sessions[0].session_id
    else:
        SESSION_ID = str(uuid.uuid4())
        stateful_session = await session_service.create_session(
            session_id=SESSION_ID,
            user_id=USER_ID,
            app_name=APP_NAME,
        )
        stateful_session.state.update(initial_state)
        print("Seeded session state:")
        print(stateful_session.state)
        print(f"Stateful session created with ID: {SESSION_ID}")
        