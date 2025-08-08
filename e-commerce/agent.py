import os 
import logging
import asyncio
from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.adk.tool.agent_tool import AgentTool
from google.genai import types
from dotenv import load_dotenv
import requests
import json
load_dotenv()


logging.basicConfig(level=logging.INFO)
logging.getLogger("google.adk.runners").setLevel(logging.ERROR)
logging.getLogger("google.genai.types").setLevel(logging.ERROR)
APP_NAME = "e-commerce-agent"
USER_ID = "user-1"
SESSION_ID = "session-001"

#create a session
session_service = InMemorySessionService()
session = session_service.create_session(
    app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
)

async def test_agent(query, agent):
    """Sends a query to the agent and prints the final response."""
    print(f"Query: {query}")
    
    #create a runner
    runner = Runner(
        session_service=session_service,
        agent=agent,
        app_name=APP_NAME,
        
    )
    content  = types.Content(role = 'user', parts = [types.Part(text=query)])
    
    final_response_text = None
    
    #we iterate through events from run_async to find the final answer
    async for event in runner.run_async(user_id=USER_ID, session_id=SESSION_ID, new_message=content):
        if event.is_final_response():
            if event.content and event.content.parts:
                final_response_text = event.content.parts[0].text
            break
    print(f"Final Response: {final_response_text}")
    
    #Define the shop agent.
    
    instruction  = f"""
    your role is a shop search agent on an e-commerce site with millions of items.
    your responsibility is to search for items based on user queries and return the results.
    """
    
    shop_agent = Agent(
        name="shop_agent",
        model='gemini-2.0-flash',
        description=("Searches for items based on user queries and returns results."),
        instruction=instruction,
        )
    await test_agent(query, shop_agent)
    
    