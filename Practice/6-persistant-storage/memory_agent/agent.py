from google.adk.agents.llm_agent import Agent
from dotenv import load_dotenv
load_dotenv()

# Simple memory agent for reminders using session state
memory_agent = Agent(
    model='gemini-2.0-flash',
    name='memory_agent',
    description='A stateful assistant that can remember reminders and recall them later.',
    instruction='''
You are a helpful memory assistant.
- Session state is available to you as session_state (a JSON-like object).
- If the user asks you to remember something like "remind me to <task>" or "remember <note>", add it to session_state.reminders as a short string.
- If the user asks what you remember or to list reminders, read session_state.reminders and summarize them.
- If no reminders exist, say so and offer to add one.
- Keep replies concise.
''',
)
