"""
Scope definitions and validation.
"""

import warnings
from dataclasses import dataclass
from enum import Enum
from typing import Literal

ServiceScopeLiteral = Literal["singleton", "app", "request", "transient", "pooled", "ephemeral"]


class ServiceScopeMeta(type(Enum)):
    def __getattribute__(cls, name):
        if name in ("SINGLETON", "APP", "REQUEST", "TRANSIENT", "POOLED", "EPHEMERAL"):
            warnings.warn(
                f"Using ServiceScope.{name} is deprecated. Use string literal '{name.lower()}' instead.",
                category=DeprecationWarning,
                stacklevel=2,
            )
        return super().__getattribute__(name)

    def __call__(cls, value, names=None, *args, **kwargs):
        if names is None:
            warnings.warn(
                "ServiceScope Enum is deprecated and will be removed in a future version. "
                "Use string literals (e.g. 'singleton', 'app') instead.",
                category=DeprecationWarning,
                stacklevel=2,
            )
        return super().__call__(value, names, *args, **kwargs)


class ServiceScope(str, Enum, metaclass=ServiceScopeMeta):
    """
    [DEPRECATED] Service lifetime scopes for dependency injection.
    Use string literals (e.g. "singleton", "app") instead.
    """

    SINGLETON = "singleton"  # One instance per app lifecycle
    APP = "app"  # One instance per app (alias for singleton)
    REQUEST = "request"  # One instance per request
    TRANSIENT = "transient"  # New instance every resolve
    POOLED = "pooled"  # Managed pool of instances
    EPHEMERAL = "ephemeral"  # Short-lived, request-scoped


@dataclass
class Scope:
    """Scope metadata and rules."""

    name: str
    cacheable: bool
    parent: str | None = None

    def can_inject_into(self, other: "Scope") -> bool:
        """
        Check if this scope can be injected into another scope.

        Rules:
        - Singleton/app can inject into anything
        - Request cannot inject into singleton/app (scope violation)
        - Transient can inject into anything
        - Ephemeral follows same rules as request
        """
        if self.name in ("singleton", "app", "transient", "pooled"):
            return True

        if self.name in ("request", "ephemeral"):
            # Cannot inject into longer-lived scopes
            return other.name not in ("singleton", "app")

        return True


# Predefined scopes
SCOPES = {
    "singleton": Scope(name="singleton", cacheable=True),
    "app": Scope(name="app", cacheable=True),
    "request": Scope(name="request", cacheable=True, parent="app"),
    "transient": Scope(name="transient", cacheable=False),
    "pooled": Scope(name="pooled", cacheable=False),
    "ephemeral": Scope(name="ephemeral", cacheable=True, parent="request"),
}


class ScopeValidator:
    """Validates scope rules and relationships."""

    @staticmethod
    def validate_injection(
        provider_scope: str,
        consumer_scope: str,
    ) -> bool:
        """
        Validate that provider scope can be injected into consumer scope.

        Args:
            provider_scope: Scope of the provider being injected
            consumer_scope: Scope of the consumer

        Returns:
            True if valid, False otherwise
        """
        provider = SCOPES.get(provider_scope)
        consumer = SCOPES.get(consumer_scope)

        if provider is None or consumer is None:
            return False

        return provider.can_inject_into(consumer)

    @staticmethod
    def get_scope_hierarchy() -> dict[str, list[str]]:
        """
        Get scope hierarchy for diagnostics.

        Returns:
            Dict mapping scope to its children
        """
        hierarchy = {}
        for name, scope in SCOPES.items():
            if scope.parent:
                hierarchy.setdefault(scope.parent, []).append(name)
            else:
                hierarchy.setdefault(name, [])
        return hierarchy
