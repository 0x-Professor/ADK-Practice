# 4-structured-output

Purpose
- Shows how to constrain an agent’s response to a Pydantic schema and return JSON reliably.

Files
- email_agent/agent.py: EmailContent schema and root_agent with output_schema and output_key.
- main.py: placeholder entry point.

Usage
- Import email_agent.agent.root_agent and run via Runner. Prompt the model to produce subject, body, recipient.

Notes
- The agent’s instruction requires returning a JSON object. The ADK runner will validate against EmailContent.
