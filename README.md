# adk-practice

A minimal project that wires Google ADK LlmAgents to create YouTube Shorts scripts with three stages: Scriptwriting, Visualization, and Formatting.

## Project layout
- agent.py — defines Scriptwriter, Visualizer, Formatter, and a root YouTube Shorts agent.
- youtube_shorts_assistant.py — helper to load instruction prompts from text files (with safe fallbacks).
- scriptwriter_instruction.txt — prompt for the Scriptwriter agent.
- visualizer_instruction.txt — prompt for the Visualizer agent.
- main.py — placeholder entry point for custom logic.
- pyproject.toml — dependencies (google-adk).

## Requirements
- Python 3.13+
- A Google ADK compatible environment and credentials for the selected model (gemini-2.0-flash).

## Setup
1) Install dependencies
   - Using uv (recommended):
     - Install uv: https://docs.astral.sh/uv/getting-started/installation/
     - From the project root: `uv sync`
   - Or with pip:
     - `pip install -e .`

2) Configure credentials
   - Ensure your environment is configured to access the `gemini-2.0-flash` model per google-adk documentation (e.g., via environment variables or default application credentials).

## Using the agents
- Import `root_agent` from `agent.py` in your own script to invoke agents and pass a state dict containing a `topic`.
- The Scriptwriter and Visualizer read their prompts from the .txt files.
- The Formatter combines outputs to `formatted_script`.

## Notes
- If instruction files are missing, `youtube_shorts_assistant.load_instruction_from_file` provides sane defaults so the app still runs.
- Adjust `model` values or add tools as needed.

## Web search with images (built-in google_search)
- This repo configures the e-commerce agents to use the built-in `google_search` tool (see `e-commerce/agent.py`).
- Compatibility: requires Gemini 2 models (e.g. `gemini-2.0-flash`).
- Credentials: set `GOOGLE_CSE_ID` and `GOOGLE_SEARCH_API_KEY` in the environment to enable the tool.
- What you get: the tool may return a UI snippet (HTML) in the model response under `renderedContent` that includes images for the query.
- How to show pictures:
  - Preferred: render the returned `renderedContent` HTML in your app’s UI to display image thumbnails and links.
  - Fallback: the agent instructions also ask the LLM to include direct image URLs using markdown image tags (e.g., `![alt](image_url)`) so clients that can’t render HTML can still show images.
- Prompting tip: ask for image-focused queries like “<product> images” (the e-commerce agents are already instructed to do this automatically).