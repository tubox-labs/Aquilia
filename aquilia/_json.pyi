"""Type stubs for the native JSON engine.

Nothing in ``aquilia`` should import this module directly -- go through
:mod:`aquilia.json`, which selects between this and the standard library and
normalises the exception types.
"""

from typing import Any, Callable

def dumps(obj: Any, default: Callable[[Any], Any] | None = ...) -> bytes:
    """Serialise ``obj`` to UTF-8 JSON bytes.

    Args:
        obj: Object graph to serialise.
        default: Called for objects the encoder cannot represent directly. Its
            return value is encoded with the hook disabled, so a hook that
            returns another unsupported object raises rather than recursing.

    Returns:
        UTF-8 encoded JSON.

    Raises:
        TypeError: An object in the graph is not serialisable.
        ValueError: A float was NaN or infinite, or nesting exceeded the limit.
    """
    ...

def loads(data: bytes | bytearray | memoryview | str) -> Any:
    """Parse JSON into Python objects.

    Args:
        data: UTF-8 bytes or a ``str``.

    Returns:
        The decoded object graph. Duplicate object keys resolve last-wins,
        matching :func:`json.loads`.

    Raises:
        ValueError: Input was not well-formed JSON, or nesting exceeded the limit.
        TypeError: ``data`` was not a supported input type.
    """
    ...

def noop() -> None:
    """Do nothing. Used to measure the Python<->native call cost."""
    ...
