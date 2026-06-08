# MCP Troubleshooting

## `mcp.root` Is Invalid

Run commands from the repository root or pass `--workspace /path/to/Aquilia`. The root must contain an `aquilia/` directory.

## Tool List Is Empty

Rebuild the index and run doctor:

```bash
aq mcp build-index --workspace . --force
aq mcp doctor --json
```

## Agent Cannot Start Server

Confirm the command works directly:

```bash
python -m aquilia.mcp --stdio --workspace .
```

For old configs, `python -m aquilia.mcp` is still supported.

## Resource Read Fails

`resources/read` only accepts `aquilia://relative/path` URIs or relative paths under the configured root. Binary files, directories, absolute paths, missing files, and traversal outside the root are blocked.

## Stale Results

The index is reused when the source tree fingerprint is unchanged. Pass `--force` to rebuild when debugging suspicious search results.

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
