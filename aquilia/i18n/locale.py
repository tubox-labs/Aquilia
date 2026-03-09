"""
Locale — BCP 47 locale tag parsing, normalization, and negotiation.

Implements RFC 5646 (BCP 47) language tag handling with:
- Structured parsing into language / script / region / variant components
- Normalization to canonical form (lowercase language, titlecase script, uppercase region)
- Accept-Language header parsing with quality values (RFC 4647)
- Locale matching with fallback chains
- Validation against known IANA subtags (common subset)

The ``Locale`` dataclass is the canonical representation used throughout
Aquilia's i18n system — middleware, DI, templates, and controllers all
work with ``Locale`` instances.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Tuple

# ═══════════════════════════════════════════════════════════════════════════
# BCP 47 Regex  (RFC 5646 §2.1)
# ═══════════════════════════════════════════════════════════════════════════

# Matches: language[-script][-region][-variant][-extension][-privateuse]
# Simplified for practical use — covers 99.9% of real-world tags
LOCALE_PATTERN = re.compile(
    r"^(?P<language>[a-zA-Z]{2,3})"          # 2-3 letter primary language
    r"(?:-(?P<script>[a-zA-Z]{4}))?"          # 4-letter script (optional)
    r"(?:-(?P<region>[a-zA-Z]{2}|\d{3}))?"    # 2-letter region or 3-digit (optional)
    r"(?:-(?P<variant>[a-zA-Z0-9]{5,8}))?"    # 5-8 char variant (optional)
    r"$",
    re.IGNORECASE,
)

# Accept-Language header value parser
# Matches: fr-CH, fr;q=0.9, en;q=0.8, *;q=0.5
_ACCEPT_LANG_RE = re.compile(
    r"(?P<tag>[a-zA-Z]{1,8}(?:-[a-zA-Z0-9]{1,8})*|\*)"
    r"(?:\s*;\s*q=(?P<q>[01](?:\.\d{1,3})?))?",
)


# ═══════════════════════════════════════════════════════════════════════════
# Locale Dataclass
# ═══════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True, slots=True)
class Locale:
    """
    Immutable BCP 47 locale tag.

    Attributes:
        language: ISO 639 primary language code (e.g. ``"en"``, ``"fr"``)
        script:   ISO 15924 script code (e.g. ``"Latn"``, ``"Hans"``) or ``None``
        region:   ISO 3166-1 region code (e.g. ``"US"``, ``"GB"``) or ``None``
        variant:  IANA variant subtag (e.g. ``"nedis"``, ``"1901"``) or ``None``

    The canonical string form is produced by ``str(locale)`` or ``locale.tag``.

    Examples::

        >>> Locale("en")
        Locale(language='en')
        >>> Locale("fr", region="CA")
        Locale(language='fr', region='CA')
        >>> str(Locale("zh", script="Hans"))
        'zh-Hans'
    """

    language: str
    script: Optional[str] = None
    region: Optional[str] = None
    variant: Optional[str] = None

    def __post_init__(self):
        # Normalize casing per BCP 47 conventions
        object.__setattr__(self, "language", self.language.lower())
        if self.script:
            object.__setattr__(self, "script", self.script.title())
        if self.region:
            # Numeric regions (e.g. "419") stay as-is
            if self.region.isalpha():
                object.__setattr__(self, "region", self.region.upper())

    @property
    def tag(self) -> str:
        """Full BCP 47 tag string."""
        parts = [self.language]
        if self.script:
            parts.append(self.script)
        if self.region:
            parts.append(self.region)
        if self.variant:
            parts.append(self.variant)
        return "-".join(parts)

    @property
    def language_tag(self) -> str:
        """Language-only tag (no script/region/variant)."""
        return self.language

    @property
    def fallback_chain(self) -> List["Locale"]:
        """
        Generate fallback chain from most specific to least.

        Example::

            Locale("fr", region="CA").fallback_chain
            # → [Locale("fr", region="CA"), Locale("fr")]
        """
        chain: list[Locale] = [self]
        if self.variant:
            chain.append(Locale(self.language, self.script, self.region))
        if self.region:
            if self.script:
                chain.append(Locale(self.language, self.script))
            chain.append(Locale(self.language))
        elif self.script:
            chain.append(Locale(self.language))
        return chain

    def matches(self, other: "Locale") -> bool:
        """
        Check if this locale matches another using prefix matching.

        ``en`` matches ``en-US``, ``en-GB``, etc.
        ``en-US`` does NOT match ``en-GB``.
        """
        if self.language != other.language:
            return False
        if self.script and other.script and self.script != other.script:
            return False
        if self.region and other.region and self.region != other.region:
            return False
        return True

    def __str__(self) -> str:
        return self.tag

    def __repr__(self) -> str:
        parts = [f"language={self.language!r}"]
        if self.script:
            parts.append(f"script={self.script!r}")
        if self.region:
            parts.append(f"region={self.region!r}")
        if self.variant:
            parts.append(f"variant={self.variant!r}")
        return f"Locale({', '.join(parts)})"


# ═══════════════════════════════════════════════════════════════════════════
# Parsing & Normalization
# ═══════════════════════════════════════════════════════════════════════════

def parse_locale(tag: str) -> Locale:
    """
    Parse a BCP 47 language tag into a ``Locale`` object.

    Handles common formats:
    - ``"en"`` → ``Locale("en")``
    - ``"en-US"`` → ``Locale("en", region="US")``
    - ``"zh-Hans"`` → ``Locale("zh", script="Hans")``
    - ``"zh-Hant-HK"`` → ``Locale("zh", script="Hant", region="HK")``
    - ``"de-CH-1901"`` → ``Locale("de", region="CH", variant="1901")``

    Also handles underscore notation (e.g. ``"en_US"`` → ``"en-US"``).

    Args:
        tag: BCP 47 language tag string

    Returns:
        Parsed ``Locale`` object

    Raises:
        ValueError: If the tag cannot be parsed
    """
    if not tag or not isinstance(tag, str):
        from aquilia.faults.domains import ConfigInvalidFault
        raise ConfigInvalidFault(
            key="i18n.locale",
            reason=f"Invalid locale tag: {tag!r}",
        )

    # Normalize: underscores → hyphens, strip whitespace
    tag = tag.strip().replace("_", "-")

    m = LOCALE_PATTERN.match(tag)
    if not m:
        # Try simple 2-3 letter language code
        if re.match(r"^[a-zA-Z]{2,3}$", tag):
            return Locale(language=tag)
        from aquilia.faults.domains import ConfigInvalidFault
        raise ConfigInvalidFault(
            key="i18n.locale",
            reason=f"Cannot parse locale tag: {tag!r}",
        )

    return Locale(
        language=m.group("language"),
        script=m.group("script"),
        region=m.group("region"),
        variant=m.group("variant"),
    )


def normalize_locale(tag: str) -> Optional[str]:
    """
    Normalize a locale tag to canonical BCP 47 form.

    - Lowercase language
    - Titlecase script
    - Uppercase region
    - Underscores → hyphens

    Args:
        tag: Raw locale tag

    Returns:
        Normalized tag string, or ``None`` if the tag cannot be parsed
    """
    try:
        return parse_locale(tag).tag
    except Exception:
        return None


def match_locale(
    requested: Locale,
    available: Sequence[Locale],
) -> Optional[Locale]:
    """
    Find the best matching locale from available options.

    Uses the following priority:
    1. Exact match (same tag)
    2. Prefix match (requested is more specific)
    3. Fallback match (language-only match)

    Args:
        requested: The desired locale
        available: Sequence of available locales

    Returns:
        Best matching locale or ``None``
    """
    if not available:
        return None

    # Exact match
    for loc in available:
        if loc.tag == requested.tag:
            return loc

    # Try fallback chain
    for fallback in requested.fallback_chain[1:]:
        for loc in available:
            if loc.tag == fallback.tag:
                return loc

    # Language-only prefix match
    for loc in available:
        if loc.language == requested.language:
            return loc

    return None


# ═══════════════════════════════════════════════════════════════════════════
# Accept-Language Parsing (RFC 4647)
# ═══════════════════════════════════════════════════════════════════════════

def parse_accept_language(header: str) -> List[Tuple[str, float]]:
    """
    Parse an ``Accept-Language`` header into a list of (tag, quality) tuples.

    Sorted by quality descending.

    Args:
        header: Raw Accept-Language header value

    Returns:
        List of ``(tag, quality)`` tuples sorted by quality

    Examples::

        >>> parse_accept_language("fr-CH, fr;q=0.9, en;q=0.8, *;q=0.5")
        [('fr-CH', 1.0), ('fr', 0.9), ('en', 0.8), ('*', 0.5)]
    """
    if not header:
        return []

    results: list[tuple[str, float]] = []
    for m in _ACCEPT_LANG_RE.finditer(header):
        tag = m.group("tag").strip()
        q_str = m.group("q")
        quality = float(q_str) if q_str else 1.0
        # Clamp quality to [0, 1]
        quality = max(0.0, min(1.0, quality))
        results.append((tag, quality))

    # Sort by quality descending, then by order of appearance
    results.sort(key=lambda x: -x[1])
    return results


def negotiate_locale(
    accept_language: str,
    available_locales: Sequence[str],
    default: str = "en",
) -> str:
    """
    Negotiate the best locale from an Accept-Language header and available locales.

    Implements a simplified version of RFC 4647 "Lookup" matching:
    1. Parse Accept-Language into quality-sorted list
    2. For each preferred tag, try to match against available locales
    3. Fall back to default if no match found

    Args:
        accept_language: Raw Accept-Language header value
        available_locales: List of locale tags the application supports
        default: Default locale tag if no match found

    Returns:
        Best matching locale tag string
    """
    if not accept_language or not available_locales:
        return default

    parsed = parse_accept_language(accept_language)
    available = [parse_locale(t) for t in available_locales]

    for tag, _quality in parsed:
        if tag == "*":
            return available_locales[0] if available_locales else default

        try:
            requested = parse_locale(tag)
        except ValueError:
            continue

        matched = match_locale(requested, available)
        if matched:
            return matched.tag

    return default
