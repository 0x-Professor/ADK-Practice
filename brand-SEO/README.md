# brand-SEO (root alias)

This folder exists to support the root FastAPI app’s loader, which expects brand-SEO/agent.py at the repository root.

Current status
- The full implementation lives under Agentic-Tools/brand-SEO/.
- To use the root UI without modifying main.py, add a thin wrapper agent.py here that imports and re-exports root_agent from Agentic-Tools.brand-SEO.agent.

Example wrapper (not auto-created):
- from Agentic-Tools.brand-SEO.agent import root_agent

Alternatively
- Keep this folder as-is and run the Agentic-Tools/brand-SEO app directly.
