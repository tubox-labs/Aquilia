"""
Aquilia Dependency Injection System

Production-grade, async-first DI with manifest awareness, multi-tenant safety,
and comprehensive observability.

Key Features:
- Explicit scopes: singleton, app, request, transient, pooled, ephemeral
- Manifest-aware registry with cross-app dependency enforcement
- Async lifecycle hooks with deterministic disposal
- Low-overhead hot path: <3µs cached lookups
- Cycle detection with safe lazy resolution
- OpenTelemetry tracing and metrics
- LSP integration via di_manifest.json
"""

from aquilia._version import __version__  # noqa: F401 — re-exported

# Legacy compatibility
from .compat import RequestCtx
from .core import (
    Container,
    Provider,
    ProviderMeta,
    Registry,
    ResolveCtx,
)
from .decorators import (
    Inject,
    auto_inject,
    factory,
    inject,
    provides,
    service,
)
from .dep import (
    Body,
    Dep,
    Header,
    Query,
)
from .errors import (
    AmbiguousProviderError,
    DependencyCycleError,
    DIError,
    ProviderNotFoundError,
    ScopeViolationError,
)
from .graph import (
    DependencyGraph,
)
from .lifecycle import (
    DisposalStrategy,
    Lifecycle,
    LifecycleContext,
    LifecycleHook,
)
from .providers import (
    AliasProvider,
    BlueprintProvider,
    ClassProvider,
    FactoryProvider,
    LazyProxyProvider,
    PoolProvider,
    ScopedProvider,
    ValueProvider,
)
from .request_dag import (
    RequestDAG,
)
from .scopes import (
    Scope,
    ScopeValidator,
    ServiceScope,
)
from .testing import (
    MockProvider,
    TestRegistry,
)

__all__ = [
    # Core types
    "Provider",
    "ProviderMeta",
    "Container",
    "Registry",
    "ResolveCtx",
    # Providers
    "ClassProvider",
    "FactoryProvider",
    "ValueProvider",
    "PoolProvider",
    "AliasProvider",
    "LazyProxyProvider",
    "ScopedProvider",
    "BlueprintProvider",
    # Scopes
    "Scope",
    "ServiceScope",
    "ScopeValidator",
    # Decorators
    "service",
    "factory",
    "inject",
    "Inject",
    "provides",
    "auto_inject",
    # Lifecycle
    "Lifecycle",
    "LifecycleHook",
    "DisposalStrategy",
    "LifecycleContext",
    # Graph
    "DependencyGraph",
    # Errors
    "DIError",
    "ProviderNotFoundError",
    "DependencyCycleError",
    "ScopeViolationError",
    "AmbiguousProviderError",
    # Testing
    "TestRegistry",
    "MockProvider",
    # Dep (annotation-driven DI)
    "Dep",
    "Header",
    "Query",
    "Body",
    "RequestDAG",
    # Legacy
    "RequestCtx",
]
