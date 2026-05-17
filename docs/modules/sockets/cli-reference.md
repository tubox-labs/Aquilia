# Sockets CLI Reference

This page is derived from the mounted Click command tree. If a source file has CLI helper functions but they are not mounted under `aq`, this page states that explicitly.

## Relationship To The `aq` CLI

The following mounted commands map to this subsystem.

| Command | Syntax | Purpose |
| --- | --- | --- |
| `aq ws inspect` | `aq ws inspect [--artifacts-dir VALUE]` | Inspect compiled WebSocket namespaces. |
| `aq ws broadcast` | `aq ws broadcast [--namespace VALUE] [--room VALUE] [--event VALUE] [--payload VALUE]` | Broadcast message to namespace or room. |
| `aq ws gen-client` | `aq ws gen-client [--lang VALUE] [--out VALUE] [--artifacts-dir VALUE]` | Generate TypeScript client SDK from compiled WebSocket artifacts. |
| `aq ws purge-room` | `aq ws purge-room [--namespace VALUE] [--room VALUE] [--redis-url VALUE]` | Purge a room's state from the adapter. |
| `aq ws kick` | `aq ws kick [--conn VALUE] [--reason VALUE] [--redis-url VALUE]` | Kick (disconnect) a WebSocket connection. |

## Detailed Commands

### `aq ws inspect`

Inspect compiled WebSocket namespaces.

```bash
aq ws inspect [--artifacts-dir VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `artifacts_dir` | `--artifacts-dir` | False | `artifacts` | Artifacts directory |

### `aq ws broadcast`

Broadcast message to namespace or room.

```bash
aq ws broadcast [--namespace VALUE] [--room VALUE] [--event VALUE] [--payload VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `namespace` | `--namespace` | True | `not set` | Namespace |
| Option | `room` | `--room` | False | `` | Room (optional) |
| Option | `event` | `--event` | True | `not set` | Event name |
| Option | `payload` | `--payload` | False | `{}` | JSON payload |

### `aq ws gen-client`

Generate TypeScript client SDK from compiled WebSocket artifacts.

```bash
aq ws gen-client [--lang VALUE] [--out VALUE] [--artifacts-dir VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `lang` | `--lang` | False | `ts` | Language (ts) |
| Option | `out` | `--out` | True | `not set` | Output file |
| Option | `artifacts_dir` | `--artifacts-dir` | False | `artifacts` | Artifacts directory |

### `aq ws purge-room`

Purge a room's state from the adapter.

```bash
aq ws purge-room [--namespace VALUE] [--room VALUE] [--redis-url VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `namespace` | `--namespace` | True | `not set` | Namespace |
| Option | `room` | `--room` | True | `not set` | Room to purge |
| Option | `redis_url` | `--redis-url` | False | `` | Redis URL (optional) |

### `aq ws kick`

Kick (disconnect) a WebSocket connection.

```bash
aq ws kick [--conn VALUE] [--reason VALUE] [--redis-url VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `conn` | `--conn` | True | `not set` | Connection ID to disconnect |
| Option | `reason` | `--reason` | False | `kicked by admin` | Reason for kick |
| Option | `redis_url` | `--redis-url` | False | `` | Redis URL (optional) |

## General Commands Useful For This Module

| Command | Why it matters |
| --- | --- |
| `aq validate` | Validates workspace manifests and catches invalid component paths. |
| `aq doctor` | Runs environment, workspace, manifest, registry, integration, and deployment diagnostics. |
| `aq inspect config` | Shows resolved config after workspace/env merging. |
| `aq inspect modules` | Lists discovered modules. |
| `aq inspect routes` | Shows compiled routes when the module contributes controllers. |
| `aq run` | Starts the dev server and executes startup wiring. |

## Error Behavior

- Click handles missing required arguments and invalid options before command callbacks run.
- Most operational commands require `workspace.py`; the root CLI guard allows help/version/init/doctor without it.
- Commands that touch external providers, databases, or files can fail with subsystem-specific faults or provider errors.
