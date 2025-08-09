from google.adk.agents import LlmAgent
from dotenv import load_dotenv

load_dotenv()
root_agent = LlmAgent(
    name = "greeting_agent",
    model = "gemini-2.0-flash",
    description = "A simple agent that greets the user with their name.",
    instruction = "You are a friendly agent that greets the user warmly. Respond with a greeting message.",
        
)
    
    