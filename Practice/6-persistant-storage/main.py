import warnings
warnings.filterwarnings(
    "ignore",
    message=r"Field name .* shadows an attribute in parent",
    category=UserWarning,
    module="pydantic",
)

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
    
    # List existing sessions (plural API) and pick the first one if any
    resp = await session_service.list_sessions(
        app_name=APP_NAME,
        user_id=USER_ID,
    )
    existing = resp.sessions if resp else []
    
    if existing:
        SESSION_ID = existing[0].id
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
    
    runner = Runner(
        agent=memory_agent,
        session_service=session_service,
        app_name=APP_NAME,
    )
    
    print(f"Running agent with session ID: {SESSION_ID}")
    print("You can ask me to remember things or retrieve your reminders.")
    
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Exiting the session.")
            break
        
        # Stream run with professional per-event state snapshots
        await call_agent_async(
            runner,
            USER_ID,
            SESSION_ID,
            user_input,
            session_service=session_service,
            app_name=APP_NAME,
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main_asyncio())