# MCP Security

Aquilia MCP is read-only by default.

Security controls:

- Resource reads are sandboxed to the configured root.
- Null-byte and path traversal attempts are rejected.
- Binary and generated artifacts are excluded from the source index.
- Tool inputs are schema-validated.
- Tool outputs are bounded and deterministic.
- Secret-like lines are redacted from indexed snippets.
- The server does not expose shell execution or file mutation tools.

Installer commands modify only local agent configuration files and keep timestamped backups.
