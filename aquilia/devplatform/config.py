"""
AquiliaDevelopmentConfig — configuration for the ADP server.

Built on ``aquilia.pyconfig.Env`` (the framework's native env/dotenv
resolution) rather than a hand-rolled ``os.environ`` reader. Server backend
selection lives in ``AquilaConfig.Server.use_adp`` — ADP (default) in
dev/test mode, always uvicorn in production mode.

Config precedence (highest to lowest):
  1. Explicit CLI flags (``--host``, ``--port``, ``--uds``, ...)
  2. ``AquilaConfig.Server`` values from ``workspace.py`` (``adp_*`` keys)
  3. ``Env(...)``-backed environment variables (``AQ_DEV_*`` prefix)
  4. Hardcoded dataclass defaults below
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from aquilia.devplatform.faults import ConfigurationFault
from aquilia.pyconfig import Env
from aquilia.typing.devplatform import AdpLogLevel, AdpTransport, AdpWsMode

_VALID_TRANSPORTS = ("auto", "h11")
_VALID_WS_MODES = ("auto", "none")
_VALID_LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR")

# Default reload exclusions. Defence-in-depth on top of the watcher's
# ``.py``-only filter: even a ``.py`` written into a generated/runtime dir
# (e.g. ``.aquilia/``) must never trigger a reload. The concrete offenders
# today are ``.aquilia/audit.surp`` and ``.aquilia/discovery_cache.surp``,
# written while serving ``/admin/``.
_DEFAULT_RELOAD_EXCLUDES = (
    "*/.aquilia/*",
    "*/.git/*",
    "*/node_modules/*",
    "*/.venv/*",
    "*/__pycache__/*",
    "*/media/*",
    "*.surp",
    "*.db",
    "*.sqlite",
    "*.sqlite3",
    "*.log",
)


def _env_str(key: str, default: str) -> Any:
    return field(default_factory=lambda: Env(f"AQ_DEV_{key}", default=default).resolve())


def _env_int(key: str, default: int | None) -> Any:
    return field(default_factory=lambda: Env(f"AQ_DEV_{key}", default=default, cast=int).resolve())


def _env_bool(key: str, default: bool) -> Any:
    return field(default_factory=lambda: Env(f"AQ_DEV_{key}", default=default, cast=bool).resolve())


def _env_float(key: str, default: float) -> Any:
    return field(default_factory=lambda: Env(f"AQ_DEV_{key}", default=default, cast=float).resolve())


@dataclass
class AquiliaDevelopmentConfig:
    """
    Full configuration schema for the Aquilia Native Development Platform.

    Every field can be overridden via an ``AQ_DEV_``-prefixed environment
    variable (e.g. ``AQ_DEV_PORT=8080``) using ``aquilia.pyconfig.Env``, or
    through the ``adp_*`` keys on ``AquilaConfig.Server`` in ``workspace.py``.

    Usage::

        config = AquiliaDevelopmentConfig(port=8000, reload=True)
        server = AquiliaDevelopmentServer(config)
        await server.start(app)

    Raises:
        ConfigurationFault: if ``__post_init__`` validation fails — an
            invalid ``http``/``ws``/``log_level`` literal, a non-positive
            timing threshold, or a negative file descriptor.
    """

    # Network
    host: str = _env_str("HOST", "127.0.0.1")
    port: int = _env_int("PORT", 8000)
    uds: str | None = field(default_factory=lambda: Env("AQ_DEV_UDS", default=None).resolve())
    fd: int | None = field(default_factory=lambda: Env("AQ_DEV_FD", default=None, cast=int).resolve())

    # Transport engine selection
    http: AdpTransport = _env_str("HTTP", "h11")
    ws: AdpWsMode = _env_str("WS", "auto")

    # Hot reload
    reload: bool = _env_bool("RELOAD", True)
    reload_dirs: list[Path] = field(default_factory=lambda: [Path.cwd()])
    reload_excludes: list[str] = field(default_factory=lambda: list(_DEFAULT_RELOAD_EXCLUDES))

    # Logging
    log_level: AdpLogLevel = _env_str("LOG_LEVEL", "INFO")

    # Inspector / tracing
    inspector_enabled: bool = _env_bool("INSPECTOR_ENABLED", True)
    max_request_history: int = _env_int("MAX_REQUEST_HISTORY", 500)

    # Profiler
    profiler_enabled: bool = _env_bool("PROFILER_ENABLED", False)

    # SQL diagnostics
    sql_explain_threshold_ms: float = _env_float("SQL_EXPLAIN_THRESHOLD_MS", 50.0)
    n_plus_one_detection: bool = _env_bool("N_PLUS_ONE_DETECTION", True)

    # Memory
    memory_snapshot_interval_s: float = _env_float("MEMORY_SNAPSHOT_INTERVAL_S", 30.0)

    # Graceful shutdown
    timeout_graceful_shutdown: float = _env_float("TIMEOUT_GRACEFUL_SHUTDOWN", 5.0)

    def __post_init__(self) -> None:
        """Normalize ``reload_dirs`` and validate all field values.

        Raises:
            ConfigurationFault: on any invalid literal, non-positive
                threshold, or negative file descriptor.
        """
        if isinstance(self.reload_dirs, (str, Path)):
            self.reload_dirs = [Path(self.reload_dirs)]
        else:
            self.reload_dirs = [Path(d) for d in self.reload_dirs]

        if self.http not in _VALID_TRANSPORTS:
            raise ConfigurationFault(f"http must be one of {_VALID_TRANSPORTS}, got {self.http!r}")
        if self.ws not in _VALID_WS_MODES:
            raise ConfigurationFault(f"ws must be one of {_VALID_WS_MODES}, got {self.ws!r}")
        if self.log_level not in _VALID_LOG_LEVELS:
            raise ConfigurationFault(f"log_level must be one of {_VALID_LOG_LEVELS}, got {self.log_level!r}")
        if self.fd is not None and self.fd < 0:
            raise ConfigurationFault(f"fd must be >= 0, got {self.fd!r}")
        if self.port <= 0 or self.port > 65535:
            raise ConfigurationFault(f"port must be in range 1-65535, got {self.port!r}")
        for name, value in (
            ("max_request_history", self.max_request_history),
            ("sql_explain_threshold_ms", self.sql_explain_threshold_ms),
            ("memory_snapshot_interval_s", self.memory_snapshot_interval_s),
            ("timeout_graceful_shutdown", self.timeout_graceful_shutdown),
        ):
            if value <= 0:
                raise ConfigurationFault(f"{name} must be > 0, got {value!r}")

    def to_dict(self) -> dict[str, Any]:
        """Return this config as a plain dict (single source of truth for serialization)."""
        return {
            "host": self.host,
            "port": self.port,
            "uds": self.uds,
            "fd": self.fd,
            "http": self.http,
            "ws": self.ws,
            "reload": self.reload,
            "reload_dirs": [str(d) for d in self.reload_dirs],
            "reload_excludes": list(self.reload_excludes),
            "log_level": self.log_level,
            "inspector_enabled": self.inspector_enabled,
            "max_request_history": self.max_request_history,
            "profiler_enabled": self.profiler_enabled,
            "sql_explain_threshold_ms": self.sql_explain_threshold_ms,
            "n_plus_one_detection": self.n_plus_one_detection,
            "memory_snapshot_interval_s": self.memory_snapshot_interval_s,
            "timeout_graceful_shutdown": self.timeout_graceful_shutdown,
        }
