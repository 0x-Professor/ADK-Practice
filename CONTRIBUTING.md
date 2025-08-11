# Contributing to ADK Practice

Thanks for helping make this an educational, production-quality reference for agentic apps with Google ADK.

Ways to contribute
- Improve examples: new agents, tools, or patterns that teach a concept clearly.
- Fix bugs: repro steps, minimal fixes, and short explanations.
- Documentation: README clarifications, troubleshooting tips, screenshots/GIFs.
- Performance/quality: safer tool execution, clearer prompts, better state handling.

Prerequisites (Windows-friendly)
- Python 3.13+
- Optional: uv for dependency sync (pip install uv)
- Chrome/Chromium for Brand-SEO SERP parsing (Selenium)
- ADK Web (if you prefer running in a UI) or Python CLI

Setup
- Clone the repo
- Copy .env.example to .env and fill relevant keys
- Install deps (one of):
  - uv sync
  - py -m pip install -e .

Running examples
- ADK Web: open this repo folder and use the built-in runner
- CLI scripts: see Practice/* READMEs (e.g., py Practice\7-multi-agent\main.py)
- Local web UI (optional): py -m uvicorn main:app --reload

Branching and commits
- Create feature branches: feature/my-change, fix/bug-123, docs/update-readme
- Use Conventional Commits where possible:
  - feat: add new agent or tool
  - fix: correct behavior or bug
  - docs: README, examples, screenshots
  - chore/build/test: infra changes

Code style
- Python: type hints where practical, small functions, readable names
- Follow PEP 8/PEP 257; include docstrings for tools (improves function schemas)
- Keep examples self-contained and runnable on Windows
- Avoid breaking changes in learning paths without updating docs

Security and secrets
- Never commit secrets. Use .env and .env.example
- Do not post API keys in issues/PRs; redact outputs
- See SECURITY.md for vulnerability reporting

Pull request checklist
- Builds/runs on Windows
- Updated or verified README(s)
- Added/updated .env.example if needed
- Added screenshots/GIFs under docs/assets if user-facing
- Clear before/after explanation in the PR description

How reviews work
- Small, focused PRs are easier to review
- We prioritize clarity and educational value
- Maintain backwards-compatible learning flows when possible
