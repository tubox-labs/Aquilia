# aq ws

WebSocket management commands. Inspect compiled WebSocket namespaces, broadcast messages, generate TypeScript client SDKs, and manage connections.

## Usage

```bash
aq ws <SUBCOMMAND> [OPTIONS]
```

## Subcommands

### aq ws inspect

Inspect compiled WebSocket namespaces from artifact files.

```bash
aq ws inspect [OPTIONS]
```

| Option           | Description          | Default      |
| ---------------- | -------------------- | ------------ |
| `--artifacts-dir`| Artifacts directory  | `artifacts`  |

### aq ws broadcast

Broadcast a message to a WebSocket namespace or room.

```bash
aq ws broadcast [OPTIONS]
```

| Option        | Description                       | Required |
| ------------- | --------------------------------- | -------- |
| `--namespace` | Namespace to broadcast to         | Yes      |
| `--room`      | Specific room (optional)          | No       |
| `--event`     | Event name                        | Yes      |
| `--payload`   | JSON payload                      | No (default: `{}`) |

```bash
aq ws broadcast --namespace /chat --event message --payload '{"text": "Hello"}'
aq ws broadcast --namespace /chat --room room1 --event system --payload '{"action": "reload"}'
```

### aq ws gen-client

Generate a TypeScript client SDK from compiled WebSocket artifacts.

```bash
aq ws gen-client [OPTIONS]
```

| Option           | Description          | Required |
| ---------------- | -------------------- | -------- |
| `--lang`         | Language (currently `ts` only) | No (default: `ts`) |
| `--out`          | Output file path     | Yes      |
| `--artifacts-dir`| Artifacts directory  | No (default: `artifacts`) |

```bash
aq ws gen-client --out client/ws-sdk.ts
aq ws gen-client --out dist/chat-client.ts --artifacts-dir build/artifacts
```

### aq ws purge-room

Purge a room's state from the adapter.

```bash
aq ws purge-room [OPTIONS]
```

| Option        | Description                | Required |
| ------------- | -------------------------- | -------- |
| `--namespace` | Namespace                  | Yes      |
| `--room`      | Room to purge              | Yes      |
| `--redis-url` | Redis URL (optional)       | No       |

```bash
aq ws purge-room --namespace /chat --room room1
aq ws purge-room --namespace /chat --room room1 --redis-url redis://localhost:6379/0
```

### aq ws kick

Kick (disconnect) a WebSocket connection by connection ID.

```bash
aq ws kick [OPTIONS]
```

| Option        | Description                | Required |
| ------------- | -------------------------- | -------- |
| `--conn`      | Connection ID to disconnect| Yes      |
| `--reason`    | Reason for kick            | No       |
| `--redis-url` | Redis URL (optional)       | No       |

```bash
aq ws kick --conn abc-123 --reason "violated rules"
aq ws kick --conn xyz-456
```

## Examples

```bash
# Inspect WebSocket namespaces
aq ws inspect

# Broadcast to a namespace
aq ws broadcast --namespace /chat --event message --payload '{"text": "Hello"}'

# Generate TypeScript client
aq ws gen-client --out client/ws-sdk.ts

# Purge a room
aq ws purge-room --namespace /chat --room room1

# Kick a connection
aq ws kick --conn abc-123 --reason "inactive"
```

## See Also

- [WebSocket API](/reference/api/websockets/) — WebSocket programming guide
- [Socket Controller](/reference/classes/socket-controller/) — SocketController class reference