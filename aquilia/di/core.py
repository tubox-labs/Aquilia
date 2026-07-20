"""
Core DI types and protocols.

Defines the fundamental contracts for the DI system.
"""

import asyncio
import inspect
from collections.abc import Callable, Coroutine
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import (
    Any,
    Optional,
    Protocol,
    TypeVar,
    runtime_checkable,
)

# Use inspect.iscoroutinefunction (asyncio version deprecated in 3.16)
_is_coroutine = inspect.iscoroutinefunction

# Module-level cache: type → "module.qualname" string.
# Bounded to avoid unbounded growth in long-running processes that
# dynamically create classes (plugins, per-test throwaway types). When
# the cap is hit the cache is cleared wholesale — entries are cheap to
# recompute, so a periodic flush is preferable to per-entry LRU bookkeeping.
_TYPE_KEY_CACHE_MAX = 8192
_type_key_cache: dict[type, str] = {}


def _cache_type_key(token: type, key: str) -> None:
    """Insert into the bounded type-key cache, flushing if over cap."""
    if len(_type_key_cache) >= _TYPE_KEY_CACHE_MAX:
        _type_key_cache.clear()
    _type_key_cache[token] = key


# Sentinel for cache-miss distinction (allows caching None values)
_CACHE_SENTINEL = object()

# Sentinel for "Dep currently resolving" (cycle guard in Dep engine)
_DEP_RESOLVING = object()

# Per-task ancestor chain of Dep cache_keys currently being resolved, used to
# distinguish a TRUE cycle (a dep that appears in its own ancestor chain) from a
# benign diamond (two parallel siblings both awaiting the same shared sub-dep).
# contextvars are copied per asyncio task, so parallel gather() branches each
# see their own ancestor chain rather than a shared mutable set.
_dep_ancestors: "ContextVar[frozenset[str]]" = ContextVar("aquilia_dep_ancestors", default=frozenset())

# Per-task set of (container-id, cache_key) pairs currently instantiating, used
# to detect cycles that cross a container link boundary. The ResolveCtx stack is
# per-container and is intentionally reset when delegating across a dependency
# link (the linked container needs its own container binding), so it cannot see
# a cross-app cycle on its own — this task-local set bridges that gap.
_resolve_ancestors: "ContextVar[frozenset[tuple[int, str]]]" = ContextVar(
    "aquilia_resolve_ancestors", default=frozenset()
)

# Scopes that should cache instances (frozen for O(1) lookup)
_CACHEABLE_SCOPES = frozenset(("singleton", "app", "request"))


T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class ProviderMeta:
    """
    Compact, serializable provider metadata.

    Stored in di_manifest.json for LSP integration.
    """

    name: str
    token: str  # Type name or string key
    scope: str  # "singleton", "app", "request", "transient", "pooled", "ephemeral"
    tags: tuple[str, ...] = field(default_factory=tuple)
    module: str = ""
    qualname: str = ""
    line: int | None = None
    version: str | None = None
    allow_lazy: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Serialize for manifest JSON."""
        return {
            "name": self.name,
            "token": self.token,
            "scope": self.scope,
            "tags": list(self.tags),
            "module": self.module,
            "qualname": self.qualname,
            "line": self.line,
            "version": self.version,
            "allow_lazy": self.allow_lazy,
        }


class ResolveCtx:
    """
    Context for resolution operations.

    Tracks resolution stack for cycle detection and diagnostics.
    Uses __slots__ for minimal allocation overhead.
    """

    __slots__ = ("container", "stack", "cache")

    def __init__(self, container: "Container"):
        self.container = container
        self.stack: list[str] = []
        self.cache: dict[str, Any] = {}

    def push(self, token: str) -> None:
        """Push token onto resolution stack."""
        self.stack.append(token)

    def pop(self) -> None:
        """Pop token from resolution stack."""
        self.stack.pop()

    def in_cycle(self, token: str) -> bool:
        """Check if token is currently being resolved (cycle)."""
        return token in self.stack

    def get_trace(self) -> list[str]:
        """Get current resolution trace for error messages."""
        return self.stack.copy()


@runtime_checkable
class Provider(Protocol):
    """
    Provider protocol - how to instantiate a dependency.

    All providers must implement this interface.
    """

    @property
    def meta(self) -> ProviderMeta:
        """Provider metadata."""
        ...

    async def instantiate(self, ctx: ResolveCtx) -> Any:
        """
        Instantiate the provider.

        Args:
            ctx: Resolution context with container and stack

        Returns:
            The instantiated object
        """
        ...

    async def shutdown(self) -> None:
        """
        Shutdown hook for cleanup.

        Called in reverse order of instantiation.
        """
        ...


class Container:
    """
    DI Container - manages provider instances and scopes.

    Optimized for low-overhead hot path (<3µs cached lookups).
    """

    __slots__ = (
        "_providers",
        "_providers_owned",
        "_cache",
        "_scope",
        "_parent",
        "_finalizers",
        "_resolve_plans",
        "_diagnostics",
        "_lifecycle",
        "_shutdown_called",
        "_inflight",
        # Cross-app dependency links: sibling app containers this container may
        # resolve from, keyed by app name (wired from manifest ``depends_on``).
        "_dep_links",
        # ── Unified Dep() resolution state (request-local graph) ──
        "_dep_cache",
        "_dep_teardowns",
        "_dep_resolving",
        "_dep_inflight",
    )

    def __init__(
        self,
        scope: str = "app",
        parent: Optional["Container"] = None,
        diagnostics: Any | None = None,
    ):
        from .diagnostics import DIDiagnostics
        from .lifecycle import Lifecycle

        self._providers: dict[str, Provider] = {}  # {cache_key: provider}
        self._providers_owned: bool = True  # True when we own the dict (can mutate in-place)
        self._cache: dict[str, Any] = {}  # {cache_key: instance}
        self._scope = scope
        self._parent = parent
        self._finalizers: list[Callable[[], Coroutine]] = []  # LIFO cleanup
        self._resolve_plans: dict[str, list[str]] = {}  # Precomputed dependency lists
        self._diagnostics = diagnostics or DIDiagnostics()
        self._lifecycle = Lifecycle()
        self._shutdown_called = False
        # In-flight instantiations of cacheable providers, so concurrent
        # (parallel-resolution) resolvers of the same token share one instance
        # instead of each building their own. Lazily allocated.
        self._inflight: dict[str, asyncio.Future] | None = None
        # Cross-app links (lazy). {app_name: Container} that this container is
        # allowed to resolve from when a token is missing locally — the runtime
        # counterpart to manifest ``depends_on`` static validation.
        self._dep_links: dict[str, Container] | None = None
        # ── Dep() resolution graph (lazy — allocated on first Dep use) ──
        self._dep_cache: dict[str, Any] | None = None
        self._dep_teardowns: list | None = None
        self._dep_resolving: set[str] | None = None
        self._dep_inflight: dict[str, asyncio.Future] | None = None

    def _parent_has_key(self, key: str) -> bool:
        """Whether any ancestor container holds this provider key (shadowing check)."""
        p = self._parent
        while p is not None:
            if key in p._providers:
                return True
            p = p._parent
        return False

    def add_dependency_link(self, app_name: str, container: "Container") -> None:
        """Link a sibling app container this container may resolve from.

        The runtime counterpart to manifest ``depends_on``: static validation
        (:meth:`Registry._validate_cross_app_deps`) proves a cross-app edge is
        *declared*; this makes it actually *resolvable*. When a token is missing
        locally (and up the parent chain), resolution falls through to linked
        containers, so a service in app ``billing`` that declares
        ``depends_on=["auth"]`` can inject an ``auth``-owned provider.

        Resolution delegates to the owning container, so an app-scoped singleton
        is still instantiated and cached exactly once, in its owning app.

        Args:
            app_name: Name of the linked app (for diagnostics / dedup).
            container: The linked app's container.
        """
        if container is self:
            return
        if self._dep_links is None:
            self._dep_links = {}
        self._dep_links[app_name] = container

    def register(self, provider: Provider, tag: str | None = None):
        """
        Register a provider.

        Performance (v3 — copy-on-write):
        If this container shares its ``_providers`` dict with a parent
        (i.e. it was created via ``create_request_scope()``), the first
        call to ``register()`` copies the dict before mutating.
        Subsequent ``register()`` calls on the same container are O(1).

        Args:
            provider: Provider instance
            tag: Optional tag for disambiguation
        """
        meta = provider.meta
        token = meta.token
        key = self._make_cache_key(token, tag)

        # Duplicate check must distinguish a genuine local re-registration from
        # legitimate shadowing of a provider inherited from a parent container.
        # A key is a real duplicate only if it exists here AND is not present in
        # the parent chain (i.e. this container itself registered it). Shadowing
        # an inherited key is allowed. Works whether or not the shared dict has
        # been COW-forked yet.
        if key in self._providers and not self._parent_has_key(key):
            existing = self._providers[key]
            # Idempotency: if same provider, ignore. If different, error.
            if existing == provider:
                return
            from ..faults.domains import DIFault

            raise DIFault(
                code="PROVIDER_ALREADY_REGISTERED",
                message=f"Provider for {token} (tag={tag}) already registered: {existing.meta.name}",
                metadata={"token": str(token), "tag": tag, "existing": existing.meta.name},
            )

        # ── Copy-on-write: copy the shared dict before mutating ──
        if not self._providers_owned:
            self._providers = self._providers.copy()
            self._providers_owned = True

        self._providers[key] = provider

        # Emit diagnostic event
        from .diagnostics import DIEventType

        self._diagnostics.emit(DIEventType.REGISTRATION, token=token, tag=tag, provider_name=meta.name)

        # Plugin hook (fast-skip when no plugins registered — hot path).
        from .plugins import _notify_provider_registered, _plugins

        if _plugins:
            _notify_provider_registered(self, provider)

    def bind(self, interface: type, implementation: type, scope: str = "app", tag: str | None = None):
        """
        Bind an interface to an implementation class.

        Example:
            container.bind(UserRepository, SqlUserRepository)

        Args:
            interface: Abstract base class or protocol
            implementation: Concrete class
            scope: Lifecycle scope
            tag: Optional tag
        """
        from .providers import ClassProvider

        provider = ClassProvider(implementation, scope=scope)

        # Register under the INTERFACE token
        # Hack: mutate the token to match the interface, but keep the implementation logic
        # A cleaner way would be to wrap or use AliasProvider, but ClassProvider is flexible.
        token = self._token_to_key(interface)

        # We manually register it under the interface key
        key = self._make_cache_key(token, tag)

        # ── Copy-on-write: copy shared dict before mutating (SEC-DI-01) ──
        if not self._providers_owned:
            self._providers = self._providers.copy()
            self._providers_owned = True

        self._providers[key] = provider

        # Emit diagnostic event
        from .diagnostics import DIEventType

        self._diagnostics.emit(
            DIEventType.REGISTRATION,
            token=token,
            tag=tag,
            provider_name=provider.meta.name,
            metadata={"binding": "interface"},
        )

    async def register_instance(
        self,
        token: type[T] | str,
        instance: T,
        scope: str = "request",
        tag: str | None = None,
    ):
        """
        Register a pre-instantiated object as a provider.

        This is useful for registering request-scoped instances like Session
        that are created outside the DI system.

        Args:
            token: Type or string key
            instance: Pre-instantiated object
            scope: Scope for the instance (default: "request")
            tag: Optional tag for disambiguation

        Example:
            >>> session = await engine.resolve(request)
            >>> await container.register_instance(Session, session, scope="request")
        """
        from .providers import ValueProvider

        # Create a ValueProvider for the instance
        provider = ValueProvider(
            token=token,
            value=instance,
            scope=scope,
            name=f"{token.__name__ if hasattr(token, '__name__') else token}_instance",
        )

        # Per-request instances must always replace the previous one --
        # evict any existing provider/cache entry for this token so that
        # register() doesn't raise "already registered".
        token_key = self._token_to_key(token)
        cache_key = self._make_cache_key(token_key, tag)

        # ── Copy-on-write: copy shared dict before mutating (SEC-DI-01) ──
        if not self._providers_owned:
            self._providers = self._providers.copy()
            self._providers_owned = True

        self._providers.pop(cache_key, None)
        self._cache.pop(cache_key, None)

        # Register the provider
        self.register(provider, tag=tag)

    def resolve(
        self,
        token: type[T] | str,
        *,
        tag: str | None = None,
        optional: bool = False,
    ) -> T:
        """
        Resolve a dependency (hot path - optimized).

        Args:
            token: Type or string key
            tag: Optional tag for disambiguation
            optional: If True, return None if not found instead of raising

        Returns:
            The resolved instance

        Raises:
            ProviderNotFoundError: If provider not found and not optional
        """
        # Convert type to string key
        token_key = self._token_to_key(token)
        cache_key = self._make_cache_key(token_key, tag)

        # Fast path: check cache
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Lookup provider
        provider = self._lookup_provider(token_key, tag)

        if provider is None:
            if optional:
                return None
            self._raise_not_found(token_key, tag)

        # Sync bridge: drive the async path on a persistent per-thread loop
        # (Bug 8 — no throwaway loop per call). Raises if in a running loop.
        from ._sync_bridge import run_sync

        return run_sync(
            self.resolve_async(token, tag=tag, optional=optional),
            provider=str(token_key),
        )

    async def resolve_async(
        self,
        token: type[T] | str,
        *,
        tag: str | None = None,
        optional: bool = False,
        ctx: ResolveCtx | None = None,
    ) -> T:
        """
        Async resolve (primary resolution path).

        Performance (v3):
        - Inlined token_to_key for common cases (str pass-through, type cache).
        - Single dict.get on _cache for the fast path.
        - No method call overhead for the >99% cached-hit case.
        - _should_cache uses frozenset constant.
        """
        # ── Inline token_to_key for speed ──
        if isinstance(token, str):
            token_key = token
        elif isinstance(token, type):
            token_key = _type_key_cache.get(token)
            if token_key is None:
                token_key = f"{token.__module__}.{token.__qualname__}"
                _cache_type_key(token, token_key)
        else:
            token_key = str(token)

        # ── Inline _make_cache_key ──
        cache_key = f"{token_key}#{tag}" if tag else token_key

        # Fast path: check cache (no diagnostics overhead)
        cached = self._cache.get(cache_key, _CACHE_SENTINEL)
        if cached is not _CACHE_SENTINEL:
            return cached

        # Lookup provider
        provider = self._lookup_provider(token_key, tag)

        if provider is None:
            # Cross-app fallback: try linked (depends_on) app containers before
            # giving up. Each link owns its providers, so delegating there caches
            # app singletons in their owning app exactly once.
            if self._dep_links:
                linked = await self._resolve_from_links(token_key, cache_key, tag, ctx)
                if linked is not _CACHE_SENTINEL:
                    return linked
            if optional:
                return None
            self._raise_not_found(token_key, tag)

        # Scope Delegation: singleton/app → parent
        # Only delegate when the provider was inherited from the parent,
        # not when the child registered it locally.
        if self._parent and provider.meta.scope in ("singleton", "app"):
            parent_provider = self._parent._providers.get(cache_key)
            if parent_provider is provider:
                return await self._parent.resolve_async(token, tag=tag, optional=optional, ctx=ctx)

        # ── SEC-DI-04: Scope validation — detect captive dependency ──
        # Prevent request/ephemeral scoped providers from being cached
        # in singleton/app scoped containers (captive dependency).
        #
        # Enforcement policy comes from DISettings.scope_enforcement:
        #   "off"   → skip the check, "warn" → log, "raise" → ScopeViolationError.
        from .settings import get_di_settings

        _di_settings = get_di_settings()
        if _di_settings.scope_check_enabled:
            from .scopes import ScopeValidator

            if not ScopeValidator.validate_injection(provider.meta.scope, self._scope):
                if _di_settings.strict_scopes:
                    from .errors import ScopeViolationError

                    raise ScopeViolationError(
                        provider_token=provider.meta.token,
                        provider_scope=provider.meta.scope,
                        consumer_token=token_key,
                        consumer_scope=self._scope,
                    )
                import logging as _log

                _log.getLogger("aquilia.di").warning(
                    "Scope violation: %s-scoped provider '%s' resolved in %s-scoped "
                    "container. This may cause captive dependency issues.",
                    provider.meta.scope,
                    provider.meta.name,
                    self._scope,
                )

        # Create or reuse resolution context
        if ctx is None:
            ctx = ResolveCtx(container=self)
        if ctx.in_cycle(cache_key):
            from .errors import DependencyCycleError

            raise DependencyCycleError(cycle=ctx.get_trace() + [cache_key])
        ctx.push(cache_key)

        # Diagnostics: emit resolution start/success/failure only when enabled
        # (keeps the hot cache-hit path free of overhead — this is the miss path).
        _emit_diag = _di_settings.diagnostics_enabled
        if _emit_diag:
            import time as _time

            from .diagnostics import DIEventType as _DET

            _t0 = _time.monotonic()
            self._diagnostics.emit(_DET.RESOLUTION_START, token=token_key, tag=tag, provider_name=provider.meta.name)

        # ── Cross-link cycle guard ──
        # The ResolveCtx stack is per-container and is reset across dependency
        # links, so it cannot catch a cycle that spans two linked app containers
        # (A→B→A). This task-local set keys on (container id, cache_key) and
        # survives the link boundary, turning a would-be deadlock into a raise.
        _anc_key = (id(self), cache_key)
        _anc = _resolve_ancestors.get()
        if _anc_key in _anc:
            ctx.pop()
            from .errors import DependencyCycleError

            raise DependencyCycleError(cycle=[*(k for _, k in _anc), cache_key])
        _anc_token = _resolve_ancestors.set(_anc | {_anc_key})

        # ── In-flight dedup for cacheable scopes ──
        # Under parallel_resolution, two sibling branches can reach here for the
        # same uncached token before either caches. Without this guard each
        # builds its own instance, breaking the singleton/app/request guarantee.
        _cacheable = provider.meta.scope in _CACHEABLE_SCOPES
        if _cacheable:
            if self._inflight is None:
                self._inflight = {}
            existing = self._inflight.get(cache_key)
            if existing is not None:
                ctx.pop()
                _resolve_ancestors.reset(_anc_token)
                return await existing
            _loop = asyncio.get_event_loop()
            _fut: asyncio.Future = _loop.create_future()
            _fut.add_done_callback(lambda f: f.exception() if not f.cancelled() else None)
            self._inflight[cache_key] = _fut

        try:
            instance = await provider.instantiate(ctx)

            # Cache if appropriate for scope
            if _cacheable:
                self._cache[cache_key] = instance
                await self._check_lifecycle_hooks(instance, provider.meta.name)
                # Skip finalizer probing on lazy proxies: hasattr() would trip
                # __getattr__ and force eager (possibly in-loop-sync) resolution.
                from .providers import _LazyProxy

                if not isinstance(instance, _LazyProxy) and (
                    hasattr(instance, "__aexit__") or hasattr(instance, "shutdown")
                ):
                    self._register_finalizer(instance)
                if not _fut.done():
                    _fut.set_result(instance)

            if _emit_diag:
                self._diagnostics.emit(
                    _DET.RESOLUTION_SUCCESS,
                    token=token_key,
                    tag=tag,
                    provider_name=provider.meta.name,
                    duration=_time.monotonic() - _t0,
                )
            return instance
        except Exception as _exc:
            if _cacheable and not _fut.done():
                _fut.set_exception(_exc)
            if _emit_diag:
                self._diagnostics.emit(
                    _DET.RESOLUTION_FAILURE,
                    token=token_key,
                    tag=tag,
                    provider_name=provider.meta.name,
                    duration=_time.monotonic() - _t0,
                    error=_exc,
                )
            raise
        finally:
            if _cacheable and self._inflight is not None:
                self._inflight.pop(cache_key, None)
            _resolve_ancestors.reset(_anc_token)
            ctx.pop()

    async def _check_lifecycle_hooks(self, instance: Any, name: str) -> None:
        """Check and register lifecycle hooks for an instance."""
        # Skip lazy proxies -- they should not be introspected until resolved
        from .providers import _LazyProxy

        if isinstance(instance, _LazyProxy):
            return

        if hasattr(instance, "on_startup"):
            hook = instance.on_startup
            # Bind hook via default arg to avoid late-binding closure bug
            if _is_coroutine(hook):
                self._lifecycle.on_startup(hook, name=f"{name}.on_startup")
            else:
                self._lifecycle.on_startup(
                    lambda _h=hook: asyncio.to_thread(_h),
                    name=f"{name}.on_startup",
                )

        if hasattr(instance, "on_shutdown"):
            hook = instance.on_shutdown
            if _is_coroutine(hook):
                self._lifecycle.on_shutdown(hook, name=f"{name}.on_shutdown")
            else:
                self._lifecycle.on_shutdown(
                    lambda _h=hook: asyncio.to_thread(_h),
                    name=f"{name}.on_shutdown",
                )

    async def startup(self) -> None:
        """
        Run startup hooks for all registered providers.
        """
        from .diagnostics import DIEventType

        self._diagnostics.emit(DIEventType.LIFECYCLE_STARTUP, metadata={"scope": self._scope})
        await self._lifecycle.run_startup_hooks()

    def is_registered(self, token: type[T] | str, tag: str | None = None) -> bool:
        """Check if a provider is registered for the token."""
        token_key = self._token_to_key(token)
        return self._lookup_provider(token_key, tag) is not None

    def add_diagnostic_listener(self, listener: "DiagnosticListener") -> None:
        """Register a diagnostic listener on this container's event stream.

        Request-scoped child containers share their parent's ``DIDiagnostics``
        instance (see ``create_request_scope``), so registering once on an
        app-level container is sufficient to observe every request scoped
        beneath it.
        """
        self._diagnostics.add_listener(listener)

    def create_request_scope(self) -> "Container":
        """
        Create a request-scoped child container (very cheap).

        Performance (v3 — copy-on-write):
        - Providers dict is **shared by reference** (zero-copy).
          If the child calls ``register()``, it copies on first write.
        - No import of DIDiagnostics/Lifecycle at call time (cached).
        - Lifecycle is a lightweight NullLifecycle for request scope.
        - Shared diagnostics reference from parent.
        """
        child = Container.__new__(Container)
        child._providers = self._providers  # Share by ref (copy-on-write)
        child._providers_owned = False  # Mark as borrowed — copy on first register()
        child._cache = {}  # Fresh cache per request
        child._scope = "request"
        child._parent = self
        child._finalizers = []
        child._resolve_plans = self._resolve_plans  # Read-only, share by ref
        child._diagnostics = self._diagnostics  # Share parent diagnostics
        child._lifecycle = _NullLifecycle  # Singleton no-op lifecycle
        child._shutdown_called = False
        child._inflight = None
        child._dep_links = self._dep_links
        child._dep_cache = None
        child._dep_teardowns = None
        child._dep_resolving = None
        child._dep_inflight = None
        return child

    def create_child(self, scope: str = "app", *, own_lifecycle: bool = True) -> "Container":
        """Create a generic hierarchical child container.

        Unlike :meth:`create_request_scope` (which is specialised for the
        per-request hot path), this creates a general nested container in any
        scope — useful for isolated sub-scopes (e.g. per-tenant containers) or
        multi-level scope trees (``root → child → request``).

        Note: the shipped runtime does NOT nest app containers. Cross-app
        sharing uses explicit links (:meth:`add_dependency_link`), not nesting.
        See ``docs/design/di-cross-app-resolution.md``.

        The child shares its parent's provider dict copy-on-write: reads fall
        through to the parent, the first ``register()`` forks a private copy.
        Resolution of ``singleton``/``app`` providers inherited from the parent
        is delegated upward so singletons are cached once at their owning level.

        Args:
            scope: Lifecycle scope for the child (``"app"``, ``"request"``,
                ``"transient"``, ``"ephemeral"``, ...).
            own_lifecycle: If ``True`` (default) the child gets its own
                :class:`~aquilia.di.lifecycle.Lifecycle` (independent startup/
                shutdown hooks). If ``False`` it uses the no-op lifecycle —
                cheaper, appropriate for short-lived children.

        Returns:
            A new child :class:`Container` parented to ``self``.

        Example::

            root = Container(scope="app")
            tenant = root.create_child(scope="app")
            tenant.register(ClassProvider(TenantService, scope="app"))
        """
        from .lifecycle import Lifecycle

        child = Container.__new__(Container)
        child._providers = self._providers
        child._providers_owned = False
        child._cache = {}
        child._scope = scope
        child._parent = self
        child._finalizers = []
        child._resolve_plans = self._resolve_plans
        child._diagnostics = self._diagnostics
        child._lifecycle = Lifecycle() if own_lifecycle else _NullLifecycle
        child._shutdown_called = False
        child._inflight = None
        child._dep_links = self._dep_links
        child._dep_cache = None
        child._dep_teardowns = None
        child._dep_resolving = None
        child._dep_inflight = None
        return child

    async def replace_provider(
        self,
        token: type[T] | str,
        provider: Provider,
        *,
        tag: str | None = None,
    ) -> None:
        """Atomically replace a registered provider at runtime (prod-safe).

        Unlike :func:`~aquilia.di.testing.override_container` (a test-only
        context manager) this is a supported production API for hot-swapping an
        implementation — e.g. flipping a feature-flagged service, or swapping a
        degraded backend for a fallback without a restart.

        The swap is copy-on-write safe (forks a shared provider dict first) and
        evicts any cached instance so the next resolution builds from the new
        provider. In-flight holders of the old instance are unaffected.

        Args:
            token: The token whose provider to replace.
            provider: The new provider to install under ``token``.
            tag: Optional tag disambiguator.

        Example::

            await container.replace_provider(PaymentGateway, ValueProvider(
                value=FallbackGateway(), token=PaymentGateway, scope="app",
            ))
        """
        token_key = self._token_to_key(token)
        cache_key = self._make_cache_key(token_key, tag)

        # COW: fork the shared dict before mutating (SEC-DI-01).
        if not self._providers_owned:
            self._providers = self._providers.copy()
            self._providers_owned = True

        self._providers[cache_key] = provider
        self._cache.pop(cache_key, None)

        from .diagnostics import DIEventType

        self._diagnostics.emit(
            DIEventType.REGISTRATION,
            token=token_key,
            tag=tag,
            provider_name=provider.meta.name,
            metadata={"replacement": True},
        )

    async def shutdown(self) -> None:
        """
        Shutdown container - run lifecycle hooks and finalizers in LIFO order.

        Performance (v2): Short-circuit for empty request-scoped containers.
        Idempotency (A-1): Guard against double-shutdown via _shutdown_called flag.
        """
        # A-1: Idempotency guard — prevent double-shutdown corruption
        if getattr(self, "_shutdown_called", False):
            return
        self._shutdown_called = True

        # Fast path: request scope with nothing to clean up
        if self._scope == "request" and not self._finalizers and not self._cache and not self._dep_teardowns:
            return

        from .diagnostics import DIEventType

        self._diagnostics.emit(DIEventType.LIFECYCLE_SHUTDOWN, metadata={"scope": self._scope})

        # Run Dep() generator teardowns (LIFO) before container finalizers
        await self._run_dep_teardowns()

        # Run lifecycle shutdown hooks
        await self._lifecycle.run_shutdown_hooks()
        await self._lifecycle.run_finalizers()

        # Compatibility with existing finalizers
        for finalizer in reversed(self._finalizers):
            try:
                await finalizer()
            except Exception as e:
                import logging as _log

                _log.getLogger("aquilia.di").warning(f"Error during finalizer: {e}")

        self._finalizers.clear()
        self._cache.clear()
        self._lifecycle.clear()
        self._dep_cache = None
        self._dep_resolving = None
        self._dep_inflight = None

    # ══════════════════════════════════════════════════════════════════
    # Unified Dep() resolution engine
    #
    # Folds the former RequestDAG into the container: one resolution
    # engine for the whole framework. Provides sub-dependency dedup,
    # parallel independent-branch resolution, and generator teardown —
    # all keyed to this (request-scoped) container's lifetime.
    # ══════════════════════════════════════════════════════════════════

    async def resolve_dep(self, dep: Any, param_type: type, request: Any = None) -> Any:
        """Resolve a ``Dep(...)`` descriptor against this container.

        Sub-dependencies are deduplicated in a request-local cache,
        independent branches resolve in parallel, and generator
        dependencies register teardown that runs at ``shutdown()``.

        Args:
            dep:        The ``Dep(...)`` descriptor.
            param_type: Base type from ``Annotated[T, Dep(...)]``.
            request:    Current request for Header/Query/Body extraction.

        Returns:
            The resolved dependency value.
        """
        # Bare Dep() — resolve by type from the container.
        if dep.is_container_lookup:
            return await self._resolve_from_container(param_type, dep.tag)

        cache_key = dep.cache_key

        if not dep.cached:
            # Uncached: always invoke fresh, no dedup, no cycle bookkeeping
            # beyond the ancestor chain check below.
            return await self._invoke_dep_guarded(dep, cache_key, param_type, request)

        if self._dep_cache is None:
            self._dep_cache = {}
            self._dep_resolving = set()
            self._dep_inflight = {}

        # 1. Fully-resolved result already cached → return it.
        if cache_key in self._dep_cache:
            return self._dep_cache[cache_key]

        # 2. True-cycle guard FIRST: if this dep is already in THIS task's
        #    ancestor chain, it depends on itself → real circular dependency.
        #    Must precede the in-flight check: for a genuine cycle the dep is
        #    both in-flight AND an ancestor, and awaiting its own Future would
        #    deadlock instead of raising.
        ancestors = _dep_ancestors.get()
        if cache_key in ancestors:
            from ..faults.domains import DIResolutionFault

            raise DIResolutionFault(
                provider=str(dep.call.__qualname__ if dep.call else param_type),
                reason="Circular dependency detected in Dep() resolution",
            )

        # 3. In-flight: another PARALLEL branch (not an ancestor) is already
        #    resolving this exact dep. A benign diamond (sibling sharing a
        #    sub-dep) awaits the same result rather than recomputing.
        inflight = self._dep_inflight.get(cache_key)
        if inflight is not None:
            return await inflight

        # Create the shared in-flight Future so concurrent siblings dedup onto it.
        loop = asyncio.get_event_loop()
        fut: asyncio.Future = loop.create_future()
        # Consume the future's exception even if no sibling awaited it, to avoid
        # "Future exception was never retrieved" noise when this is the only path.
        fut.add_done_callback(lambda f: f.exception() if not f.cancelled() else None)
        self._dep_inflight[cache_key] = fut
        token = _dep_ancestors.set(ancestors | {cache_key})
        try:
            result = await self._invoke_dep(dep, request)
            self._dep_cache[cache_key] = result
            if not fut.done():
                fut.set_result(result)
            return result
        except Exception as exc:
            if not fut.done():
                fut.set_exception(exc)
            raise
        finally:
            _dep_ancestors.reset(token)
            self._dep_inflight.pop(cache_key, None)

    async def _invoke_dep_guarded(self, dep: Any, cache_key: str, param_type: type, request: Any) -> Any:
        """Invoke an uncached dep with only ancestor-based cycle detection."""
        ancestors = _dep_ancestors.get()
        if cache_key in ancestors:
            from ..faults.domains import DIResolutionFault

            raise DIResolutionFault(
                provider=str(dep.call.__qualname__ if dep.call else param_type),
                reason="Circular dependency detected in Dep() resolution",
            )
        token = _dep_ancestors.set(ancestors | {cache_key})
        try:
            return await self._invoke_dep(dep, request)
        finally:
            _dep_ancestors.reset(token)

    async def _invoke_dep(self, dep: Any, request: Any) -> Any:
        """Invoke a Dep callable after resolving its sub-dependencies."""
        assert dep.call is not None

        sub_deps = dep.get_sub_dependencies()
        kwargs = await self._resolve_sub_deps(sub_deps, request)

        if dep.is_generator:
            return await self._invoke_dep_generator(dep, kwargs)
        elif dep.is_async:
            return await dep.call(**kwargs)
        else:
            result = dep.call(**kwargs)
            if inspect.isawaitable(result):
                return await result
            return result

    async def _resolve_sub_deps(self, sub_deps: dict[str, tuple], request: Any) -> dict[str, Any]:
        """Resolve sub-dependencies, parallelising independent branches."""
        if not sub_deps:
            return {}

        coros = {
            pname: self._resolve_single_dep(pname, ptype, sub_dep, request)
            for pname, (ptype, sub_dep) in sub_deps.items()
        }

        if len(coros) == 1:
            key = next(iter(coros))
            return {key: await coros[key]}

        keys = list(coros.keys())
        results = await asyncio.gather(*(coros[k] for k in keys))
        return dict(zip(keys, results, strict=False))

    async def _resolve_single_dep(self, pname: str, ptype: type, sub_dep: Any, request: Any) -> Any:
        """Resolve a single sub-dependency parameter."""
        from .dep import Body, Cookie, Dep, Header, Path, Query, _unpack_annotation
        from .request_dag import _get_base_type, _is_contract_type

        if request is not None and isinstance(sub_dep, (Query, Header, Body, Cookie, Path)):
            return await self._resolve_extracted_parameter(pname, ptype, sub_dep, request)

        if isinstance(sub_dep, Dep):
            base_type, _ = _unpack_annotation(ptype)
            return await self.resolve_dep(sub_dep, base_type, request)

        base_type = _get_base_type(ptype)
        if _is_contract_type(base_type):
            from aquilia.contracts.integration import bind_contract_to_request

            bp = await bind_contract_to_request(base_type, request)
            if hasattr(bp, "is_sealed_async"):
                await bp.is_sealed_async(raise_fault=True)
            else:
                bp.is_sealed(raise_fault=True)
            return bp

        return await self._resolve_from_container(ptype, tag=None)

    async def _resolve_extracted_parameter(self, pname: str, ptype: type, sub_dep: Any, request: Any) -> Any:
        """Resolve a Header/Query/Body/Cookie/Path extractor parameter."""
        from .dep import Body
        from .request_dag import _get_base_type, _is_contract_type

        base_type = _get_base_type(ptype)
        if _is_contract_type(base_type):
            from aquilia.contracts.integration import bind_contract_to_request

            bp = await bind_contract_to_request(base_type, request)
            if hasattr(bp, "is_sealed_async"):
                await bp.is_sealed_async(raise_fault=True)
            else:
                bp.is_sealed(raise_fault=True)
            return bp

        body = None
        if isinstance(sub_dep, Body) or sub_dep is None:
            body = await self._extract_body_value(request)
        return _resolve_extracted_parameter_sync(request, pname, ptype, sub_dep, body=body)

    async def _invoke_dep_generator(self, dep: Any, kwargs: dict[str, Any]) -> Any:
        """Invoke a generator Dep and register its teardown."""
        if self._dep_teardowns is None:
            self._dep_teardowns = []

        if inspect.isasyncgenfunction(dep.call):
            gen = dep.call(**kwargs)
            value = await gen.__anext__()
            self._dep_teardowns.append(gen)
            return value
        elif inspect.isgeneratorfunction(dep.call):
            gen = dep.call(**kwargs)
            value = next(gen)
            self._dep_teardowns.append(gen)
            return value
        else:
            from ..faults.domains import DIResolutionFault

            raise DIResolutionFault(
                provider=repr(dep.call),
                reason="Dependency call is not a generator function",
            )

    async def _resolve_from_container(self, param_type: type, tag: str | None) -> Any:
        """Resolve from this container by type, with qualified-name fallback."""
        try:
            return await self.resolve_async(param_type, tag=tag, optional=False)
        except Exception:
            if isinstance(param_type, type):
                key = f"{param_type.__module__}.{param_type.__qualname__}"
                try:
                    return await self.resolve_async(key, tag=tag, optional=False)
                except Exception:
                    pass
            raise

    async def _extract_body_value(self, request: Any) -> Any:
        """Extract JSON/form body from the request."""
        if request is None:
            return {}
        try:
            return await request.json()
        except Exception:
            try:
                return await request.form()
            except Exception:
                return {}

    async def _run_dep_teardowns(self) -> None:
        """Run generator teardowns in LIFO order (called from shutdown)."""
        if not self._dep_teardowns:
            return
        import contextlib as _ctxlib

        for gen in reversed(self._dep_teardowns):
            try:
                if inspect.isasyncgen(gen):
                    with _ctxlib.suppress(StopAsyncIteration):
                        await gen.__anext__()
                elif inspect.isgenerator(gen):
                    with _ctxlib.suppress(StopIteration):
                        next(gen)
            except Exception as exc:
                import logging as _log

                _log.getLogger("aquilia.di.dag").warning(f"Error during Dep teardown: {exc}")
        self._dep_teardowns = None

    def _token_to_key(self, token: type | str) -> str:
        """Convert type or string to cache key.

        Performance: type→key results are cached in a module-level dict
        to avoid repeated f-string formatting (~0.12µs → ~0.04µs).
        """
        if isinstance(token, str):
            return token

        if isinstance(token, type):
            key = _type_key_cache.get(token)
            if key is None:
                key = f"{token.__module__}.{token.__qualname__}"
                _cache_type_key(token, key)
            return key

        # Handle typing generics
        return str(token)

    def _make_cache_key(self, token: str, tag: str | None) -> str:
        """Create cache key from token and tag."""
        if tag:
            return f"{token}#{tag}"
        return token

    def _lookup_provider(
        self,
        token: str,
        tag: str | None,
    ) -> Provider | None:
        """
        Lookup provider in current container or parent.

        Returns:
            Provider or None if not found
        """
        # Check current container
        key = self._make_cache_key(token, tag)
        if key in self._providers:
            return self._providers[key]

        # Check parent
        if self._parent:
            return self._parent._lookup_provider(token, tag)

        return None

    async def _resolve_from_links(
        self,
        token_key: str,
        cache_key: str,
        tag: str | None,
        ctx: "ResolveCtx | None",
    ) -> Any:
        """Resolve a token from a linked (depends_on) app container.

        Delegates to the first linked container that actually owns the token so
        its provider instantiates and caches in its owning app. Returns
        :data:`_CACHE_SENTINEL` when no link can satisfy the token.

        A per-resolution visited set (threaded on ``ctx``) prevents an A↔B link
        cycle from recursing forever — a linked container that can't resolve the
        token simply reports miss.
        """
        # Track visited containers across the whole resolution to break link cycles.
        visited: set[int]
        if ctx is not None and getattr(ctx, "cache", None) is not None:
            visited = ctx.cache.setdefault("__link_visited__", set())
        else:
            visited = set()
        visited.add(id(self))

        for linked in self._dep_links.values():
            if id(linked) in visited:
                continue
            # Only delegate if the link (or its parent chain) actually owns it,
            # so we don't trigger a not-found raise in the linked container.
            if linked._lookup_provider(token_key, tag) is not None:
                visited.add(id(linked))
                return await linked.resolve_async(token_key, tag=tag, optional=False, ctx=None)
        return _CACHE_SENTINEL

    def _should_cache(self, scope: str) -> bool:
        """Check if scope should cache instances."""
        return scope in _CACHEABLE_SCOPES

    def _register_finalizer(self, instance: Any) -> None:
        """Register finalizer for cleanup."""
        if hasattr(instance, "__aexit__"):
            self._finalizers.append(lambda: instance.__aexit__(None, None, None))
        elif hasattr(instance, "shutdown"):
            self._finalizers.append(instance.shutdown)

    def _raise_not_found(self, token: str, tag: str | None) -> None:
        """Raise ProviderNotFoundError with helpful diagnostics."""
        from .errors import ProviderNotFoundError

        # Find similar providers
        candidates = []
        for key, _provider in self._providers.items():
            if token in key:
                candidates.append(key)

        raise ProviderNotFoundError(
            token=token,
            tag=tag,
            candidates=candidates,
        )


class Registry:
    """
    Registry - builds and validates provider graph from manifests.

    Performs static analysis, cycle detection, and generates manifest JSON.
    """

    def __init__(self, config: Any | None = None):
        self.config = config
        self._providers: list[Provider] = []
        self._graph: dict[str, list[str]] = {}  # {provider: [dependencies]}

    @classmethod
    def from_manifests(
        cls,
        manifests: list[Any],
        config: Any | None = None,
        *,
        enforce_cross_app: bool = True,
    ) -> "Registry":
        """
        Build registry from manifests.

        Args:
            manifests: List of AppManifest instances
            config: Optional config object
            enforce_cross_app: If True, enforce depends_on rules

        Returns:
            Validated registry
        """
        registry = cls(config=config)

        # Phase 1: Load provider metadata (no imports yet)
        for manifest in manifests:
            registry._load_manifest_services(manifest)

        # Phase 1b: Plugin hook — contribute/mutate providers before graph build
        # (honoured only when DISettings.enable_plugins is on).
        from .plugins import run_registry_build

        run_registry_build(registry)

        # Phase 2: Build dependency graph
        registry._build_dependency_graph()

        # Phase 3: Detect cycles
        registry._detect_cycles()

        # Phase 4: Validate cross-app dependencies
        if enforce_cross_app:
            registry._validate_cross_app_deps(manifests)

        return registry

    def add_provider(self, provider: Provider) -> None:
        """Append a provider to the registry (plugin-facing API).

        Intended for use from :meth:`aquilia.di.plugins.DIPlugin.on_registry_build`
        to contribute providers before the dependency graph is built.

        Args:
            provider: The provider to add.

        Example::

            def on_registry_build(self, registry):
                registry.add_provider(ClassProvider(AuditLogger, scope="app"))
        """
        self._providers.append(provider)

    def build_container(self) -> Container:
        """
        Build container from registry.

        Returns:
            Configured container
        """
        container = Container(scope="app")

        for provider in self._providers:
            # Extract tag from metadata if present
            tag = provider.meta.tags[0] if provider.meta.tags else None
            container.register(provider, tag=tag)

        return container

    def _load_manifest_services(self, manifest: Any) -> None:
        """Load services from manifest (phase 1)."""
        if not hasattr(manifest, "services") or not manifest.services:
            return

        import importlib
        import logging as _log
        import re as _re

        from .providers import ClassProvider

        _logger = _log.getLogger("aquilia.di")

        # ── Security: restrict importable module paths ──────────────────
        # Only allow dotted Python identifiers (no path traversal, no dunders).
        _SAFE_MODULE_RE = _re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)*$")
        _SAFE_CLASS_RE = _re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")
        # Block known dangerous top-level modules from being loaded via manifest.
        _BLOCKED_MODULES = frozenset(
            {
                "os",
                "sys",
                "subprocess",
                "shutil",
                "importlib",
                "ctypes",
                "pickle",
                "shelve",
                "code",
                "codeop",
                "compile",
                "compileall",
                "builtins",
                "__builtin__",
                "runpy",
                "pty",
                "commands",
            }
        )

        for service_entry in manifest.services:
            # Handle both string format and dict format
            if isinstance(service_entry, str):
                # Format: "module.path:ClassName"
                service_str = service_entry
                scope = "singleton"  # Default scope
                tag = None
            elif isinstance(service_entry, dict):
                # Format: {"class": "module.path:ClassName", "scope": "singleton", "tag": "..."}
                service_str = service_entry.get("class")
                scope = service_entry.get("scope", "singleton")
                tag = service_entry.get("tag")
            else:
                continue

            if not service_str or ":" not in service_str:
                continue

            # Parse module path and class name
            module_path, class_name = service_str.rsplit(":", 1)

            # ── Validate module path & class name ───────────────────────
            if not _SAFE_MODULE_RE.match(module_path):
                _logger.warning("Rejected service %r: module path contains illegal characters.", service_str)
                continue

            if not _SAFE_CLASS_RE.match(class_name):
                _logger.warning("Rejected service %r: class name contains illegal characters.", service_str)
                continue

            # Check top-level module against blocklist
            top_module = module_path.split(".")[0]
            if top_module in _BLOCKED_MODULES:
                _logger.warning(
                    "Rejected service %r: top-level module %r is blocked for security.",
                    service_str,
                    top_module,
                )
                continue

            # Reject dunder class names (e.g. __import__)
            if class_name.startswith("__") and class_name.endswith("__"):
                _logger.warning("Rejected service %r: dunder class names are not allowed.", service_str)
                continue

            try:
                # Import module
                module = importlib.import_module(module_path)

                # Get class
                service_class = getattr(module, class_name)

                # Verify it's actually a class, not a function/module/arbitrary object
                if not isinstance(service_class, type):
                    _logger.warning("Rejected service %r: resolved object is not a class.", service_str)
                    continue

                # Manifest-declared tag takes precedence; fall back to a
                # tag set by the @service(tag=...) decorator on the class.
                resolved_tag = tag or getattr(service_class, "__di_tag__", None)

                # Create provider
                provider = ClassProvider(
                    cls=service_class,
                    scope=scope,
                    tags=(resolved_tag,) if resolved_tag else (),
                )

                # Add to registry
                self._providers.append(provider)

            except (ImportError, AttributeError) as e:
                # Log error but continue
                _logger.warning(f"Could not load service {service_str}: {e}")

    def _build_dependency_graph(self) -> None:
        """
        Build dependency graph from registered providers (phase 2).

        Extracts dependencies from ClassProvider constructors and builds
        the dependency graph for analysis.

        Raises:
            MissingDependencyError: If a required dependency is not registered
        """
        import inspect

        from .errors import MissingDependencyError
        from .graph import DependencyGraph

        # Create dependency graph
        self._dep_graph = DependencyGraph()

        # Add all providers to graph
        for provider in self._providers:
            dependencies = []

            # Extract dependencies from ClassProvider
            if hasattr(provider, "cls"):
                try:
                    # Get constructor signature
                    sig = inspect.signature(provider.cls.__init__)

                    for param_name, param in sig.parameters.items():
                        if param_name == "self":
                            continue

                        # Get type annotation
                        if param.annotation != inspect.Parameter.empty:
                            # Handle Optional types
                            param_type = param.annotation

                            # Skip if Optional (not required)
                            origin = getattr(param_type, "__origin__", None)
                            if origin is not None:
                                # Handle Union types (Optional is Union[T, None])
                                import typing

                                if origin is typing.Union:
                                    args = getattr(param_type, "__args__", ())
                                    # If None in args, it's optional
                                    if type(None) in args:
                                        continue
                                    # Otherwise use first non-None type
                                    param_type = next((a for a in args if a is not type(None)), param_type)

                            # Get token from type
                            if hasattr(param_type, "__module__") and hasattr(param_type, "__name__"):
                                dep_token = f"{param_type.__module__}.{param_type.__name__}"
                                dependencies.append(dep_token)

                        # If no annotation but has default, skip (optional)
                        elif param.default != inspect.Parameter.empty:
                            continue

                except Exception as e:
                    # Log warning but continue
                    import logging as _log

                    _log.getLogger("aquilia.di").warning(
                        f"Could not extract dependencies from {provider.meta.token}: {e}"
                    )

            # Add to graph
            self._dep_graph.add_provider(provider, dependencies)
            self._graph[provider.meta.token] = dependencies

        # Validate all dependencies exist
        missing = []
        for token, deps in self._graph.items():
            for dep in deps:
                if not any(p.meta.token == dep for p in self._providers):
                    missing.append((token, dep))

        if missing:
            # Report first missing dependency
            service_token, dep_token = missing[0]
            provider = next((p for p in self._providers if p.meta.token == service_token), None)
            location = None
            if provider and provider.meta.module and provider.meta.line:
                location = (provider.meta.module, provider.meta.line)

            raise MissingDependencyError(
                service_token=service_token,
                dependency_token=dep_token,
                service_location=location,
            )

    def _detect_cycles(self) -> None:
        """
        Detect cycles using Tarjan's algorithm (phase 3).

        Uses the DependencyGraph's Tarjan implementation to find
        strongly connected components (cycles).

        Raises:
            CircularDependencyError: If circular dependencies detected
        """
        from .errors import CircularDependencyError

        if not hasattr(self, "_dep_graph"):
            # Graph not built yet
            return

        # Detect cycles using Tarjan's algorithm
        cycles = self._dep_graph.detect_cycles()

        if cycles:
            # Collect location information for error reporting
            locations = {}
            for cycle in cycles:
                for token in cycle:
                    provider = next((p for p in self._providers if p.meta.token == token), None)
                    if provider and provider.meta.module and provider.meta.line:
                        locations[token] = (provider.meta.module, provider.meta.line)

            raise CircularDependencyError(cycles=cycles, locations=locations)

    def _validate_cross_app_deps(self, manifests: list[Any]) -> None:
        """
        Validate cross-app dependencies (phase 4).

        Ensures that:
        1. Cross-app dependencies are declared in manifest depends_on
        2. No circular app dependencies
        3. Dependency load order is correct

        Args:
            manifests: List of AppManifest instances

        Raises:
            CrossAppDependencyError: If cross-app dependency rules violated
        """
        from .errors import CrossAppDependencyError

        # Build app -> services mapping
        app_services: dict[str, list[str]] = {}
        for manifest in manifests:
            app_name = getattr(manifest, "name", "unknown")
            services = []

            if hasattr(manifest, "services"):
                for service_entry in manifest.services:
                    if isinstance(service_entry, str):
                        service_str = service_entry
                    elif isinstance(service_entry, dict):
                        service_str = service_entry.get("class", "")
                    else:
                        continue

                    if ":" in service_str:
                        # Convert to token format
                        module_path, class_name = service_str.rsplit(":", 1)
                        token = f"{module_path}.{class_name}"
                        services.append(token)

            app_services[app_name] = services

        # Build app dependencies from manifest
        app_depends_on: dict[str, list[str]] = {}
        for manifest in manifests:
            app_name = getattr(manifest, "name", "unknown")
            depends_on = getattr(manifest, "depends_on", [])
            app_depends_on[app_name] = depends_on

        # Check each service's dependencies
        for manifest in manifests:
            consumer_app = getattr(manifest, "name", "unknown")
            consumer_services = app_services.get(consumer_app, [])

            for service_token in consumer_services:
                # Get dependencies of this service
                deps = self._graph.get(service_token, [])

                for dep_token in deps:
                    # Find which app provides this dependency
                    provider_app = None
                    for app, services in app_services.items():
                        if dep_token in services:
                            provider_app = app
                            break

                    # If dependency is from another app, check if declared
                    if provider_app and provider_app != consumer_app:
                        if provider_app not in app_depends_on.get(consumer_app, []):
                            raise CrossAppDependencyError(
                                consumer_app=consumer_app,
                                provider_app=provider_app,
                                provider_token=dep_token,
                            )


# ── Lightweight null lifecycle for request-scoped containers ──


class _NullLifecycleType:
    """No-op lifecycle singleton -- avoids allocating a real Lifecycle
    per request container."""

    __slots__ = ()

    async def run_startup_hooks(self):
        pass

    async def run_shutdown_hooks(self):
        pass

    async def run_finalizers(self):
        pass

    def on_startup(self, *a, **kw):
        pass

    def on_shutdown(self, *a, **kw):
        pass

    def clear(self):
        pass


_NullLifecycle = _NullLifecycleType()


def _resolve_extracted_parameter_sync(request: Any, pname: str, ptype: type, sub_dep: Any, body: Any = None) -> Any:
    """Cast + validate an extracted request parameter via the Facet pipeline.

    Shared by the container's Dep engine and RequestDAG shim.
    """
    from aquilia.contracts.annotations import _build_facet_from_annotation
    from aquilia.contracts.exceptions import CastFault
    from aquilia.contracts.facets import UNSET
    from aquilia.contracts.integration import extract_value_from_request
    from aquilia.faults.domains import BadRequestFault

    facet = _build_facet_from_annotation(
        name=pname,
        annotation=ptype,
        field_spec=None,
        class_default=UNSET,
    )

    raw_val = extract_value_from_request(request, pname, sub_dep, facet, body)

    if raw_val is UNSET:
        if getattr(sub_dep, "default", None) not in (None, ...):
            raw_val = sub_dep.default
        elif facet.default is not UNSET:
            raw_val = facet.default() if callable(facet.default) else facet.default
        elif getattr(sub_dep, "required", False) or facet.required:
            raise BadRequestFault(
                message=f"Missing required parameter: {pname}",
                detail=f"Missing required parameter: {pname}",
            )
        else:
            raw_val = None

    if raw_val is None:
        if facet.allow_null:
            return None
        raise BadRequestFault(
            message=f"Parameter '{pname}' may not be null",
            detail=f"Parameter '{pname}' may not be null",
        )

    try:
        cast_val = facet.cast(raw_val)
        return facet.seal(cast_val)
    except CastFault as exc:
        raise BadRequestFault(
            message=f"Invalid value for parameter '{pname}': {exc}",
            detail=f"Invalid value for parameter '{pname}': {exc}",
        )
