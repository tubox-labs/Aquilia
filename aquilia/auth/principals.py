"""
AquilAuth — Principal Injection

First-class request-principal injection, comparable to NestJS's
``@CurrentUser()`` decorator, for **application-defined principal types**.

The framework principal (:class:`~aquilia.auth.core.Identity`) remains the
canonical internal representation, but applications usually want their own
principal type — a dataclass with exactly the fields their handlers use.
Two mechanisms compose:

**1. The ``CurrentUser`` marker (per-parameter)::

    from aquilia.auth import CurrentUser
    from aquilia.auth.principals import Principal

    @dataclass
    class AppUser:
        id: str
        session_id: str | None

    class MeController(Controller):
        @GET("/me")
        async def me(self, ctx, user: Annotated[AppUser, CurrentUser]):
            return {"id": user.id}

    The parameter resolves from the canonical auth state — the
    application principal when the auth pipeline produced one (see below),
    otherwise the framework ``Identity``. ``CurrentUser(optional=True)``
    injects ``None`` for anonymous requests instead of raising 401.

**2. The ``principal_factory`` (pipeline-level)**::

    # workspace.py
    class auth(AquilaConfig.Auth):
        principal_factory = "app.auth.build_principal"   # dotted path

    # app/auth.py
    def build_principal(identity, claims):
        return AppUser(id=identity.id, session_id=claims.get("sid"))

Once configured, every authenticated request carries the app principal on
``ctx.auth_state.principal`` / ``request.state["principal"]`` and the
``CurrentUser`` marker returns it. The factory also runs for stateless
strategies (``jwt-stateless`` builds principals straight from claims).

The module also defines :class:`Principal` — a minimal protocol any app
principal satisfies (``id`` attribute) — used only for documentation and
runtime ``getattr`` fallbacks.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable


class CurrentUser:
    """
    Marker for principal injection: ``Annotated[MyUser, CurrentUser]``.

    Usable as a bare class in ``Annotated`` metadata or as an instance::

        user: Annotated[AppUser, CurrentUser]                      # required
        user: Annotated[AppUser | None, CurrentUser(optional=True)]  # anonymous → None

    Also usable directly as the annotation — ``user: CurrentUser`` — which
    injects whatever the auth pipeline resolved (app principal, else the
    framework ``Identity``).
    """

    __aquilia_current_user__ = True

    def __init__(self, *, optional: bool = False) -> None:
        self.optional = optional


@runtime_checkable
class Principal(Protocol):
    """Anything with a stable identity id can serve as a principal."""

    @property
    def id(self) -> Any: ...


def find_current_user_marker(annotation: Any) -> CurrentUser | None:
    """
    Extract the ``CurrentUser`` marker (and its options) from an annotation.

    Handles the bare-class form (``Annotated[T, CurrentUser]``) and the
    instance form (``Annotated[T, CurrentUser(optional=True)]``). Returns
    ``None`` when the annotation carries no marker.
    """
    from typing import Annotated, get_args, get_origin

    def _as_marker(obj: Any) -> CurrentUser | None:
        if isinstance(obj, CurrentUser):
            return obj
        if obj is CurrentUser:
            return CurrentUser()
        return None

    marker = _as_marker(annotation)
    if marker is not None:
        return marker

    origin = get_origin(annotation)
    if origin is not None and origin is Annotated:
        for meta in get_args(annotation)[1:]:
            marker = _as_marker(meta)
            if marker is not None:
                return marker
    return None


def build_identity_fallback_principal(identity: Any) -> Any:
    """The default principal when no app factory produced one: the Identity."""
    return identity


@dataclass
class _AnonymousPrincipal:
    """Internal sentinel-free representation for anonymous requests."""

    id: Any = None


__all__ = [
    "CurrentUser",
    "Principal",
    "find_current_user_marker",
]
