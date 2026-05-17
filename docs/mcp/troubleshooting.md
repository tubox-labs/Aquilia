# MCP Troubleshooting

## No tools appear

Run:

```bash
aq mcp doctor --json
```

Confirm the workspace path points at a repository root containing `aquilia/`.

## Agent cannot start the server

Run the configured command manually:

```bash
python -m aquilia.mcp --stdio --workspace .
```

It should wait for JSON-RPC input on stdin.

## Index is stale

Run:

```bash
aq mcp build-index --force --workspace .
```

## Resource read fails

Only relative `aquilia://...` URIs inside the configured root are allowed.
