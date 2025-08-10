from google.adk.agents.llm_agent import Agent

question_answering_agent = Agent(
    model='gemini-2.0-flash',
    name='question_answering_agent',
    description='An agent that can answer questions based on user preferences and past interactions.',
    instruction="""
    You are a personal assistant that can answer questions based on the user's preferences and past interactions.
    Use the session state to provide personalized responses.
    If you need more information, ask the user for clarification.   
    """,
)