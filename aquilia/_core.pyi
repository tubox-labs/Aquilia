"""Type stubs for the native core engine.

Hand-written rather than nanobind-stubgen output: the module surface is small and
the semantics of `match`'s three-way return need prose that a generator will not
produce.

Import from :mod:`aquilia._core_loader`, not from here -- this module does not
exist when the extension is not built.
"""

from typing import Any, Final

class ParamKind:
    """Conversion applied to a captured path segment.

    Only these three exist natively. Any other param type (bool, uuid, slug,
    json, path) disqualifies its whole HTTP method from native matching on the
    Python side.
    """

    STR: Final[ParamKind]
    INT: Final[ParamKind]
    FLOAT: Final[ParamKind]

DEFER: Final[Any]
"""Sentinel meaning "the native matcher declines to decide; run the Python tiers".

Is ``NotImplemented``. Returned only when a param value falls outside the strict
ASCII fast path (``1_000``, ``" 42"``, Unicode digits), where CPython's
``int()``/``float()`` semantics are the authority.
"""

NO_INTERN: Final[int]

def noop() -> None:
    """No-op. Exists to measure per-call binding overhead."""

class Interner:
    """Append-only byte-string to dense-id table. Byte-safe (NULs, invalid UTF-8)."""

    def __init__(self) -> None: ...
    def intern(self, s: str) -> int:
        """Return the id for ``s``, assigning one if unseen. Idempotent."""

    def lookup(self, s: str) -> int:
        """Return the id for ``s``, or ``NO_INTERN`` if never interned."""

    def get(self, id: int) -> str:
        """Return the bytes behind ``id``, or ``""`` if ``id`` is invalid."""

    def __len__(self) -> int: ...

class Router:
    """Radix trie router with a static-path fast path.

    Lifecycle: construct, register routes, ``freeze()``, then ``match()``.
    ``freeze()`` is one-way; post-freeze the router is immutable and ``match()``
    is lock-free from any thread.
    """

    def __init__(self) -> None: ...
    def add_static(self, method: str, path: str, route_id: int) -> bool:
        """Register a parameter-free path for O(1) exact lookup.

        Returns False on conflict, meaning the caller must keep the whole method
        on the Python path so the existing ``RoutingFault`` is still raised.
        """

    def add_route(self, method: str, path: str, param_kinds: dict[str, ParamKind], route_id: int) -> bool:
        """Register a parameterised path.

        ``path`` must be the **compiled** pattern (``compiled_pattern.raw``), not
        ``route.full_path``: the decorators normalise ``{name}`` to
        ``<name:type>`` before compilation, and only the compiled form agrees
        with ``compiled_pattern.params``.

        Returns False when the path is not natively representable, in which case
        the caller must keep the whole method on the Python path.
        """

    def freeze(self) -> None:
        """Flatten the trie into contiguous arrays. Idempotent, one-way."""

    @property
    def frozen(self) -> bool: ...
    @property
    def node_count(self) -> int: ...
    @property
    def static_count(self) -> int: ...
    def match(self, method: str, path: str) -> tuple[int, dict[str, Any]] | Any | None:
        """Match ``path``, three-way.

        * ``None`` -- definitive miss; no route for this method accepts the path.
        * ``DEFER`` -- native matching declined; run the Python tiers.
        * ``(route_id, params)`` -- hit.

        Compare the middle case with ``is DEFER``, never by truth-testing.
        """

    def allowed_methods(self, path: str) -> list[str]:
        """Methods accepting ``path``. For the 405 path only."""

class RequestContext:
    """Fixed-slot request context; the base of :class:`aquilia.RequestCtx`.

    The seven slots are data descriptors, so a write is a direct field store and
    never enters ``__setattr__``. Instances carry a ``__dict__``, so unknown
    attribute writes land there -- which is what keeps ``RequestCtx._extra``
    working without a ``__setattr__`` override.
    """

    def __init__(self) -> None: ...

    request: Any
    identity: Any
    session: Any
    auth: Any
    container: Any
    state: Any
    request_id: Any
