# Manager (Multi-agent)

Purpose
- Orchestrates sub-agents and exposes a local time tool.

Files
- agent.py: defines root_agent, registers sub_agents and get_current_time_tool.
- sub_agent/: leaf agents grouped by topic.
- tools/: local utilities used by the manager.

Usage
- Imported by 7-multi-agent/main.py which provides an interactive loop.
