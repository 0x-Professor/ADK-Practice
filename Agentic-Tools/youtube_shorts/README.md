# YouTube Shorts Agents

Overview
- Scriptwriter: generates a 45–60s narration based on state['topic'].
- Visualizer: turns narration into a concise shot plan.
- Formatter: merges both into a final, ready-to-use script.

Prompts
- scriptwriter_instruction.txt and visualizer_instruction.txt live next to this module.
- If missing, the helper youtube_shorts_assistant.load_instruction_from_file provides sane defaults.

Usage
- Used via the repository root FastAPI app (select a topic and run the LoopAgent flow), or import youtube_shorts.agent.root_agent.
- Optional google_search tool is enabled automatically if GOOGLE_CSE_ID and GOOGLE_SEARCH_API_KEY are set.
