from google.adk.agents import LlmAgent, LoopAgent
from google.adk.tools import google_search
from dotenv import load_dotenv
from pathlib import Path
import os

# Load environment variables from a local .env file next to this module (preferred)
# If that file does not exist, fall back to the default dotenv search.
if not load_dotenv(Path(__file__).with_name(".env")):
    load_dotenv()

from .youtube_shorts_assistant import load_instruction_from_file

# Enable web search only if expected credentials are present to avoid runtime failures.
ENABLE_SEARCH_TOOL = bool(
    os.getenv("GOOGLE_CSE_ID") and os.getenv("GOOGLE_SEARCH_API_KEY")
)
TOOLS = [google_search] if ENABLE_SEARCH_TOOL else []

scriptwriter_agent = LlmAgent(
    name="Scriptwriter",
    model='gemini-2.0-flash',
    instruction=load_instruction_from_file("scriptwriter_instruction.txt"),
    tools=TOOLS,
    output_key='generated_script'
)

visualizer_agent = LlmAgent(
    name="Visualizer",
    model='gemini-2.0-flash',
    instruction=load_instruction_from_file("visualizer_instruction.txt"),
    tools=TOOLS,
    output_key='visualization_script'
)

format_agent = LlmAgent(
    name="Formatter",
    model='gemini-2.0-flash',
    instruction="""Combine the script from state['generated_script'] and visualization state['visualization_script'] into a final YouTube Shorts script. Ensure it is concise, engaging, and formatted correctly for YouTube Shorts. The script should be no longer than 60 seconds when read aloud.
You will receive the script and visualization as inputs. Format the output as a single script ready for YouTube Shorts, including any necessary transitions or cues for visuals.
Output the final script as a single string.""",
    description="Combines the script and visualization into a final YouTube Shorts script.",
    output_key='formatted_script'
)

#youtube_shorts_agent = LoopAgent(
#    name="YouTube_Shorts_Agent",
#    model='gemini-2.0-flash',
#   instruction="""You are an expert in creating engaging YouTube Shorts scripts. Your task is to generate a script based on the provided topic, ensuring it is concise, engaging, and suitable for YouTube Shorts format.""",
#   description="you are an expert in creating engaging YouTube Shorts scripts.",
#   sub_agents=[
#       scriptwriter_agent,
#        visualizer_agent,
#        format_agent,
#   ]
#)

youtube_shorts_agent = LoopAgent(
    name="YouTube_Shorts_Agent",
    
    max_iterations=3,
    sub_agents=[
        scriptwriter_agent,
        visualizer_agent,
        format_agent,
    ]
)

root_agent = youtube_shorts_agent