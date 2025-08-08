# Reuse the root_agent defined in the top-level agent.py module
# ADK will import youtube_shorts.agent and look for `root_agent`.
import agent as _top_level

root_agent = _top_level.root_agent
