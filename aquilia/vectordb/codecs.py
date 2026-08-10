"""
AquilaVectorDB — Payload codecs.

elips metadata is flat and narrowly typed: ``MetaValue = bool | int | float | str``,
one level deep, no lists. Python payloads are not, so every ``Payload`` attribute
is routed through a codec that encodes on write and decodes on read.

The table is closed by design. An attribute whose type has no codec raises
:class:`~aquilia.vectordb.faults.VectorSchemaFault` at model-creation time rather
than failing on first write — a store half-populated with unreadable values is
much harder to recover from than an import error.

Round-trip caveats, stated rather than hidden:

* ``datetime`` encodes to a POSIX timestamp (``float``). Naive values are
  assumed UTC. Decode returns a **timezone-aware UTC** ``datetime``, so a naive
  value in is an aware value out — the instant survives, the ``tzinfo`` does not.
* ``Decimal`` encodes to ``str`` to keep exactness. Range filters over it are
  therefore rejected (lexicographic ordering is wrong: ``"9" > "10"``);
  equality and membership work.
* ``UUID`` encodes to its canonical hyphenated string.
* ``Enum`` encodes to ``.value``, which must itself be a ``MetaValue``.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from decimal import Decimal
from enum import Enum
from typing import Any

META_SCALARS: tuple[type, ...] = (bool, int, float, str)


@dataclass(frozen=True)
class Codec:
    """
    Bidirectional converter between a Python type and an elips ``MetaValue``.

    Attributes:
        name: Stable codec identifier, surfaced in schema dumps and faults.
        encode: Python value → ``MetaValue``.
        decode: ``MetaValue`` → Python value.
        meta_type: The ``MetaValue`` primitive this codec stores as. Drives
            range-filter admissibility: only ``int``/``float`` orderings are
            faithful.
        orderable: Whether range lookups (``__gt``, ``__lte``, ...) are
            meaningful in the encoded space.
    """

    name: str
    encode: Callable[[Any], Any]
    decode: Callable[[Any], Any]
    meta_type: type
    orderable: bool = True


def _identity(value: Any) -> Any:
    """Return ``value`` unchanged — used by the scalar pass-through codecs."""
    return value


def _encode_datetime(value: Any) -> float:
    """Encode a ``datetime`` as a POSIX timestamp, treating naive input as UTC."""
    if not isinstance(value, datetime):
        value = datetime.fromisoformat(str(value))
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.timestamp()


def _decode_datetime(value: Any) -> datetime:
    """Decode a POSIX timestamp into a timezone-aware UTC ``datetime``."""
    return datetime.fromtimestamp(float(value), tz=timezone.utc)


def _encode_date(value: Any) -> str:
    """Encode a ``date`` as an ISO-8601 string (lexicographically ordered)."""
    if isinstance(value, datetime):
        value = value.date()
    elif not isinstance(value, date):
        value = date.fromisoformat(str(value))
    return value.isoformat()


def _decode_date(value: Any) -> date:
    """Decode an ISO-8601 date string."""
    return date.fromisoformat(str(value))


def _encode_time(value: Any) -> str:
    """Encode a ``time`` as an ISO-8601 string."""
    if not isinstance(value, time):
        value = time.fromisoformat(str(value))
    return value.isoformat()


def _decode_time(value: Any) -> time:
    """Decode an ISO-8601 time string."""
    return time.fromisoformat(str(value))


def _encode_decimal(value: Any) -> str:
    """Encode a ``Decimal`` as its exact string form."""
    return str(Decimal(value))


def _decode_decimal(value: Any) -> Decimal:
    """Decode an exact ``Decimal`` from its string form."""
    return Decimal(str(value))


def _encode_uuid(value: Any) -> str:
    """Encode a ``UUID`` as its canonical hyphenated string."""
    return str(uuid.UUID(str(value)))


def _decode_uuid(value: Any) -> uuid.UUID:
    """Decode a canonical UUID string."""
    return uuid.UUID(str(value))


def _encode_bytes(value: Any) -> str:
    """Encode ``bytes`` as base64 ASCII.

    Not orderable, and not cheap: base64 inflates by 4/3 and every filter over
    it compares the encoded form. Suitable for short opaque handles, not blobs.
    """
    import base64

    return base64.b64encode(bytes(value)).decode("ascii")


def _decode_bytes(value: Any) -> bytes:
    """Decode base64 ASCII back to ``bytes``."""
    import base64

    return base64.b64decode(str(value).encode("ascii"))


#: Codecs keyed by exact Python type. Consulted before the ``Enum`` check.
CODECS: dict[type, Codec] = {
    bool: Codec("bool", _identity, bool, bool),
    int: Codec("int", _identity, int, int),
    float: Codec("float", _identity, float, float),
    str: Codec("str", _identity, str, str),
    datetime: Codec("datetime", _encode_datetime, _decode_datetime, float),
    date: Codec("date", _encode_date, _decode_date, str),
    time: Codec("time", _encode_time, _decode_time, str),
    # Exact but not orderable in the encoded space — see module docstring.
    Decimal: Codec("decimal", _encode_decimal, _decode_decimal, str, orderable=False),
    uuid.UUID: Codec("uuid", _encode_uuid, _decode_uuid, str, orderable=False),
    bytes: Codec("bytes", _encode_bytes, _decode_bytes, str, orderable=False),
}


def enum_codec(enum_cls: type[Enum]) -> Codec:
    """
    Build a codec for an ``Enum`` subclass.

    Encodes to ``member.value`` and decodes by calling ``enum_cls(value)``.
    The member values must all be ``MetaValue`` primitives; a nested payload
    (e.g. a tuple value) has no encoding and is rejected here.

    Args:
        enum_cls: The enum type to build a codec for.

    Returns:
        A :class:`Codec` for ``enum_cls``.

    Raises:
        ValueError: If any member value is not a ``MetaValue`` primitive. The
            caller (metaclass) converts this into a ``VectorSchemaFault``.
    """
    value_types = {type(m.value) for m in enum_cls}
    bad = [t for t in value_types if t not in META_SCALARS]
    if bad:
        names = ", ".join(t.__name__ for t in bad)
        raise ValueError(
            f"Enum {enum_cls.__name__} has member values of type {names}, "
            f"which elips metadata cannot store (allowed: bool, int, float, str)"
        )

    meta_type = next(iter(value_types)) if len(value_types) == 1 else str

    return Codec(
        name=f"enum:{enum_cls.__name__}",
        encode=lambda v: v.value if isinstance(v, Enum) else v,
        decode=lambda v: enum_cls(v),
        meta_type=meta_type,
        orderable=meta_type in (int, float),
    )


def resolve_codec(py_type: Any) -> Codec | None:
    """
    Return the codec for ``py_type``, or ``None`` when none applies.

    Optional types are unwrapped by the caller before this is consulted;
    ``None`` payload values bypass codecs entirely and are omitted from the
    metadata dict (elips has no null — an absent key *is* the absence).

    Args:
        py_type: The unwrapped, non-optional annotation type.

    Returns:
        The matching :class:`Codec`, or ``None`` if the type is unsupported.
    """
    codec = CODECS.get(py_type)
    if codec is not None:
        return codec

    if isinstance(py_type, type):
        if issubclass(py_type, Enum):
            return enum_codec(py_type)
        # Subclasses of the scalar primitives (e.g. IntEnum handled above,
        # or a str subclass) encode as their base primitive.
        for base in META_SCALARS:
            if issubclass(py_type, base):
                return CODECS[base]

    return None


def decode_value(value: Any, py_type: Any) -> Any:
    """
    Decode a stored ``MetaValue`` back into ``py_type``.

    Used on the hydration path, where the target type comes from the compiled
    schema rather than being re-derived per record.

    Args:
        value: The raw value as elips returned it.
        py_type: The attribute's unwrapped, non-optional annotation type.

    Returns:
        The decoded value. A value that cannot be decoded is returned unchanged
        rather than raising: a read must not fail because one record predates a
        type change, and the caller can see the raw form. Writes are where type
        errors are caught, and those raise.
    """
    if value is None:
        return None

    codec = resolve_codec(py_type)
    if codec is None:
        return value

    try:
        return codec.decode(value)
    except Exception:
        return value


def encode_value(value: Any, py_type: Any) -> Any:
    """
    Encode a Python value into an elips ``MetaValue``.

    Args:
        value: The value to encode.
        py_type: The attribute's unwrapped, non-optional annotation type.

    Returns:
        The encoded ``MetaValue``, or ``None`` when ``value`` is ``None``.

    Raises:
        ValueError: When no codec covers ``py_type``.
    """
    if value is None:
        return None

    codec = resolve_codec(py_type)
    if codec is None:
        raise ValueError(f"no codec for type {getattr(py_type, '__name__', py_type)!r}")

    return codec.encode(value)


__all__ = [
    "CODECS",
    "META_SCALARS",
    "Codec",
    "decode_value",
    "encode_value",
    "enum_codec",
    "resolve_codec",
]
