"""
Base Auth Backend and Session Backend.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable
from unittest.mock import Mock

if TYPE_CHECKING:
    from ..core import Identity, IdentityStore


@runtime_checkable
class AuthBackend(Protocol):
    """
    Structural protocol for authentication backends.
    """

    def accepts(self, credentials: dict[str, Any]) -> bool:
        """Return ``True`` when this backend can attempt the given credentials."""
        ...

    async def authenticate(self, credentials: dict[str, Any]) -> Identity | None:
        """
        Attempt authentication.
        """
        ...


class SessionBackend:
    """
    Authentication backend that restores identity from an active session.
    """

    def __init__(self, identity_store: IdentityStore) -> None:
        self._identity_store = identity_store

    def accepts(self, credentials: dict[str, Any]) -> bool:
        """Accept when a session is present."""
        return "session" in credentials

    async def authenticate(self, credentials: dict[str, Any]) -> Identity | None:
        """
        Restore identity from session principal or data.
        """
        if not self.accepts(credentials):
            return None

        session = credentials["session"]
        if session is None or isinstance(session, Mock):
            return None

        identity_id = None
        principal = getattr(session, "principal", None)
        if principal is not None and not isinstance(principal, Mock):
            identity_id = getattr(principal, "id", None)

        if not identity_id:
            data = getattr(session, "data", None)
            if isinstance(data, dict):
                identity_id = data.get("identity_id")

        if not identity_id or isinstance(identity_id, Mock):
            return None

        try:
            return await self._identity_store.get(identity_id)
        except Exception:
            return None


def resolve_backend(b: Any, auth_manager: Any) -> Any:
    """
    Resolve a backend reference (instance, class, short name, or dotted path)
    into an instantiated backend object.
    """
    import importlib
    import inspect

    if isinstance(b, str):
        b_lower = b.strip().lower()
        if b_lower == "token":
            from .token import TokenBackend

            return TokenBackend(auth_manager.token_manager, auth_manager.identity_store)
        elif b_lower == "session":
            return SessionBackend(auth_manager.identity_store)
        elif b_lower == "password":
            from .password import PasswordBackend

            return PasswordBackend(
                auth_manager.identity_store,
                auth_manager.credential_store,
                auth_manager.password_hasher,
                auth_manager.rate_limiter,
                auth_manager.login_identifier_attributes,
            )
        elif b_lower == "api_key":
            from .api_key import ApiKeyBackend

            return ApiKeyBackend(auth_manager.credential_store, auth_manager.identity_store)
        elif "." in b:
            # Dotted path to class or function
            try:
                module_path, class_name = b.rsplit(".", 1)
                module = importlib.import_module(module_path)
                backend_cls = getattr(module, class_name)
            except (ValueError, ImportError, AttributeError) as err:
                raise ImportError(f"Could not import auth backend: {b}") from err
            return resolve_backend(backend_cls, auth_manager)
        else:
            raise ValueError(f"Unknown authentication backend name: {b}")

    if inspect.isclass(b):
        cls_name = b.__name__
        if cls_name == "TokenBackend":
            from .token import TokenBackend

            return TokenBackend(auth_manager.token_manager, auth_manager.identity_store)
        elif cls_name == "SessionBackend":
            return SessionBackend(auth_manager.identity_store)
        elif cls_name == "PasswordBackend":
            from .password import PasswordBackend

            return PasswordBackend(
                auth_manager.identity_store,
                auth_manager.credential_store,
                auth_manager.password_hasher,
                auth_manager.rate_limiter,
                auth_manager.login_identifier_attributes,
            )
        elif cls_name == "ApiKeyBackend":
            from .api_key import ApiKeyBackend

            return ApiKeyBackend(auth_manager.credential_store, auth_manager.identity_store)

        # Custom backend class signature inspection
        try:
            sig = inspect.signature(b)
        except ValueError:
            return b()

        kwargs = {}
        for name, param in sig.parameters.items():
            if name == "self":
                continue
            if name == "auth_manager":
                kwargs[name] = auth_manager
            elif name == "identity_store":
                kwargs[name] = getattr(auth_manager, "identity_store", None)
            elif name == "credential_store":
                kwargs[name] = getattr(auth_manager, "credential_store", None)
            elif name == "token_manager":
                kwargs[name] = getattr(auth_manager, "token_manager", None)
            elif name == "password_hasher":
                kwargs[name] = getattr(auth_manager, "password_hasher", None)
            elif name == "rate_limiter":
                kwargs[name] = getattr(auth_manager, "rate_limiter", None)

        return b(**kwargs)

    return b
