from google.adk.agents.llm_agent import Agent
from google.adk.tools import google_search
from dotenv import load_dotenv
import json
import re
import time
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import requests


load_dotenv()
def get_current_date() -> dict:
    """ Returns the current date in YYYY-MM-DD format. Used for logging or metadata purposes. """
    from datetime import datetime
    return {"current_date": datetime.now().strftime("%Y-%m-%d")}


root_agent = Agent(
    model='gemini-2.0-flash',
    name='root_agent',
    description='A helpful assistant for user questions.',
    instruction='Answer user questions to the best of your knowledge. If you need to perform a search, use the get_current_date tool.',
    #tools=[google_search],
    tools = [get_current_date],
    
)
