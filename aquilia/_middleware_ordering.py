"""Middleware ordering helpers — transport-agnostic leaf module.

Both middleware stacks (HTTP ``MiddlewareStack`` and WebSocket
``SocketMiddlewareStack``) sort by ``(scope_rank, priority)`` ascending and
report same-scope priority collisions. The rules are identical and small, so
they live here rather than being copied into each stack.

Import nothing from the rest of the framework.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Protocol


class _Descriptor(Protocol):
    """Minimal surface of a middleware descriptor used for collision checks."""

    name: str
    scope: str
    priority: int


# Ordering contract: ascending priority = outer = runs first. Lower priority
# wins ties by registration order (stable sort), which is an implementation
# detail, not a public guarantee — that is exactly why collisions are reported.
def scope_rank(scope: str, order: Mapping[str, int]) -> int:
    """Map a middleware scope string to its rank.

    Scopes are ``"global"``, ``"app:name"`` / ``"namespace:/chat"``,
    ``"controller:name"`` / ``"event:foo"``, ``"route:..."`` — the prefix
    before the first ``:`` selects the band; the suffix discriminates within it.
    Unknown scopes sort last so foreign middleware still runs, just after
    framework bands.
    """
    scope_type = scope.split(":", 1)[0]
    return order.get(scope_type, 99)


def find_collision(
    existing: Sequence[_Descriptor],
    scope: str,
    priority: int,
) -> _Descriptor | None:
    """Return an already-registered descriptor sharing scope and priority, if any."""
    for desc in existing:
        if desc.priority == priority and desc.scope == scope:
            return desc
    return None


def collision_message(name: str, other_name: str, scope: str, priority: int) -> str:
    """The warning/error text used by both stacks, in one place."""
    return (
        f"Middleware priority collision: '{name}' and '{other_name}' both registered "
        f"at scope={scope!r} priority={priority}. Their relative order falls back to "
        f"registration order, which is not part of the public API and can change silently "
        f"when registration code is reordered. Give one of them a distinct priority."
    )


__all__ = ["scope_rank", "find_collision", "collision_message"]
