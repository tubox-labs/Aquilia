"""
Aquilia Versioning — Version Parser

Parses raw version strings into ``ApiVersion`` instances.

Supported formats:
- ``"1"`` → (1, 0, 0)
- ``"1.0"`` → (1, 0, 0)
- ``"2.1"`` → (2, 1, 0)
- ``"2.1.3"`` → (2, 1, 3)
- ``"v2"`` → (2, 0, 0)  (strip 'v' prefix)
- ``"v2.1"`` → (2, 1, 0)
- ``"2025-01"`` → (2025, 1, 0)  (epoch format)
- ``"2025-01-15"`` → (2025, 1, 15)  (epoch with day)

The parser is a pluggable protocol: users can implement custom parsers
for non-numeric version schemes (e.g. date-based, codename-based).
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod

from .core import ApiVersion
from .errors import InvalidVersionError


class VersionParser(ABC):
    """
    Abstract version parser protocol.

    Subclass this to implement custom version parsing (e.g. date-based,
    codename-based, or any non-standard format).
    """

    @abstractmethod
    def parse(self, raw: str) -> ApiVersion:
        """
        Parse a raw version string into an ``ApiVersion``.

        Args:
            raw: Raw version string from request.

        Returns:
            Parsed ``ApiVersion`` instance.

        Raises:
            InvalidVersionError: If the string cannot be parsed.
        """
        ...

    @abstractmethod
    def format(self, version: ApiVersion) -> str:
        """
        Format an ``ApiVersion`` back to a string.

        Args:
            version: The ``ApiVersion`` to format.

        Returns:
            String representation.
        """
        ...


# ── Regex patterns ────────────────────────────────────────────────────
# Matches: v2, v2.1, v2.1.3, 2, 2.1, 2.1.3
_SEMANTIC_RE = re.compile(
    r"^v?(\d+)(?:\.(\d+))?(?:\.(\d+))?$",
    re.IGNORECASE,
)

# Matches epoch: 2025-01, 2025-01-15
_EPOCH_RE = re.compile(
    r"^(\d{4})-(\d{1,2})(?:-(\d{1,2}))?$",
)


class SemanticVersionParser(VersionParser):
    """
    Default version parser supporting semantic and epoch formats.

    Parses both ``major.minor.patch`` and ``YYYY-MM`` epoch formats.
    The 'v' prefix is optional and case-insensitive.
    """

    def parse(self, raw: str) -> ApiVersion:
        """Parse version string.

        Examples::

            parse("2")       → ApiVersion(2, 0, 0)
            parse("v2.1")    → ApiVersion(2, 1, 0)
            parse("2025-01") → ApiVersion(2025, 1, 0, label="2025-01")
        """
        if not raw or not isinstance(raw, str):
            raise InvalidVersionError(
                str(raw),
                reason="Version string must be a non-empty string.",
            )

        cleaned = raw.strip()

        # Try epoch format first (YYYY-MM or YYYY-MM-DD)
        epoch_match = _EPOCH_RE.match(cleaned)
        if epoch_match:
            year = int(epoch_match.group(1))
            month = int(epoch_match.group(2))
            day = int(epoch_match.group(3)) if epoch_match.group(3) else 0
            return ApiVersion(
                major=year,
                minor=month,
                patch=day,
                label=cleaned,
            )

        # Try semantic format (v?major.minor.patch)
        sem_match = _SEMANTIC_RE.match(cleaned)
        if sem_match:
            major = int(sem_match.group(1))
            minor = int(sem_match.group(2)) if sem_match.group(2) else 0
            patch = int(sem_match.group(3)) if sem_match.group(3) else 0
            return ApiVersion(major=major, minor=minor, patch=patch)

        raise InvalidVersionError(
            raw,
            reason=("Expected format: 'N', 'N.N', 'N.N.N', 'vN', 'vN.N', 'YYYY-MM', or 'YYYY-MM-DD'."),
        )

    def format(self, version: ApiVersion) -> str:
        """Format version to string."""
        return str(version)


# Module-level singleton for convenience
_default_parser = SemanticVersionParser()
