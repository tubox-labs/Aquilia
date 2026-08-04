"""Type stubs for the native data engine extension.

Hand-written rather than generated: the module is small, and the stub doubles as
the authoritative description of the boundary API.
"""

from typing import Any, Final

def noop() -> None:
    """Do nothing. Used to measure the Python<->native call cost."""

def uuid_from_string(s: str) -> Any | None:
    """Parse a canonical UUID string into a ``uuid.UUID``.

    Returns ``None`` -- not an exception -- when the string falls outside the
    narrow grammar the native parser accepts. CPython's ``uuid.UUID`` accepts
    several forms this parser deliberately refuses (underscore separators,
    leading signs, surrounding whitespace), so the caller must fall back to it
    rather than treating ``None`` as invalid input.

    Raises ``ValueError`` only when the input is invalid to CPython as well.
    """

def convert(code: int, raw: Any | None) -> Any:
    """Convert one value according to a :class:`TypeCode`.

    A parity-test and measurement entry point, **not** the production API: a
    per-field native call is refuted by ``docs/models-engine/02`` §3, because the
    boundary crossing costs more than six of the eight scalar conversions.
    Production traffic goes through the batch plans instead.
    """

class TypeCode:
    """Type codes shared by both plans. Mirrors ``src/typecode.hpp``."""

    PASSTHROUGH: Final[int]
    STR: Final[int]
    INT: Final[int]
    FLOAT: Final[int]
    BOOL: Final[int]
    DATE: Final[int]
    DATETIME: Final[int]
    TIME: Final[int]
    DECIMAL: Final[int]
    UUID: Final[int]
    JSON: Final[int]
    BYTES: Final[int]
    UNSUPPORTED: Final[int]
