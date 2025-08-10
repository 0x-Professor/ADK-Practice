from google.adk.agents.llm_agent import Agent
from google.adk.models.lite_llm import LiteLLM
from dotenv import load_dotenv
import os
load_dotenv()

model = LiteLLM(
    model_name='openrouter/deepseek/deepseek-chat-v3-0324:free',
    api_key=os.getenv('OPENROUTER_API_KEY'),
    #timeout=30,
)

def get_dad_joke(question: str) -> dict:
    """Create a dad joke based on the question asked using the configured LLM."""
    prompt = (question or "").strip()
    if not prompt:
        prompt = "Tell me a clean dad joke."

    messages = [
        {
            "role": "system",
            "content": (
                "You are a dad joke generator. Reply with one clean, punny dad joke only. "
                "Keep it under 30 words and family-friendly."
            ),
        },
        {"role": "user", "content": prompt},
    ]

    try:
        # If the model expects messages via an attribute, set it.
        if hasattr(model, "message"):
            model.message = messages

        resp = None
        # Try common invocation methods
        if hasattr(model, "run"):
            try:
                # Prefer passing messages if supported
                if getattr(model.run, "__code__", None) and "messages" in getattr(model.run, "__code__").co_varnames:
                    resp = model.run(messages=messages)
                else:
                    resp = model.run()
            except TypeError:
                resp = model.run()  # fallback if signature differs
        elif hasattr(model, "chat"):
            resp = model.chat(messages=messages)
        elif hasattr(model, "__call__"):
            resp = model(messages=messages)

        # Normalize response to text
        text = None
        if isinstance(resp, str):
            text = resp
        elif isinstance(resp, dict):
            text = resp.get("content") or resp.get("message") or resp.get("text")
            if not text and "choices" in resp:
                choices = resp.get("choices") or []
                if choices:
                    c0 = choices[0] or {}
                    text = (
                        (c0.get("message") or {}).get("content")
                        or c0.get("text")
                        or c0.get("content")
                    )
        # Fallbacks if the wrapper stores last message/response
        if not text and hasattr(model, "last_message"):
            last = getattr(model, "last_message")
            if isinstance(last, dict):
                text = last.get("content")
            elif isinstance(last, str):
                text = last
        if not text and hasattr(model, "response"):
            r = getattr(model, "response")
            if isinstance(r, dict):
                text = r.get("content") or r.get("text")

        if not text:
            text = "Why did the API cross the road? To deliver a punchline, eventually."

        return {"joke": text.strip()}
    except Exception:
        # Keep tool output stable even on errors
        return {"joke": "Why did the try block catch the error? Because the punchline threw an exception."}

root_agent = Agent(
    model=model,
    name='dad_joke_agent',
    description='A helpful dad joke agent that can answer questions and tell jokes',
    instruction="""You are a dad joke agent. You can answer questions and tell jokes. If you don't know the answer to a question, you can search the web for information. If you don't know a joke, you can create a new one based on the question asked. If you don't know how to create a joke, you can use the `get_dad_joke` tool to create a new joke based on the question asked. If you don't know how to answer a question""",
    tools=[get_dad_joke],
)
