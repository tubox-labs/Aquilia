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
from aquilia.di.compat import (
    RequestCtx,
    get_request_container,
    request_container_scope,
    reset_request_container,
    set_request_container,
)
from aquilia.di.core import Container, Provider, ProviderMeta, Registry, ResolveCtx
from aquilia.di.decorators import (
    ConditionContext,
    Inject,
    auto_inject,
    conditional,
    factory,
    inject,
    provides,
    service,
    should_register,
)
from aquilia.di.dep import Body, Cookie, Dep, Header, Path, Query
from aquilia.di.errors import (
    AmbiguousProviderError,
    DependencyCycleError,
    DIError,
    ProviderNotFoundError,
    ScopeViolationError,
)
from aquilia.di.graph import DependencyGraph
from aquilia.di.interceptors import InterceptContext, InterceptingProvider, ProviderInterceptor, intercept
from aquilia.di.lifecycle import DisposalStrategy, Lifecycle, LifecycleContext, LifecycleHook
from aquilia.di.plugins import DIPlugin, clear_plugins, get_plugins, register_plugin, unregister_plugin
from aquilia.di.providers import (
    AliasProvider,
    ClassProvider,
    ContractProvider,
    FactoryProvider,
    LazyProxyProvider,
    PoolProvider,
    ScopedProvider,
    ValueProvider,
)
from aquilia.di.request_dag import RequestDAG
from aquilia.di.scopes import Scope, ScopeValidator, ServiceScope, ServiceScopeLiteral
from aquilia.di.settings import DIConfigFault, DISettings, configure_di, get_di_settings, reset_di_settings
from aquilia.di.testing import MockProvider, TestRegistry

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
    "ContractProvider",
    # Scopes
    "Scope",
    "ServiceScope",
    "ServiceScopeLiteral",
    "ScopeValidator",
    # Decorators
    "service",
    "factory",
    "inject",
    "Inject",
    "provides",
    "auto_inject",
    "conditional",
    "ConditionContext",
    "should_register",
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
    # Settings
    "DISettings",
    "DIConfigFault",
    "configure_di",
    "get_di_settings",
    "reset_di_settings",
    # Interceptors (provider-level AOP)
    "ProviderInterceptor",
    "InterceptingProvider",
    "InterceptContext",
    "intercept",
    # Plugins
    "DIPlugin",
    "register_plugin",
    "unregister_plugin",
    "get_plugins",
    "clear_plugins",
    # Testing
    "TestRegistry",
    "MockProvider",
    # Dep (annotation-driven DI)
    "Dep",
    "Header",
    "Query",
    "Cookie",
    "Path",
    "Body",
    "RequestDAG",
    # Legacy
    "RequestCtx",
    "get_request_container",
    "set_request_container",
    "reset_request_container",
    "request_container_scope",
]
