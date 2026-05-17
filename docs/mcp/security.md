# MCP Security

Aquilia MCP is read-only by default.

## Boundaries

- No arbitrary shell execution tools are registered.
- Tools return plans, validation, source anchors, and prompts; they do not write application files.
- Resource reads must resolve under the configured workspace root.
- Absolute paths, `..` traversal, null bytes, directories, missing files, and known binary extensions are rejected.
- Indexed text redacts secret-like lines containing markers such as `password`, `secret`, `token`, `api_key`, or `credential`.
- Request and resource sizes are bounded by `MCPConfig`.

## Installer Behavior

Installers only patch local JSON config files for the selected agent. Existing configs are backed up before write. Dry-run returns the proposed config without writing.

## Diagnostics

`aq mcp doctor --json` reports tool, prompt, source, and fingerprint metadata without dumping indexed source text or environment variables.

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
