from google.adk.agents.llm_agent import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService, Session
from google.genai import types
from question_answering import question_answering_agent
from dotenv import load_dotenv
import uuid
import asyncio

load_dotenv()

session_service_stateful = InMemorySessionService()
initial_state = {
    "user_name": "John Doe",
    "user_preferences": """
    likes to play basketball,
    enjoys reading science fiction,
    prefers coffee over tea,
    and loves to travel.
    and loves to break the code logic 
    build secure logics
    """
    
}

APP_NAME = "personal-Bot"
USER_ID = "user123"
SESSION_ID = str(uuid.uuid4())

async def main():
    # Create session (async API) and seed state
    stateful_session = await session_service_stateful.create_session(
        session_id=SESSION_ID,
        user_id=USER_ID,
        app_name=APP_NAME,
    )
    stateful_session.state.update(initial_state)

    print(f"Stateful session created with ID: {SESSION_ID}")
    runner = Runner(
        agent=question_answering_agent,
        session_service=session_service_stateful,
        app_name=APP_NAME,
    )

    new_message = types.Content(
        role="user",
        parts=[types.Part(text="What are my favorite activities?")],
    )

    for event in runner.run(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=new_message,
    ):
        if event.is_final_response():
            if event.content and event.content.parts:
                response_text = event.content.parts[0].text
                print(f"Response: {response_text}")

    print("Session state after interaction:")
    session = await session_service_stateful.get_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
    )
    print(session.state)
    for key, value in session.state.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    asyncio.run(main())



