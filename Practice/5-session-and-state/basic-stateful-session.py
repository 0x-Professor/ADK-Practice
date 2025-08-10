from google.adk.agents.llm_agent import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService, Session
from google.genai import types
from question_answering import question_answering_agent
from dotenv import load_dotenv
import uuid

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
stateful_session = session_service_stateful.create_session(
    session_id=SESSION_ID,
    user_id=USER_ID,
    app_name=APP_NAME,
    initial_state=initial_state
)

print(f"Stateful session created with ID: {SESSION_ID}")
runner = Runner(
    agent=question_answering_agent,
    session_service=session_service_stateful,
    session=stateful_session,
    model='gemini-2.0-flash',
    name='stateful_session_agent',
    description='An agent that maintains state across sessions and can answer questions based on user preferences.',
    instruction="""
    You are a personal assistant that can answer questions based on the user's preferences and past interactions.
    Use the session state to provide personalized responses.
    If you need more information, ask the user for clarification.
    """,
)
