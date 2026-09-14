"""
AquilAuth — Strategy Registry

Passport-style named-strategy registry for authentication backends.

The registry decouples *naming* strategies in configuration (``backends =
["token", "session", "google"]``) from *constructing* them (which dependencies
they need, where the class lives). Applications and plugins register custom
strategies once and reference them by name everywhere — config, manifests,
middleware — exactly like NestJS/Passport's ``PassportStrategy('jwt')``.

Built-in names (always registered):

===================  ==================================================
``"token"`` /        Bearer JWT verification **with** per-request identity
``"jwt"``            resolution through the identity store.
``"jwt-stateless"``  Bearer JWT verification that builds the principal
                     from verified claims — no identity lookup per request
                     (the passport-jwt default posture).
``"session"``        Restore identity from the framework session cookie.
``"api_key"``        ``X-Api-Key`` / ``ApiKey <key>`` header.
``"password"``       Credential login (programmatic).
===================  ==================================================

Extensibility::

    from aquilia.auth import register_strategy
    from aquilia.auth.strategies import AuthStrategyRegistry

    class GoogleOAuthBackend:
        def __init__(self, identity_store, client_id): ...
        def accepts(self, credentials): return "google_code" in credentials
        async def authenticate(self, credentials): ...

    register_strategy("google", lambda auth_manager: GoogleOAuthBackend(
        auth_manager.identity_store, client_id="...",
    ))

    # workspace.py — the name is now first-class config:
    class auth(AquilaConfig.Auth):
        backends = ["google", "jwt-stateless"]

A factory receives the :class:`~aquilia.auth.manager.AuthManager` being
wired (expose ``identity_store``, ``credential_store``, ``token_manager``,
``password_hasher``, ``rate_limiter`` on your own object if your strategy
needs different dependencies). A bare backend class or instance may also be
registered directly.
"""

from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass


StrategyFactory = Callable[[Any], Any]


class AuthStrategyRegistry:
    """
    Registry mapping strategy names to backend factories.

    The registry is intentionally tiny: names → zero-arg or
    ``auth_manager``-aware factories. Construction concerns (which store,
    which token manager) stay in the factory.
    """

    def __init__(self) -> None:
        self._factories: dict[str, StrategyFactory] = {}

    def register(self, name: str, backend: Any) -> None:
        """
        Register *backend* under *name*.

        ``backend`` may be:

        * a callable taking the :class:`~aquilia.auth.manager.AuthManager`
          (the usual factory form);
        * a backend **class** — instantiated with the AuthManager if its
          ``__init__`` accepts an ``auth_manager`` parameter, else with no
          arguments;
        * a ready-made **instance** (returned unchanged on every create).
        """
        if not name or not isinstance(name, str):
            raise ValueError("Strategy name must be a non-empty string")
        self._factories[name] = self._normalize(backend)

    def register_factory(self, name: str, factory: StrategyFactory) -> None:
        """Register an explicit factory (alias of :meth:`register` for callables)."""
        self.register(name, factory)

    def unregister(self, name: str) -> None:
        """Remove a strategy registration (built-ins can be overridden this way)."""
        self._factories.pop(name, None)

    def is_registered(self, name: str) -> bool:
        return name in self._factories

    def names(self) -> list[str]:
        return sorted(self._factories)

    def create(self, name: str, auth_manager: Any) -> Any:
        """
        Instantiate the strategy named *name* for *auth_manager*.

        Raises:
            ValueError: Unknown strategy name (with the available names).
        """
        factory = self._factories.get(name)
        if factory is None:
            available = ", ".join(self.names()) or "(none)"
            raise ValueError(f"Unknown authentication strategy: {name!r}. Available: {available}")
        return factory(auth_manager)

    # ── internals ───────────────────────────────────────────────────────

    @staticmethod
    def _normalize(backend: Any) -> StrategyFactory:
        if callable(backend) and not inspect.isclass(backend):
            # Plain factory.
            return backend

        if inspect.isclass(backend):

            def class_factory(auth_manager: Any, _cls: type = backend) -> Any:
                try:
                    sig = inspect.signature(_cls.__init__)
                except (TypeError, ValueError):
                    return _cls()
                params = sig.parameters
                if "auth_manager" in params:
                    return _cls(auth_manager)
                # Any signature inspectable custom class: hand over the
                # AuthManager so it can pick the dependencies it declares.
                kwargs = {}
                for pname in params:
                    if pname == "self":
                        continue
                    if pname == "auth_manager":
                        kwargs[pname] = auth_manager
                    elif pname == "identity_store":
                        kwargs[pname] = getattr(auth_manager, "identity_store", None)
                    elif pname == "credential_store":
                        kwargs[pname] = getattr(auth_manager, "credential_store", None)
                    elif pname == "token_manager":
                        kwargs[pname] = getattr(auth_manager, "token_manager", None)
                    elif pname == "password_hasher":
                        kwargs[pname] = getattr(auth_manager, "password_hasher", None)
                    elif pname == "rate_limiter":
                        kwargs[pname] = getattr(auth_manager, "rate_limiter", None)
                if kwargs or not params:
                    try:
                        return _cls(**kwargs)
                    except TypeError:
                        pass
                return _cls(auth_manager) if "auth_manager" in params else _cls()

            return class_factory

        # Ready-made instance.
        return lambda _auth_manager, _inst=backend: _inst


def _builtin_factories() -> dict[str, StrategyFactory]:
    """Lazily-imported built-in strategies (avoids import cycles at module load)."""

    def token(auth_manager: Any) -> Any:
        from aquilia.auth.backends.token import TokenBackend

        return TokenBackend(auth_manager.token_manager, auth_manager.identity_store)

    def jwt_stateless(auth_manager: Any) -> Any:
        from aquilia.auth.backends.token import StatelessTokenBackend

        builder = getattr(auth_manager, "principal_builder", None)
        return StatelessTokenBackend(auth_manager.token_manager, principal_builder=builder)

    def session(auth_manager: Any) -> Any:
        from aquilia.auth.backends.base import SessionBackend

        return SessionBackend(auth_manager.identity_store)

    def password(auth_manager: Any) -> Any:
        from aquilia.auth.backends.password import PasswordBackend

        return PasswordBackend(
            auth_manager.identity_store,
            auth_manager.credential_store,
            auth_manager.password_hasher,
            auth_manager.rate_limiter,
            getattr(auth_manager, "login_identifier_attributes", None),
        )

    def api_key(auth_manager: Any) -> Any:
        from aquilia.auth.backends.api_key import ApiKeyBackend

        return ApiKeyBackend(auth_manager.credential_store, auth_manager.identity_store)

    return {
        "token": token,
        "jwt": token,
        "jwt-stateless": jwt_stateless,
        "stateless": jwt_stateless,
        "session": session,
        "api_key": api_key,
        "password": password,
    }


def create_default_registry() -> AuthStrategyRegistry:
    """A fresh registry pre-populated with the built-in strategies."""
    registry = AuthStrategyRegistry()
    for name, factory in _builtin_factories().items():
        registry.register_factory(name, factory)
    return registry


#: The process-wide default registry. Applications may swap it wholesale
#: (``set_default_registry``) or register additional strategies into it.
_default_registry: AuthStrategyRegistry | None = None


def get_default_registry() -> AuthStrategyRegistry:
    """The process-wide default registry (created on first use)."""
    global _default_registry
    if _default_registry is None:
        _default_registry = create_default_registry()
    return _default_registry


def set_default_registry(registry: AuthStrategyRegistry) -> None:
    """Replace the process-wide default registry."""
    global _default_registry
    _default_registry = registry


def reset_default_registry() -> None:
    """Reset to a fresh built-in registry (test isolation)."""
    global _default_registry
    _default_registry = create_default_registry()


def register_strategy(name: str, backend: Any) -> None:
    """
    Register a strategy in the default registry.

    Example::

        register_strategy("google", lambda am: GoogleOAuthBackend(am.identity_store))
    """
    get_default_registry().register(name, backend)


__all__ = [
    "AuthStrategyRegistry",
    "create_default_registry",
    "get_default_registry",
    "set_default_registry",
    "reset_default_registry",
    "register_strategy",
]
