"""
Aquilia Cloud Providers — Pluggable PaaS/IaaS Deployment Backends.

This package provides first-party provider integrations for deploying
Aquilia workspaces to cloud platforms with a single command.

Current providers:

- **render** — Render PaaS (Docker-based, cloud hosting)

Architecture
~~~~~~~~~~~~
Each provider implements:

1. ``client.py``   — API client with retry, auth, rate-limit handling
2. ``deployer.py`` — Orchestrator: build → push → create/update
3. ``store.py``    — Secure credential storage (Crous + HMAC signing)
4. ``types.py``    — Typed dataclasses for API resources
"""

__all__ = ["render"]
