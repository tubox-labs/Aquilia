# Migration Guide — 1.3.x → 1.4.0b0

## Dashboard / TUI Removed

`aquilia/devplatform/dashboard/` (browser dashboard + Textual TUI) is
deleted entirely. If you had `AQ_DEV_TUI` / `adp_tui` set, or scripts that
opened the ADP dashboard URL, they no longer apply — the field and flag are
gone from `AquilaConfig.Server`, `AquiliaDevelopmentConfig`, and the
CLI-generated `runtime/_adp_app.py` wrapper.

Replacement: Aquilia's Inspector, mounted at `/__aquilia__/inspector`.

```bash
aq inspector                  # opens the Inspector URL in your browser
aq inspector --no-browser     # prints the URL instead
aq inspector --port=3000
```

`Inspector` was already present before this release (`aquilia/inspector/`)
and is unchanged — this release only removes the duplicate, ADP-specific
debugging surface.

## `textual` Dependency Dropped

Removed from core `dependencies` in `pyproject.toml`; `uv.lock` regenerated,
also dropping its transitive dependencies (`rich`, `markdown-it-py`,
`mdit-py-plugins`, `mdurl`, `linkify-it-py`, `uc-micro-py`). If your own
code imported `textual` indirectly through Aquilia, pin it directly in your
own project.

`aquilia.devplatform.profiler.call_tree` still has an optional, lazy `from
rich.tree import Tree` import — this was already guarded with try/except
before this release and continues to degrade gracefully (returns `None`)
when `rich` isn't installed; it is not part of core dependencies.

## New Commands

- **`aq dev`** — alias for `aq run`. Same flags, same behavior; just a
  friendlier name matching the Vite/Next/Bun convention.
- **`aq inspector`** — opens/prints the Inspector URL (see above). Distinct
  from the pre-existing `aq inspect` command group (static
  manifest/DI/route introspection) — the names are similar but the two do
  different things.

## New Network / Transport Flags

`aq run` / `aq dev` gain four new flags:

```
--uds TEXT         Bind to a UNIX domain socket path instead of host:port
--fd INTEGER       Bind to an inherited file descriptor instead of host:port
--http [auto|h11]  HTTP transport engine (default: h11)
--ws [auto|none]   WebSocket support (default: auto)
```

**Behavioral change**: previously, `aq run`/`aq dev` always used uvicorn as
the transport whenever it was installed (a core dependency, so effectively
always) — the ADP's own `AquiliaDevelopmentServer.start()` path only ran as
a fallback when uvicorn was missing. As of this release, the native h11
transport (`--http h11`) is the **default**. If you relied on uvicorn-
specific transport behavior (e.g. HTTP/2, its own `--reload` subprocess
mechanism), pass `--http auto` explicitly, or set `adp_http = "auto"` on
your `AquilaConfig.Server` subclass in `workspace.py`.

```python
# workspace.py — pin to the uvicorn transport if you need it
from aquilia.pyconfig import AquilaConfig

class Server(AquilaConfig.Server):
    adp_http = "auto"
```

No action needed if you don't rely on uvicorn-specific behavior — the new
default is a drop-in HTTP/1.1 server with keep-alive, chunked
transfer-encoding, and WebSocket support.

## Development-Only Enforcement

The ADP is now explicitly a **development** server and refuses to be the
production transport. `AquiliaDevelopmentServer.start()` logs a production
warning, and `aq run` **forces uvicorn in production mode** (`mode="prod"`)
regardless of `use_adp`. The `use_adp` flag (default `True`) is honored only
in dev/test mode.

```python
# workspace.py — production deployments always run uvicorn
class Server(AquilaConfig.Server):
    use_adp = True   # dev/test only; ignored when running in prod mode
```

Deploy production apps with uvicorn (or another mature ASGI server such as
hypercorn or daphne) — the ADP has not been hardened for internet-facing
traffic. No action is needed if you already deploy production with uvicorn;
if you were (incorrectly) running `aq run` in production, switch to a real
ASGI server invocation.

## Config Loading Change

`AquiliaDevelopmentConfig` now resolves each field through
`aquilia.pyconfig.Env` (the framework's native env/dotenv system) instead of
a bespoke `os.environ` reader, and validates all values in `__post_init__`
— an invalid `http`/`ws`/`log_level`, a non-positive threshold, an
out-of-range port, or a negative `fd` now raises a `ConfigurationFault`
(from the new `devplatform` fault domain) at construction instead of being
silently coerced. The `AQ_DEV_*` env var names and precedence are unchanged;
`AQ_DEV_FD=0` now correctly means "bind fd 0" (previously coerced to unset).

## Config Precedence (all network fields)

1. Explicit CLI flags (`--host`, `--port`, `--reload`, `--uds`, `--fd`, `--http`, `--ws`)
2. `AquilaConfig.Server` values from `workspace.py` (`adp_uds`, `adp_http`, `adp_ws`)
3. `AQ_DEV_*` environment variables (resolved via `aquilia.pyconfig.Env`)
4. Hardcoded fallback defaults (`http="h11"`, `ws="auto"`, no `uds`/`fd`)

`uds`/`fd` take priority over `host`/`port` at bind time — set at most one
binding mode.

## Profiler Behavior Change

`profiler_enabled` (config) / `adp_profiler` (workspace config) previously
had no effect on the ADP transport path — `ProfilingMiddleware`, the only
consumer of `cProfilingRunner`, was dead code (unwired, and would have
raised `TypeError` if anyone had tried to register it with
`MiddlewareStack.add()`). As of this release, `profiler_enabled=True`
actually profiles every request, and the `X-Aquilia-Profile: true` request
header enables profiling per-request regardless of the global setting. If
you previously set `profiler_enabled=True` expecting no effect, you will
now see `RequestRecord.profile_stats` populated and a measurable per-request
CPU overhead from `cProfile`.

## No Action Needed For

- `AquiliaDevelopmentConfig`'s other fields (`reload`, `reload_dirs`,
  `reload_excludes`, `log_level`, `inspector_enabled`,
  `max_request_history`, `sql_explain_threshold_ms`,
  `n_plus_one_detection`, `memory_snapshot_interval_s`,
  `timeout_graceful_shutdown`) — unchanged.
- Plugin API (`AquiliaDevelopmentPlugin` protocol, `aquilia_dev.plugins`
  entry point group) — unchanged.
- Hot-reload behavior for typical edits — the AST-based reverse-dependency
  rewrite fixes false positives (see [reload.md](reload.md)); it does not
  change the public `WorkspaceWatcher`/`ModuleReloadExecutor` API.
