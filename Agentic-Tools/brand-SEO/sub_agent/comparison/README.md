# Comparison Sub-agent

Purpose
- Drafts a competitor comparison and runs a critic pass to ensure schema compliance and actionability.

Files
- agent.py: comparison_agent, comparison_critic_agent, and orchestrator comparison_root_agent.
- prompt.py: JSON-only schemas for draft, critic, and orchestrator.

Output
- comparison_root_agent -> comparison_report (JSON).
