"""
DI runtime settings — typed, fault-based configuration for the container.

The DI subsystem historically read a couple of loose ``os.environ`` flags
(e.g. strict-scope enforcement). This module centralises **all** DI runtime
knobs into a single typed :class:`DISettings` object that is:

* **Typed** — every field is annotated; consumed via :mod:`aquilia.typing`.
* **Fault-based** — invalid values raise :class:`~aquilia.faults.domains.DIFault`
  subclasses, never bare :class:`ValueError`/:class:`RuntimeError`.
* **Config-driven** — populated from :class:`aquilia.pyconfig.AquilaConfig`'s
  ``di`` section via :meth:`DISettings.from_mapping`, so users configure the
  container the same way they configure every other subsystem.

Access pattern::

    from aquilia.di.settings import get_di_settings

    if get_di_settings().strict_scopes:
        ...

The active settings object is a process-global singleton, installed once at
server boot by :func:`configure_di`. Until then a permissive default applies,
so importing the DI system in isolation (tests, scripts) needs no setup.

Example — configure explicitly (e.g. in a test)::

    from aquilia.di.settings import DISettings, configure_di

    configure_di(DISettings(scope_enforcement="raise", parallel_resolution=True))
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import Any, Final

from ..faults.domains import DIFault

# ── Valid enumerations (kept here to avoid import cycles with scopes.py) ──

#: Disposal strategies accepted for finalizer ordering.
_VALID_DISPOSAL: Final[frozenset[str]] = frozenset({"lifo", "fifo", "parallel"})

#: Scope-enforcement modes.
#:   * ``"warn"``  — log a warning on captive-dependency violations (default).
#:   * ``"raise"`` — raise :class:`~aquilia.di.errors.ScopeViolationError`.
#:   * ``"off"``   — skip the check entirely (fastest; use only when proven safe).
_VALID_SCOPE_ENFORCEMENT: Final[frozenset[str]] = frozenset({"warn", "raise", "off"})


class DIConfigFault(DIFault):
    """Raised when DI settings contain an invalid value.

    A configuration-time fault (bad ``di`` section in ``workspace.py``),
    surfaced at boot rather than at first resolution.
    """

    def __init__(self, field_name: str, value: Any, reason: str) -> None:
        super().__init__(
            code="DI_CONFIG_INVALID",
            message=f"Invalid DI setting {field_name!r}={value!r}: {reason}",
            metadata={"field": field_name, "value": repr(value), "reason": reason},
        )


@dataclass(frozen=True, slots=True)
class DISettings:
    """Immutable, typed runtime configuration for the DI container.

    Every field maps 1:1 to a key under the ``di`` section of an
    :class:`aquilia.pyconfig.AquilaConfig`. Construct directly for tests, or
    build from config with :meth:`from_mapping`.

    Attributes:
        scope_enforcement: How captive-dependency violations are handled —
            ``"warn"`` (default), ``"raise"``, or ``"off"``.
        parallel_resolution: Resolve independent constructor dependencies
            concurrently with ``asyncio.gather`` instead of sequentially.
        diagnostics_enabled: Emit ``RESOLUTION_START/SUCCESS/FAILURE`` events
            around each provider instantiation (small per-resolve overhead).
        disposal_strategy: Finalizer ordering — ``"lifo"`` (default),
            ``"fifo"``, or ``"parallel"``.
        hook_timeout_seconds: Per-hook timeout for startup/shutdown hooks.
        pool_acquire_timeout_seconds: Default pool acquire timeout.
        pool_max_waiters: Optional cap on concurrent waiters queued against an
            exhausted pool (fast-fail under overload). ``None`` = unbounded.
        type_key_cache_max: Upper bound on the global type→key cache before a
            wholesale flush.
        enable_conditional_providers: Honour ``@conditional`` / ``when=``
            predicates during registration (env/feature-gated providers).
        enable_plugins: Run registered :class:`~aquilia.di.plugins.DIPlugin`
            hooks during registry build.
        strict_service_registration: Fail-fast at boot when a service fails to
            register, instead of logging a warning and continuing.

    Example::

        settings = DISettings(
            scope_enforcement="raise",
            parallel_resolution=True,
            pool_max_waiters=256,
        )
    """

    scope_enforcement: str = "warn"
    parallel_resolution: bool = False
    diagnostics_enabled: bool = False
    disposal_strategy: str = "lifo"
    hook_timeout_seconds: float = 30.0
    pool_acquire_timeout_seconds: float = 30.0
    pool_max_waiters: int | None = None
    type_key_cache_max: int = 8192
    enable_conditional_providers: bool = True
    enable_plugins: bool = True
    strict_service_registration: bool = False

    # Precomputed for hot-path checks (avoids repeated string compares).
    _strict_scopes: bool = field(default=False, init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        self._validate()
        # frozen dataclass — bypass __setattr__ for the derived cache field.
        object.__setattr__(self, "_strict_scopes", self.scope_enforcement == "raise")

    # ── Validation ────────────────────────────────────────────────────

    def _validate(self) -> None:
        if self.scope_enforcement not in _VALID_SCOPE_ENFORCEMENT:
            raise DIConfigFault(
                "scope_enforcement",
                self.scope_enforcement,
                f"must be one of {sorted(_VALID_SCOPE_ENFORCEMENT)}",
            )
        if self.disposal_strategy not in _VALID_DISPOSAL:
            raise DIConfigFault(
                "disposal_strategy",
                self.disposal_strategy,
                f"must be one of {sorted(_VALID_DISPOSAL)}",
            )
        if self.hook_timeout_seconds <= 0:
            raise DIConfigFault("hook_timeout_seconds", self.hook_timeout_seconds, "must be > 0")
        if self.pool_acquire_timeout_seconds <= 0:
            raise DIConfigFault(
                "pool_acquire_timeout_seconds",
                self.pool_acquire_timeout_seconds,
                "must be > 0",
            )
        if self.pool_max_waiters is not None and self.pool_max_waiters < 1:
            raise DIConfigFault("pool_max_waiters", self.pool_max_waiters, "must be >= 1 or None")
        if self.type_key_cache_max < 1:
            raise DIConfigFault("type_key_cache_max", self.type_key_cache_max, "must be >= 1")

    # ── Derived accessors ─────────────────────────────────────────────

    @property
    def strict_scopes(self) -> bool:
        """Whether a scope violation raises (``scope_enforcement == "raise"``)."""
        return self._strict_scopes

    @property
    def scope_check_enabled(self) -> bool:
        """Whether the scope-validation check runs at all (not ``"off"``)."""
        return self.scope_enforcement != "off"

    # ── Construction from config ──────────────────────────────────────

    @classmethod
    def from_mapping(cls, data: Any) -> DISettings:
        """Build settings from a ``di`` config mapping (or ``None``).

        Unknown keys are ignored (forward-compatible); known keys are
        type-checked by the dataclass and validated by :meth:`_validate`.

        Args:
            data: A mapping (dict) from the ``di`` config section, an object
                exposing the same attributes, or ``None`` for defaults.

        Returns:
            A validated :class:`DISettings` instance.

        Raises:
            DIConfigFault: If any provided value is invalid.

        Example::

            loader = MyConfig.to_loader()
            settings = DISettings.from_mapping(loader.get_di_config())
        """
        if data is None:
            return cls()

        # Accept dict-like or attribute-bearing objects uniformly.
        def _get(key: str, default: Any) -> Any:
            if isinstance(data, dict):
                return data.get(key, default)
            return getattr(data, key, default)

        known = {f.name for f in fields(cls) if f.init}
        kwargs: dict[str, Any] = {}
        for name in known:
            sentinel = object()
            val = _get(name, sentinel)
            if val is not sentinel:
                kwargs[name] = val
        return cls(**kwargs)


# ── Process-global singleton ──────────────────────────────────────────

_active_settings: DISettings = DISettings()


def configure_di(settings: DISettings) -> None:
    """Install *settings* as the active DI configuration for this process.

    Called once during server boot (from the config's ``di`` section). Safe
    to call again to reconfigure — the last call wins. Also propagates the
    type-key cache bound to :mod:`aquilia.di.core`.

    Args:
        settings: The validated settings to activate.

    Example::

        from aquilia.di.settings import DISettings, configure_di

        configure_di(DISettings(parallel_resolution=True))
    """
    global _active_settings
    if not isinstance(settings, DISettings):
        raise DIConfigFault("settings", settings, "must be a DISettings instance")
    _active_settings = settings

    # Propagate the cache bound to the core module's module-level cap.
    from . import core as _core

    _core._TYPE_KEY_CACHE_MAX = settings.type_key_cache_max


def get_di_settings() -> DISettings:
    """Return the active :class:`DISettings` singleton.

    Returns the permissive default until :func:`configure_di` runs, so DI
    works out-of-the-box in tests and standalone scripts.

    Example::

        from aquilia.di.settings import get_di_settings

        settings = get_di_settings()
        if settings.parallel_resolution:
            ...
    """
    return _active_settings


def reset_di_settings() -> None:
    """Reset DI settings to defaults. Intended for test teardown."""
    global _active_settings
    _active_settings = DISettings()
