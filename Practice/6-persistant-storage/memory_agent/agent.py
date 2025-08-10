from google.adk.agents.llm_agent import Agent
from dotenv import load_dotenv
load_dotenv()

def add_reminder(session_state, reminder: str):
    """Add a reminder to the session state."""
    if 'reminders' not in session_state:
        session_state['reminders'] = []
    session_state['reminders'].append(reminder)
    
def view_reminder(session_state):
    """View all reminders in the session state."""
    if 'reminders' in session_state and session_state['reminders']:
        return "\n".join(session_state['reminders'])
    else:
        return "You have no reminders."
def update_reminder(session_state, old_reminder: str, new_reminder: str):
    """Update an existing reminder in the session state."""
    if 'reminders' in session_state and old_reminder in session_state['reminders']:
        index = session_state['reminders'].index(old_reminder)
        session_state['reminders'][index] = new_reminder
        return f"Updated reminder: {new_reminder}"
    else:
        return "Reminder not found."
    
def delete_reminder(session_state, reminder: str):
    """Delete a reminder from the session state."""
    if 'reminders' in session_state and reminder in session_state['reminders']:
        session_state['reminders'].remove(reminder)
        return f"Deleted reminder: {reminder}"
    else:
        return "Reminder not found."
    

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
