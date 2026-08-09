"""Middleware type aliases and the ``Scope`` value type — dependency-free leaf.

The callable aliases stay canonical in :mod:`aquilia.typing.middleware`; they are
re-exported here so middleware authors have one import to remember. ``Scope`` is
new: registration used to pass scope around as a bare string and re-split it at
every use site.

Import nothing from the rest of the framework here.
"""

from __future__ import annotations

from dataclasses import dataclass

from aquilia.typing.middleware import (
    MiddlewareCallable,
    MiddlewareName,
    MiddlewarePriority,
    MiddlewareProtocol,
    MiddlewareScope,
    RequestHandler,
)

# ``Handler`` is the historical spelling used across the framework and in user
# middleware signatures. Kept as the primary name.
Handler = RequestHandler


@dataclass(frozen=True, slots=True)
class Scope:
    """A parsed middleware scope.

    A scope string is ``"<band>"`` or ``"<band>:<target>"`` — ``"global"``,
    ``"app:billing"``, ``"controller:users"``, ``"route:/health"``. The band
    selects the ordering tier; the target discriminates within it.

    Parsing once at registration means the stack, the collision check, and any
    future scoped-execution filter all read the same two fields instead of each
    calling ``split(":", 1)`` on the raw string.
    """

    band: str
    target: str = ""

    @classmethod
    def parse(cls, raw: str | Scope) -> Scope:
        """Build a scope from its string form. Already-parsed scopes pass through."""
        if isinstance(raw, Scope):
            return raw
        band, _, target = raw.partition(":")
        return cls(band, target)

    def matches(self, band: str, target: str) -> bool:
        """True when this scope applies to *band*/*target*.

        ``global`` applies everywhere. A scope with an empty target applies to
        its whole band. Otherwise both must match exactly.
        """
        if self.band == "global":
            return True
        if self.band != band:
            return False
        return not self.target or self.target == target

    def __str__(self) -> str:
        return self.band if not self.target else f"{self.band}:{self.target}"


__all__ = [
    "Handler",
    "MiddlewareCallable",
    "MiddlewareName",
    "MiddlewarePriority",
    "MiddlewareProtocol",
    "MiddlewareScope",
    "RequestHandler",
    "Scope",
]
