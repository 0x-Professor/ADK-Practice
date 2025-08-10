try:
    from .agent import question_answering_agent
except Exception:  # fallback for direct execution contexts
    from importlib import import_module as _import_module
    question_answering_agent = _import_module("question_answering_agent.agent").question_answering_agent

__all__ = ["question_answering_agent"]
