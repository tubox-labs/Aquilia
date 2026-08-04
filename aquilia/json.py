"""Framework-wide JSON entry point.

Every JSON operation in Aquilia goes through this module. Nothing else in the
framework may import ``json``, ``orjson``, or any other codec directly on a
request path.

Why this module exists
----------------------
Before it, ``response.py``, ``request.py`` and ``controller/validation.py`` each
resolved their own codec with a different fallback chain and a different return
type. That is how :func:`Response.json` ended up serialising to ``str`` and then
paying a second full pass to encode it -- a 100KB payload was built twice. One
module, one resolution, one contract.

The contract
------------
- :func:`dumps` returns ``bytes``. Always. There is no ``str`` path to fall into.
- :func:`loads` accepts ``bytes``, ``bytearray``, ``memoryview`` or ``str``.
- Both raise :class:`JSONDecodeError` / :class:`JSONEncodeError` and nothing else
  for malformed input, so callers never need a bare ``except Exception``.

Backend selection
-----------------
``aquilia._json`` (the first-party native extension, yyjson-backed) when it is
importable, otherwise the standard library. ``orjson`` and ``ujson`` are
deliberately *not* consulted: a core dependency on a third-party codec is what
the previous design promised and never delivered, because it was an optional
import nobody installed. The default path has to be fast without asking the user
to install anything.

The selection happens exactly once, at import. :func:`backend` reports it, and
the benchmark harness records it so a run can never again silently measure a
codec nobody intended to test.
"""

from __future__ import annotations

import json as _stdlib
from typing import Any, Final

__all__ = [
    "JSONDecodeError",
    "JSONEncodeError",
    "backend",
    "default_serializer",
    "dumps",
    "loads",
    "native",
]


class JSONDecodeError(ValueError):
    """Raised when input is not well-formed JSON.

    Subclasses :class:`ValueError` so that existing ``except ValueError`` handlers
    -- including :class:`json.JSONDecodeError` handlers, which share that base --
    keep working across the backend switch.
    """


class JSONEncodeError(TypeError):
    """Raised when an object graph cannot be serialised.

    Subclasses :class:`TypeError` to match :func:`json.dumps`, which raises
    ``TypeError`` for unserialisable types.
    """


def default_serializer(o: Any) -> Any:
    """Fallback for types the encoder does not handle natively.

    Kept deliberately small: every branch here runs inside the encoder's slow
    path, and a long chain of ``isinstance`` checks on the hot path is exactly
    the kind of cost this module exists to remove.

    Args:
        o: The object the encoder could not represent.

    Returns:
        A JSON-representable stand-in.
    """
    if isinstance(o, (set, frozenset, tuple)):
        return list(o)
    isoformat = getattr(o, "isoformat", None)
    if isoformat is not None:
        return isoformat()
    if isinstance(o, bytes):
        return o.decode("utf-8", "replace")
    return str(o)


# ---------------------------------------------------------------------------
# Backend resolution -- once, at import.
# ---------------------------------------------------------------------------

_native_mod: Any = None
try:  # pragma: no cover - exercised by whichever branch the build produced
    from aquilia import _json as _native_mod  # type: ignore[attr-defined]
except ImportError:
    _native_mod = None

native: Final[bool] = _native_mod is not None
_BACKEND: Final[str] = "aquilia._json" if native else "stdlib"


def backend() -> str:
    """Name of the active codec: ``"aquilia._json"`` or ``"stdlib"``.

    Recorded in benchmark run metadata. A performance result is not meaningful
    without it.
    """
    return _BACKEND


if native:  # pragma: no cover - selected by build configuration
    _n_dumps = _native_mod.dumps
    _n_loads = _native_mod.loads
    _NativeDecodeError = _native_mod.DecodeError
    _NativeEncodeError = _native_mod.EncodeError

    def dumps(obj: Any, *, default: Any = default_serializer) -> bytes:
        """Serialise ``obj`` to UTF-8 JSON bytes.

        Args:
            obj: Object graph to serialise.
            default: Called for objects the encoder cannot represent directly.

        Returns:
            UTF-8 encoded JSON. Never ``str``.

        Raises:
            JSONEncodeError: The graph contains something ``default`` could not
                resolve, or nesting exceeded the configured limit.
        """
        try:
            return _n_dumps(obj, default)
        except _NativeEncodeError as exc:
            raise JSONEncodeError(str(exc)) from None

    def loads(data: bytes | bytearray | memoryview | str) -> Any:
        """Deserialise JSON to Python objects.

        Args:
            data: UTF-8 bytes or a ``str``.

        Returns:
            The decoded object graph.

        Raises:
            JSONDecodeError: Input was not well-formed JSON.
        """
        try:
            return _n_loads(data)
        except _NativeDecodeError as exc:
            raise JSONDecodeError(str(exc)) from None

else:
    _s_dumps = _stdlib.dumps
    _s_loads = _stdlib.loads

    def dumps(obj: Any, *, default: Any = default_serializer) -> bytes:
        """Serialise ``obj`` to UTF-8 JSON bytes.

        The ``separators`` argument matters: :func:`json.dumps` defaults to
        ``", "`` and ``": "``, which inflates every payload with whitespace no
        HTTP client wants. Compact separators are both smaller and faster.

        Args:
            obj: Object graph to serialise.
            default: Called for objects the encoder cannot represent directly.

        Returns:
            UTF-8 encoded JSON. Never ``str``.

        Raises:
            JSONEncodeError: The graph contains something ``default`` could not
                resolve, or it is recursive.
        """
        try:
            return _s_dumps(
                obj,
                default=default,
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode("utf-8")
        except (TypeError, ValueError, RecursionError) as exc:
            raise JSONEncodeError(str(exc)) from None

    def loads(data: bytes | bytearray | memoryview | str) -> Any:
        """Deserialise JSON to Python objects.

        Args:
            data: UTF-8 bytes or a ``str``.

        Returns:
            The decoded object graph.

        Raises:
            JSONDecodeError: Input was not well-formed JSON.
        """
        try:
            return _s_loads(data)
        except (ValueError, TypeError, UnicodeDecodeError) as exc:
            raise JSONDecodeError(str(exc)) from None
