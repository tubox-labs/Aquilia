"""
AquiliaRuntime — Structured ASGI Bootstrap Lifecycle Manager.

Replaces the procedural, auto-generated ``runtime/app.py`` with a typed,
phase-gated class that encapsulates the full application lifecycle:

    CREATED → CONFIGURING → DISCOVERING → BOOTSTRAPPING → READY → RUNNING → STOPPED

Architecture
------------
The runtime consolidates three previously duplicated bootstrap paths
(CLI generator, ``entrypoint.py``, generated ``app.py``) into a single,
reusable orchestrator that leverages Aquilia's native module system.

Usage
-----
Fluent API (explicit control)::

    from aquilia.runtime import AquiliaRuntime, RuntimeConfig

    config = RuntimeConfig(workspace_root=Path.cwd(), mode="dev")
    runtime = AquiliaRuntime(config).configure().discover().bootstrap()
    app = runtime.app

Factory shortcut (one-liner)::

    from aquilia.runtime import AquiliaRuntime

    app = AquiliaRuntime.create_app()

ASGI Servers::

    uvicorn runtime.app:app
    gunicorn runtime.app:app -k uvicorn.workers.UvicornWorker
    hypercorn runtime.app:app --bind 0.0.0.0:8000
"""

from __future__ import annotations

import importlib
import importlib.util
import logging
import os
import re
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Literal

from .typing import ASGIApplication
from .typing.manifest import ManifestCollection

__all__ = [
    "AquiliaRuntime",
    "RuntimeConfig",
    "RuntimePhase",
]

_logger = logging.getLogger("aquilia.runtime")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Phase Enum
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class RuntimePhase(str, Enum):
    """Lifecycle phase of an :class:`AquiliaRuntime` instance.

    The runtime progresses linearly through these phases::

        CREATED → CONFIGURING → DISCOVERING → BOOTSTRAPPING → READY
        READY → RUNNING (after ASGI lifespan startup)
        RUNNING → SHUTTING_DOWN → STOPPED
        Any → FAILED (on unrecoverable error)
    """

    CREATED = "created"
    CONFIGURING = "configuring"
    DISCOVERING = "discovering"
    BOOTSTRAPPING = "bootstrapping"
    READY = "ready"
    RUNNING = "running"
    SHUTTING_DOWN = "shutting_down"
    STOPPED = "stopped"
    FAILED = "failed"


# Explicit ordering for phase comparisons (avoids relying on str >=)
_PHASE_ORDER: dict[RuntimePhase, int] = {
    RuntimePhase.CREATED: 0,
    RuntimePhase.CONFIGURING: 1,
    RuntimePhase.DISCOVERING: 2,
    RuntimePhase.BOOTSTRAPPING: 3,
    RuntimePhase.READY: 4,
    RuntimePhase.RUNNING: 5,
    RuntimePhase.SHUTTING_DOWN: 6,
    RuntimePhase.STOPPED: 7,
    RuntimePhase.FAILED: -1,
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Configuration Dataclass
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@dataclass(frozen=True)
class RuntimeConfig:
    """Immutable configuration for an :class:`AquiliaRuntime` instance.

    All parameters are validated at construction time.  The ``frozen=True``
    flag ensures that configuration cannot be mutated after the runtime has
    been created — preventing a class of subtle bugs where config drifts
    between phases.

    Attributes:
        workspace_root: Absolute path to the workspace directory containing
            ``workspace.py`` and the ``modules/`` tree.
        mode: Runtime mode — controls debug logging, secure cookie defaults,
            signing key fallback, and ``RegistryMode`` selection.
        debug: Explicit debug flag.  When ``None``, derived from *mode*.
        config_overrides: Extra key/value pairs merged into ``ConfigLoader``
            with the highest precedence.
    """

    workspace_root: Path
    mode: Literal["dev", "test", "prod"] = "prod"
    debug: bool | None = None
    config_overrides: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Normalise workspace_root to an absolute path
        if not self.workspace_root.is_absolute():
            object.__setattr__(
                self, "workspace_root", self.workspace_root.resolve()
            )

        # Derive debug from mode when not explicitly set
        if self.debug is None:
            object.__setattr__(self, "debug", self.mode == "dev")

    @property
    def is_dev(self) -> bool:
        """Whether the runtime is in development mode."""
        return self.mode == "dev"

    @property
    def workspace_file(self) -> Path:
        """Path to ``workspace.py``."""
        return self.workspace_root / "workspace.py"

    @property
    def modules_dir(self) -> Path:
        """Path to the ``modules/`` directory."""
        return self.workspace_root / "modules"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Colour Formatter (shared with entrypoint / generated app.py)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class _ColorFormatter(logging.Formatter):
    """Coloured log formatter for terminal output (dev mode)."""

    _COLORS: dict[int, str] = {
        logging.DEBUG: "\033[36m",     # cyan
        logging.INFO: "\033[32m",      # green
        logging.WARNING: "\033[33m",   # yellow
        logging.ERROR: "\033[31m",     # red
        logging.CRITICAL: "\033[1;31m",  # bold red
    }
    _RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self._COLORS.get(record.levelno, "")
        msg = super().format(record)
        return f"{color}{msg}{self._RESET}" if color else msg


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Runtime Class
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class AquiliaRuntime:
    """Structured ASGI bootstrap lifecycle manager.

    Encapsulates the full application bootstrap into discrete, auditable
    phases with typed access guards.  Each phase is idempotent — calling
    ``configure()`` twice is a no-op.

    The runtime is designed to be the **single source of truth** for
    application bootstrapping, replacing the three previously duplicated
    paths (CLI generator, entrypoint factory, generated ``app.py``).

    Example::

        runtime = AquiliaRuntime.from_workspace(mode="dev")
        app = runtime.app       # ASGI callable
        server = runtime.server  # AquiliaServer instance

    Fluent chaining::

        runtime = (
            AquiliaRuntime(RuntimeConfig(workspace_root=Path.cwd()))
            .configure()
            .discover()
            .bootstrap()
        )

    Attributes:
        config: The immutable :class:`RuntimeConfig`.
        phase: Current :class:`RuntimePhase`.
    """

    __slots__ = (
        "config",
        "_phase",
        "_config_loader",
        "_manifests",
        "_workspace_modules",
        "_server",
        "_workspace_name",
        "_module_names",
    )

    def __init__(self, config: RuntimeConfig) -> None:
        """Create a new runtime in the ``CREATED`` phase.

        Args:
            config: Immutable runtime configuration.

        Raises:
            TypeError: If *config* is not a :class:`RuntimeConfig`.
        """
        if not isinstance(config, RuntimeConfig):
            raise TypeError(
                f"Expected RuntimeConfig, got {type(config).__name__}"
            )
        self.config: RuntimeConfig = config
        self._phase: RuntimePhase = RuntimePhase.CREATED

        # Populated during lifecycle phases
        self._config_loader: Any = None       # ConfigLoader
        self._manifests: ManifestCollection = []
        self._workspace_modules: dict[str, dict[str, Any]] = {}
        self._server: Any = None              # AquiliaServer
        self._workspace_name: str = "aquilia-app"
        self._module_names: list[str] = []

    # ──────────────────────────────────────────────────────────────────────
    # Properties
    # ──────────────────────────────────────────────────────────────────────

    @property
    def phase(self) -> RuntimePhase:
        """Current lifecycle phase."""
        return self._phase

    @property
    def app(self) -> ASGIApplication:
        """The ASGI application callable.

        Raises:
            RuntimeError: If the runtime has not reached ``READY`` phase.
        """
        if self._phase not in (
            RuntimePhase.READY,
            RuntimePhase.RUNNING,
        ):
            raise RuntimeError(
                f"Cannot access 'app' in phase '{self._phase.value}'. "
                f"Call configure().discover().bootstrap() first."
            )
        return self._server.app

    @property
    def server(self) -> Any:
        """The :class:`~aquilia.server.AquiliaServer` instance.

        Raises:
            RuntimeError: If the runtime has not reached ``READY`` phase.
        """
        if self._phase not in (
            RuntimePhase.READY,
            RuntimePhase.RUNNING,
        ):
            raise RuntimeError(
                f"Cannot access 'server' in phase '{self._phase.value}'. "
                f"Call configure().discover().bootstrap() first."
            )
        return self._server

    @property
    def workspace_name(self) -> str:
        """Workspace name extracted from ``workspace.py``."""
        return self._workspace_name

    @property
    def module_names(self) -> list[str]:
        """List of discovered module names."""
        return list(self._module_names)

    # ──────────────────────────────────────────────────────────────────────
    # Phase 1: CONFIGURE
    # ──────────────────────────────────────────────────────────────────────

    def configure(self) -> AquiliaRuntime:
        """Bootstrap paths, environment variables, logging, and config.

        **Idempotent**: returns ``self`` unchanged if already past this phase.

        Actions:
        1. Insert workspace root into ``sys.path``
        2. Set ``AQUILIA_ENV`` and ``AQUILIA_WORKSPACE`` environment defaults
        3. Configure structured, mode-aware logging
        4. Load ``workspace.py`` via :class:`~aquilia.config.ConfigLoader`

        Returns:
            ``self`` for fluent chaining.

        Raises:
            FileNotFoundError: If ``workspace.py`` does not exist.
        """
        if _PHASE_ORDER[self._phase] >= _PHASE_ORDER[RuntimePhase.CONFIGURING] and self._phase != RuntimePhase.CREATED:
            return self

        self._phase = RuntimePhase.CONFIGURING
        try:
            # 1. Path bootstrap
            ws_str = str(self.config.workspace_root)
            if ws_str not in sys.path:
                sys.path.insert(0, ws_str)

            # 2. Environment defaults
            os.environ.setdefault("AQUILIA_ENV", self.config.mode)
            os.environ.setdefault("AQUILIA_WORKSPACE", ws_str)

            # 3. Logging
            self._setup_logging()

            # 4. Configuration
            if not self.config.workspace_file.exists():
                raise FileNotFoundError(
                    f"workspace.py not found at {self.config.workspace_root}. "
                    f"Set AQUILIA_WORKSPACE to the correct path."
                )

            from .config import ConfigLoader

            overrides: dict[str, Any] = {
                "mode": self.config.mode,
                "debug": str(self.config.debug),
            }
            overrides.update(self.config.config_overrides)

            self._config_loader = ConfigLoader.load(
                paths=["workspace.py"],
                overrides=overrides,
            )

        except Exception:
            self._phase = RuntimePhase.FAILED
            raise

        return self

    # ──────────────────────────────────────────────────────────────────────
    # Phase 2: DISCOVER
    # ──────────────────────────────────────────────────────────────────────

    def discover(self) -> AquiliaRuntime:
        """Discover workspace name, module manifests, and workspace module configs.

        **Idempotent**: returns ``self`` unchanged if already past this phase.

        Actions:
        1. Parse ``workspace.py`` to extract workspace name and module names
        2. Import manifest objects from ``modules/<name>/manifest.py`` (static)
        3. Dynamically discover any extra modules not declared in ``workspace.py``
        4. Populate the ``apps`` namespace in ``ConfigLoader``
        5. Load workspace module configs (``route_prefix``, etc.)

        Returns:
            ``self`` for fluent chaining.

        Raises:
            RuntimeError: If :meth:`configure` has not been called.
        """
        if self._phase == RuntimePhase.CREATED:
            raise RuntimeError(
                "Cannot discover before configure(). "
                "Call runtime.configure().discover()."
            )
        if _PHASE_ORDER[self._phase] >= _PHASE_ORDER[RuntimePhase.DISCOVERING] and self._phase != RuntimePhase.CONFIGURING:
            return self

        self._phase = RuntimePhase.DISCOVERING
        try:
            workspace_content = self.config.workspace_file.read_text(
                encoding="utf-8"
            )

            # 1. Extract workspace name
            self._workspace_name = self._extract_workspace_name(
                workspace_content
            )

            # 2. Extract declared module names
            self._module_names = self._extract_module_names(workspace_content)

            # 3. Ensure apps namespace
            if "apps" not in self._config_loader.config_data:
                self._config_loader.config_data["apps"] = {}

            # 4. Import static manifests
            self._manifests = []
            for mod_name in self._module_names:
                self._config_loader.config_data["apps"].setdefault(
                    mod_name, {}
                )
                try:
                    mod = importlib.import_module(
                        f"modules.{mod_name}.manifest"
                    )
                    manifest = getattr(mod, "manifest", None)
                    if manifest is not None:
                        self._manifests.append(manifest)
                    else:
                        _logger.warning(
                            "No 'manifest' attribute in modules.%s.manifest",
                            mod_name,
                        )
                except Exception as exc:
                    _logger.error(
                        "Failed to import manifest for %s: %s",
                        mod_name,
                        exc,
                    )

            # 5. Dynamic discovery — pick up modules added after last build
            known = set(self._module_names)
            if self.config.modules_dir.is_dir():
                for pkg in sorted(self.config.modules_dir.iterdir()):
                    if (
                        pkg.is_dir()
                        and pkg.name not in known
                        and (pkg / "manifest.py").exists()
                        and not pkg.name.startswith(("_", "."))
                    ):
                        try:
                            mod = importlib.import_module(
                                f"modules.{pkg.name}.manifest"
                            )
                            m = getattr(mod, "manifest", None)
                            if m is not None:
                                self._manifests.append(m)
                                self._config_loader.config_data[
                                    "apps"
                                ].setdefault(pkg.name, {})
                                self._module_names.append(pkg.name)
                        except Exception as exc:
                            _logger.warning(
                                "Could not import manifest for %s: %s",
                                pkg.name,
                                exc,
                            )

            # 6. Rebuild apps namespace
            self._config_loader._build_apps_namespace()

            # 7. Load workspace module configs (route_prefix, etc.)
            self._workspace_modules = self._load_workspace_modules()

        except Exception:
            self._phase = RuntimePhase.FAILED
            raise

        return self

    # ──────────────────────────────────────────────────────────────────────
    # Phase 3: BOOTSTRAP
    # ──────────────────────────────────────────────────────────────────────

    def bootstrap(self) -> AquiliaRuntime:
        """Construct the :class:`~aquilia.server.AquiliaServer`.

        **Idempotent**: returns ``self`` unchanged if already past this phase.

        Actions:
        1. Resolve ``RegistryMode`` from the configured mode
        2. Construct ``AquiliaServer`` with manifests, config, and mode
        3. Transition to ``READY`` phase

        Returns:
            ``self`` for fluent chaining.

        Raises:
            RuntimeError: If :meth:`discover` has not been called.
        """
        if self._phase in (RuntimePhase.CREATED, RuntimePhase.CONFIGURING):
            raise RuntimeError(
                "Cannot bootstrap before discover(). "
                "Call runtime.configure().discover().bootstrap()."
            )
        if _PHASE_ORDER[self._phase] >= _PHASE_ORDER[RuntimePhase.BOOTSTRAPPING] and self._phase != RuntimePhase.DISCOVERING:
            return self

        self._phase = RuntimePhase.BOOTSTRAPPING
        try:
            from .aquilary import RegistryMode
            from .server import AquiliaServer

            mode_map: dict[str, RegistryMode] = {
                "dev": RegistryMode.DEV,
                "prod": RegistryMode.PROD,
                "test": RegistryMode.TEST,
            }
            registry_mode = mode_map.get(self.config.mode, RegistryMode.PROD)

            self._server = AquiliaServer(
                manifests=self._manifests,
                config=self._config_loader,
                mode=registry_mode,
                workspace_modules=self._workspace_modules,
            )

            self._phase = RuntimePhase.READY

        except Exception:
            self._phase = RuntimePhase.FAILED
            raise

        return self

    # ──────────────────────────────────────────────────────────────────────
    # Factory Class Methods
    # ──────────────────────────────────────────────────────────────────────

    @classmethod
    def from_workspace(
        cls,
        workspace_root: Path | str | None = None,
        mode: str | None = None,
        *,
        config_overrides: dict[str, Any] | None = None,
    ) -> AquiliaRuntime:
        """Create a fully bootstrapped runtime from workspace configuration.

        This is the recommended factory for most use-cases.  It resolves
        the workspace root and mode from environment variables when not
        provided explicitly, then runs the full ``configure → discover →
        bootstrap`` pipeline.

        Args:
            workspace_root: Path to workspace directory.  Defaults to
                ``AQUILIA_WORKSPACE`` env var, then ``Path.cwd()``.
            mode: Runtime mode (``dev``, ``test``, ``prod``).  Defaults to
                ``AQUILIA_ENV`` env var, then ``"prod"``.
            config_overrides: Extra config keys merged at highest precedence.

        Returns:
            A fully initialised :class:`AquiliaRuntime` in ``READY`` phase.

        Raises:
            FileNotFoundError: If ``workspace.py`` is not found.
        """
        # Resolve workspace root
        if workspace_root is None:
            ws_env = os.environ.get("AQUILIA_WORKSPACE", "").strip()
            workspace_root = Path(ws_env) if ws_env else Path.cwd()
        elif isinstance(workspace_root, str):
            workspace_root = Path(workspace_root)

        # Resolve mode
        if mode is None:
            mode = os.environ.get("AQUILIA_ENV", "prod").strip().lower()
            if mode == "production":
                mode = "prod"

        # Validate mode
        valid_modes = {"dev", "test", "prod"}
        if mode not in valid_modes:
            _logger.warning(
                "Invalid mode %r, falling back to 'prod'. "
                "Valid modes: %s",
                mode,
                ", ".join(sorted(valid_modes)),
            )
            mode = "prod"

        rc = RuntimeConfig(
            workspace_root=workspace_root,
            mode=mode,  # type: ignore[arg-type]
            config_overrides=config_overrides or {},
        )

        return cls(rc).configure().discover().bootstrap()

    @classmethod
    def create_app(
        cls,
        workspace_root: Path | str | None = None,
        mode: str | None = None,
        *,
        config_overrides: dict[str, Any] | None = None,
    ) -> ASGIApplication:
        """One-liner factory returning just the ASGI callable.

        Equivalent to ``AquiliaRuntime.from_workspace(...).app``.

        Args:
            workspace_root: Path to workspace directory.
            mode: Runtime mode.
            config_overrides: Extra config overrides.

        Returns:
            The ASGI application callable.
        """
        runtime = cls.from_workspace(
            workspace_root=workspace_root,
            mode=mode,
            config_overrides=config_overrides,
        )
        return runtime.app

    # ──────────────────────────────────────────────────────────────────────
    # Private Helpers
    # ──────────────────────────────────────────────────────────────────────

    def _setup_logging(self) -> None:
        """Configure structured, mode-aware, coloured logging."""
        level = logging.DEBUG if self.config.is_dev else logging.INFO
        fmt = (
            "%(asctime)s | %(levelname)-8s | %(name)s — %(message)s"
            if self.config.mode == "prod"
            else "%(levelname)-8s | %(name)s — %(message)s"
        )

        handler = logging.StreamHandler()
        if self.config.is_dev:
            handler.setFormatter(_ColorFormatter(fmt))
        else:
            handler.setFormatter(logging.Formatter(fmt))

        logging.root.handlers.clear()
        logging.root.addHandler(handler)
        logging.root.setLevel(level)

        # Silence noisy third-party loggers
        for name in (
            "aquilia.sqlite",
            "asyncio",
            "urllib3",
            "httpcore",
            "httpx",
            "watchfiles",
            "uvicorn.error",
            "python_multipart",
            "python_multipart.multipart",
        ):
            logging.getLogger(name).setLevel(logging.WARNING)

    @staticmethod
    def _extract_workspace_name(content: str) -> str:
        """Extract workspace name from ``workspace.py`` content."""
        match = re.search(
            r'Workspace\(\s*(?:name\s*=\s*)?["\']([^"\']+)["\']',
            content,
        )
        return match.group(1) if match else "aquilia-app"

    @staticmethod
    def _extract_module_names(content: str) -> list[str]:
        """Extract module names from ``workspace.py``, excluding comments."""
        clean_lines = [
            line
            for line in content.splitlines()
            if not line.strip().startswith("#")
        ]
        clean = "\n".join(clean_lines)

        modules = re.findall(
            r'\.module\(\s*Module\(\s*["\']([^"\']+)["\']',
            clean,
        )

        # Deduplicate preserving order, exclude the starter pseudo-module
        seen: set[str] = set()
        result: list[str] = []
        for m in modules:
            if m not in seen and m != "starter":
                seen.add(m)
                result.append(m)
        return result

    def _load_workspace_modules(self) -> dict[str, dict[str, Any]]:
        """Load module configs from ``workspace.py`` Workspace object."""
        ws_file = self.config.workspace_file
        if not ws_file.exists():
            return {}

        try:
            spec = importlib.util.spec_from_file_location(
                "_aq_runtime_ws_loader", ws_file
            )
            if spec is None or spec.loader is None:
                _logger.warning(
                    "Failed to create module spec for workspace.py"
                )
                return {}

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            workspace = getattr(module, "workspace", None)
            if workspace is None:
                _logger.warning(
                    "No 'workspace' object found in workspace.py"
                )
                return {}

            ws_dict = workspace.to_dict()
            modules_list = ws_dict.get("modules", [])
            return {m["name"]: m for m in modules_list if "name" in m}

        except Exception as exc:
            _logger.warning("Failed to load workspace modules: %s", exc)
            return {}

    # ──────────────────────────────────────────────────────────────────────
    # Dunder Methods
    # ──────────────────────────────────────────────────────────────────────

    def __repr__(self) -> str:
        return (
            f"<AquiliaRuntime "
            f"workspace={self._workspace_name!r} "
            f"mode={self.config.mode!r} "
            f"phase={self._phase.value!r} "
            f"modules={len(self._module_names)}>"
        )

    def __str__(self) -> str:
        return (
            f"AquiliaRuntime({self._workspace_name}, "
            f"mode={self.config.mode}, phase={self._phase.value})"
        )
