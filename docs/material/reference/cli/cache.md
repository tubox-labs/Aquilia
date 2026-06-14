# aq cache

Check, inspect, clear, and monitor Aquilia's cache layer. Supports memory, Redis, and composite (L1 + L2) backends.

## Usage

```bash
aq cache <SUBCOMMAND> [OPTIONS]
```

## Subcommands

### aq cache check

Validate cache configuration and test backend connectivity.

```bash
aq cache check
```

Reports:

- Backend type (memory, Redis, composite)
- Default TTL, max size, eviction policy
- Serializer and key prefix
- For Redis: connection test with memory usage info
- For Composite: L1/L2 configuration details
- HTTP cache middleware status

Example output:

```
Cache Configuration Check
────────────────────────────────────────
  Enabled:          True
  Backend:          redis
  Default TTL:      300s
  Max Size:         10000
  Eviction Policy:  lru
  Serializer:       json
  Key Prefix:       'aq:'

  Redis Config:
    URL:            redis://localhost:6379/0
    Max Connections: 10
    Socket Timeout:  5s

  Testing Redis connection...
  Redis connection OK
    Used Memory: 2.5M

  Middleware:        enabled
    HTTP TTL:       300s
    Namespace:      'http'

Cache configuration valid
```

### aq cache inspect

Display current cache configuration as JSON.

```bash
aq cache inspect
```

### aq cache stats

Display live cache statistics from the configured backend.

```bash
aq cache stats
```

Requires a reachable cache backend. Displays metrics like hit/miss ratios, entry counts, and memory usage.

### aq cache clear

Clear all or namespace-scoped cache entries.

```bash
aq cache clear [OPTIONS]
```

| Option        | Alias | Description                        | Default |
| ------------- | ----- | ---------------------------------- | ------- |
| `--namespace` | `-n`  | Clear only this namespace          | `None`  |

```bash
aq cache clear
aq cache clear --namespace http
aq cache clear -n sessions
```

!!! warning "Production Caution"
    Clearing the cache in production will invalidate all cached responses, sessions, and computed values. Use namespace-scoped clears when possible.

## Examples

```bash
aq cache check
aq cache inspect
aq cache stats
aq cache clear
aq cache clear --namespace http
```

## See Also

- [Cache Service](/reference/classes/cache-service/) — CacheService API reference