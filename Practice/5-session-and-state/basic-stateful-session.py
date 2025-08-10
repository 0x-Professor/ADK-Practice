from google.adk.agents.llm_agent import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from question_answering import question_answering_agent
from dotenv import load_dotenv

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