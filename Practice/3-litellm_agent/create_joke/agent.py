from google.adk.agents.llm_agent import Agent
from google.adk.models.lite_llm import LiteLLM
from dotenv import load_dotenv
import os
load_dotenv()

model = LiteLLM(
    model_name='openrouter/deepseek-chat-v3-0324:free',
    api_key=os.getenv('OPENROUTER_API_KEY'),
    #timeout=30,
)

root_agent = Agent(
    model=model,
    name='dad_joke_agent',
    description='A helpful assistant for user questions.',
    instruction='Answer user questions to the best of your knowledge',
)
