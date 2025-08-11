# Security Policy

Supported versions
- Main branch: actively maintained
- Sample subprojects: provided “as-is” for education; fixes are best-effort

Reporting a vulnerability
- Email: security@adk-practice.local
- Alternatively, open a private security advisory in the repository (preferred when available)
- Please include: affected files/modules, repro steps, severity/impact, environment details (OS, Python, versions)

Coordinated disclosure
- We will acknowledge receipt within 3 business days
- We aim to provide an initial assessment within 7 business days
- Fixes and coordinated disclosure timelines depend on severity and scope

Secrets and data handling
- Do not include secrets in reports; provide redacted logs or minimal repro
- Store API keys in .env files only; never commit secrets
- Rotate exposed credentials immediately and inform us if you suspect leakage

Dependency policy
- We prefer pinned or range-limited dependencies
- Security fixes are prioritized for high-severity CVEs (CVSS ≥ 7.0)
- For Selenium/driver toolchains, keep Chrome/ChromeDriver updated to latest stable

Supply chain
- Review third-party code/tools embedded in examples before use in production
- Lock files (uv.lock) are provided for reproducibility when applicable

Scope
- This repo is educational; examples may trade completeness for clarity
- Report issues that could impact learners (e.g., unsafe examples, injection risks, insecure defaults)
