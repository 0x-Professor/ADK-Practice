from google.adk.agents.llm_agent import Agent
from google.adk.tools.tool_context import ToolContext
from dotenv import load_dotenv
from typing import Dict, List
load_dotenv()

# Ensure reminders list exists and return it
def _ensure_reminders(tool_context: ToolContext) -> List[str]:
    state = tool_context.state
    reminders = state.get('reminders') or []
    if not isinstance(reminders, list):
        reminders = []
    state['reminders'] = reminders
    return reminders


def add_reminder(reminder: str, tool_context: ToolContext) -> Dict:
    """Add a reminder to session state using ToolContext."""
    reminder = (reminder or '').strip()
    if not reminder:
        return {"ok": False, "message": "Reminder text is empty."}
    reminders = _ensure_reminders(tool_context)
    if reminder not in reminders:
        reminders.append(reminder)
    return {"ok": True, "message": f"Added reminder: {reminder}", "count": len(reminders), "reminders": reminders}


def view_reminders(tool_context: ToolContext) -> Dict:
    """Return all reminders from session state via ToolContext."""
    reminders = tool_context.state.get('reminders') or []
    return {"ok": True, "reminders": reminders}


def update_reminder(old_reminder: str, new_reminder: str, tool_context: ToolContext) -> Dict:
    """Update an existing reminder in session state via ToolContext."""
    old_reminder = (old_reminder or '').strip()
    new_reminder = (new_reminder or '').strip()
    if not old_reminder or not new_reminder:
        return {"ok": False, "message": "Both old_reminder and new_reminder are required."}
    reminders = _ensure_reminders(tool_context)
    if old_reminder in reminders:
        idx = reminders.index(old_reminder)
        reminders[idx] = new_reminder
        return {"ok": True, "message": f"Updated reminder to: {new_reminder}", "reminders": reminders}
    return {"ok": False, "message": "Reminder not found.", "reminders": reminders}


def delete_reminder(reminder: str, tool_context: ToolContext) -> Dict:
    """Delete a reminder from session state via ToolContext."""
    reminder = (reminder or '').strip()
    if not reminder:
        return {"ok": False, "message": "Reminder text is required."}
    reminders = _ensure_reminders(tool_context)
    if reminder in reminders:
        reminders.remove(reminder)
        return {"ok": True, "message": f"Deleted reminder: {reminder}", "count": len(reminders), "reminders": reminders}
    return {"ok": False, "message": "Reminder not found.", "reminders": reminders}


# Simple memory agent for reminders using session state
memory_agent = Agent(
    model='gemini-2.0-flash',
    name='memory_agent',
    description='A stateful assistant that can remember reminders and recall them later.',
    instruction='''
You are a helpful memory assistant.
- Use the provided tools to manage reminders in the session state.
- For "remember/remind me" intents, call add_reminder(reminder: string).
- To list saved items, call view_reminders().
- To modify an item, call update_reminder(old_reminder: string, new_reminder: string).
- To remove an item, call delete_reminder(reminder: string).
- Always read/write reminders via ToolContext-backed state; do not invent data.
- Keep replies concise and confirm the action and the resulting list when applicable.
''',
    tools=[
        add_reminder,
        view_reminders,
        update_reminder,
        delete_reminder,
    ],
)
