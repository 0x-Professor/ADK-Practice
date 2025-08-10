from google.adk.agents.llm_agent import Agent
from google.adk.tools.agent_tool import AgentTool
from .sub_agent.funny_nerd.agent import funny_nerd_agent
from .sub_agent.news_analyst.agent import news_analyst_agent
from .sub_agent.weather_forecaster.agent import weather_forecaster_agent
from .sub_agent.joke_teller.agent import joke_teller_agent
from tools.tools import get_current_time


root_agent = Agent(
    model='gemini-2.0-flash',
    name='manager',
    description='Manager Agent',
    instruction="""    You are a manager agent that can assist users with various tasks.
    You can delegate tasks to sub-agents based on the user's request.
    You can also use tools to perform tasks that do not require sub-agents.
    If you don't know how to answer a question, you can delegate it to a sub-agent.
    If you don't know how to use a tool, you can ask the user for more information.""",
    sub_agents={
        funny_nerd_agent,
        news_analyst_agent,
        weather_forecaster_agent,
        joke_teller_agent,
    },
    tools=[
        AgentTool(
            name='get_current_time',
            description='Get the current time in a specific format',
            tool=get_current_time,
        ),
    ],
    
)
