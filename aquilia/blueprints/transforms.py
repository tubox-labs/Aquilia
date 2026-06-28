"""
Aquilia Blueprint Transforms -- built-in transform callables for >> pipelines.

Usage::

    from aquilia.blueprints.transforms import strip, lower, dasherize

    slug: Annotated[str, Facet.text() >> strip >> lower >> dasherize >> Facet.pattern(r"^[a-z0-9-]+$")]

Each transform is a plain function: one positional argument → transformed value.
Custom transforms follow the same contract.
"""

from __future__ import annotations

import re
from collections.abc import Callable

__all__ = [
    "strip",
    "lstrip",
    "rstrip",
    "lower",
    "upper",
    "title",
    "dasherize",
    "slugify",
    "coerce_int",
    "coerce_float",
    "coerce_bool",
    "truncate",
]


def strip(value: str) -> str:
    """Strip leading and trailing whitespace."""
    return value.strip()


def lstrip(value: str) -> str:
    """Strip leading whitespace."""
    return value.lstrip()


def rstrip(value: str) -> str:
    """Strip trailing whitespace."""
    return value.rstrip()


def lower(value: str) -> str:
    """Convert to lowercase."""
    return value.lower()


def upper(value: str) -> str:
    """Convert to uppercase."""
    return value.upper()


def title(value: str) -> str:
    """Convert to title case."""
    return value.title()


def dasherize(value: str) -> str:
    """Replace spaces and underscores with hyphens, then lowercase."""
    return re.sub(r"[\s_]+", "-", value).lower()


def slugify(value: str) -> str:
    """Dasherize then remove all non-alphanumeric-hyphen characters."""
    dashed = dasherize(value)
    return re.sub(r"[^a-z0-9-]", "", dashed)


def coerce_int(value) -> int:
    """Coerce value to int. Raises ValueError on failure."""
    return int(value)


def coerce_float(value) -> float:
    """Coerce value to float. Raises ValueError on failure."""
    return float(value)


_TRUTHY = frozenset({"true", "1", "yes", "on", "t", "y"})
_FALSY = frozenset({"false", "0", "no", "off", "f", "n"})


def coerce_bool(value) -> bool:
    """Coerce value to bool.

    Accepts 'true'/'1'/'yes'/'on'/'t'/'y' → True,
    'false'/'0'/'no'/'off'/'f'/'n' → False (case-insensitive).
    Non-string values are passed through bool().
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in _TRUTHY:
            return True
        if lowered in _FALSY:
            return False
        raise ValueError(f"Cannot coerce {value!r} to bool")
    return bool(value)


def truncate(max_len: int) -> Callable[[str], str]:
    """Return a transform that truncates strings to *max_len* characters."""

    def _truncate(value: str) -> str:
        return value[:max_len]

    _truncate.__name__ = f"truncate({max_len})"
    _truncate.__qualname__ = f"truncate({max_len})"
    return _truncate
