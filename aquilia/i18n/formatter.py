"""
Message Formatter — ICU MessageFormat-inspired interpolation & locale formatting.

Provides:
- Named argument interpolation: ``"Hello, {name}!"``
- Plural selection: ``"{count, plural, one {# item} other {# items}}"``
- Select expressions: ``"{gender, select, male {He} female {She} other {They}}"``
- Number formatting: ``format_number(1234.5, "de")`` → ``"1.234,5"``
- Currency formatting: ``format_currency(9.99, "USD", "en")`` → ``"$9.99"``
- Date/time formatting with locale-aware patterns
- Ordinal formatting: ``format_ordinal(3, "en")`` → ``"3rd"``
- Percent formatting: ``format_percent(0.42, "en")`` → ``"42%"``

Zero external dependencies — uses locale data embedded in the module.
"""

from __future__ import annotations

import re
from datetime import date, datetime, time
from decimal import Decimal
from typing import Any, Dict, Optional, Union

from .plural import select_plural

Number = Union[int, float, Decimal]

# ═══════════════════════════════════════════════════════════════════════════
# Locale-specific formatting data
# ═══════════════════════════════════════════════════════════════════════════

_NUMBER_FORMATS: Dict[str, Dict[str, str]] = {
    # language → { decimal_sep, group_sep, group_size }
    "en": {"decimal": ".", "group": ",", "size": "3"},
    "de": {"decimal": ",", "group": ".", "size": "3"},
    "fr": {"decimal": ",", "group": "\u202f", "size": "3"},  # narrow no-break space
    "es": {"decimal": ",", "group": ".", "size": "3"},
    "it": {"decimal": ",", "group": ".", "size": "3"},
    "pt": {"decimal": ",", "group": ".", "size": "3"},
    "nl": {"decimal": ",", "group": ".", "size": "3"},
    "ru": {"decimal": ",", "group": "\u00a0", "size": "3"},  # no-break space
    "uk": {"decimal": ",", "group": "\u00a0", "size": "3"},
    "pl": {"decimal": ",", "group": "\u00a0", "size": "3"},
    "cs": {"decimal": ",", "group": "\u00a0", "size": "3"},
    "sk": {"decimal": ",", "group": "\u00a0", "size": "3"},
    "ro": {"decimal": ",", "group": ".", "size": "3"},
    "hu": {"decimal": ",", "group": "\u00a0", "size": "3"},
    "tr": {"decimal": ",", "group": ".", "size": "3"},
    "ar": {"decimal": "٫", "group": "٬", "size": "3"},
    "hi": {"decimal": ".", "group": ",", "size": "3"},  # Indian uses 2+3 but simplified
    "ja": {"decimal": ".", "group": ",", "size": "3"},
    "ko": {"decimal": ".", "group": ",", "size": "3"},
    "zh": {"decimal": ".", "group": ",", "size": "3"},
    "sv": {"decimal": ",", "group": "\u00a0", "size": "3"},
    "da": {"decimal": ",", "group": ".", "size": "3"},
    "fi": {"decimal": ",", "group": "\u00a0", "size": "3"},
    "nb": {"decimal": ",", "group": "\u00a0", "size": "3"},
    "nn": {"decimal": ",", "group": "\u00a0", "size": "3"},
    "el": {"decimal": ",", "group": ".", "size": "3"},
    "he": {"decimal": ".", "group": ",", "size": "3"},
    "th": {"decimal": ".", "group": ",", "size": "3"},
    "vi": {"decimal": ",", "group": ".", "size": "3"},
    "id": {"decimal": ",", "group": ".", "size": "3"},
    "ms": {"decimal": ".", "group": ",", "size": "3"},
}

_CURRENCY_SYMBOLS: Dict[str, str] = {
    "USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥", "CNY": "¥",
    "KRW": "₩", "INR": "₹", "RUB": "₽", "TRY": "₺", "BRL": "R$",
    "CAD": "CA$", "AUD": "A$", "CHF": "CHF", "SEK": "kr", "NOK": "kr",
    "DKK": "kr", "PLN": "zł", "CZK": "Kč", "HUF": "Ft", "RON": "lei",
    "THB": "฿", "PHP": "₱", "MXN": "MX$", "ZAR": "R", "SGD": "S$",
    "HKD": "HK$", "NZD": "NZ$", "ILS": "₪", "AED": "د.إ",
    "SAR": "﷼", "EGP": "E£", "NGN": "₦", "KES": "KSh",
    "MAD": "MAD", "TWD": "NT$", "MYR": "RM", "IDR": "Rp",
    "VND": "₫", "UAH": "₴", "BGN": "лв", "HRK": "kn",
}

# English ordinal suffixes
_ORDINAL_SUFFIXES_EN = {1: "st", 2: "nd", 3: "rd"}

# Date format patterns per locale
_DATE_FORMATS: Dict[str, Dict[str, str]] = {
    "en": {"short": "%m/%d/%Y", "medium": "%b %d, %Y", "long": "%B %d, %Y", "full": "%A, %B %d, %Y"},
    "en-US": {"short": "%m/%d/%Y", "medium": "%b %d, %Y", "long": "%B %d, %Y", "full": "%A, %B %d, %Y"},
    "en-GB": {"short": "%d/%m/%Y", "medium": "%d %b %Y", "long": "%d %B %Y", "full": "%A, %d %B %Y"},
    "de": {"short": "%d.%m.%Y", "medium": "%d. %b %Y", "long": "%d. %B %Y", "full": "%A, %d. %B %Y"},
    "fr": {"short": "%d/%m/%Y", "medium": "%d %b %Y", "long": "%d %B %Y", "full": "%A %d %B %Y"},
    "es": {"short": "%d/%m/%Y", "medium": "%d %b %Y", "long": "%d de %B de %Y", "full": "%A, %d de %B de %Y"},
    "it": {"short": "%d/%m/%Y", "medium": "%d %b %Y", "long": "%d %B %Y", "full": "%A %d %B %Y"},
    "pt": {"short": "%d/%m/%Y", "medium": "%d de %b de %Y", "long": "%d de %B de %Y", "full": "%A, %d de %B de %Y"},
    "nl": {"short": "%d-%m-%Y", "medium": "%d %b %Y", "long": "%d %B %Y", "full": "%A %d %B %Y"},
    "ru": {"short": "%d.%m.%Y", "medium": "%d %b %Y г.", "long": "%d %B %Y г.", "full": "%A, %d %B %Y г."},
    "ja": {"short": "%Y/%m/%d", "medium": "%Y年%m月%d日", "long": "%Y年%m月%d日", "full": "%Y年%m月%d日(%A)"},
    "ko": {"short": "%Y. %m. %d.", "medium": "%Y년 %m월 %d일", "long": "%Y년 %m월 %d일", "full": "%Y년 %m월 %d일 %A"},
    "zh": {"short": "%Y/%m/%d", "medium": "%Y年%m月%d日", "long": "%Y年%m月%d日", "full": "%Y年%m月%d日%A"},
    "ar": {"short": "%d/%m/%Y", "medium": "%d %b %Y", "long": "%d %B %Y", "full": "%A، %d %B %Y"},
}

_TIME_FORMATS: Dict[str, Dict[str, str]] = {
    "en": {"short": "%I:%M %p", "medium": "%I:%M:%S %p", "long": "%I:%M:%S %p %Z"},
    "en-US": {"short": "%I:%M %p", "medium": "%I:%M:%S %p", "long": "%I:%M:%S %p %Z"},
    "en-GB": {"short": "%H:%M", "medium": "%H:%M:%S", "long": "%H:%M:%S %Z"},
    "de": {"short": "%H:%M", "medium": "%H:%M:%S", "long": "%H:%M:%S %Z"},
    "fr": {"short": "%H:%M", "medium": "%H:%M:%S", "long": "%H:%M:%S %Z"},
    "ja": {"short": "%H:%M", "medium": "%H:%M:%S", "long": "%H時%M分%S秒"},
}


# ═══════════════════════════════════════════════════════════════════════════
# Message Formatter
# ═══════════════════════════════════════════════════════════════════════════

# Pattern: {name} or {name, type, style_with_braces}
# Uses a function-based approach for nested brace handling
_SIMPLE_ARG_PATTERN = re.compile(r"\{(\w+)\}")

# Plural sub-pattern: one {# item} other {# items}
_PLURAL_FORM_PATTERN = re.compile(r"(=\d+|\w+)\s*\{([^}]*)\}")


def _find_icu_args(pattern: str):
    """
    Find ICU-style arguments in a pattern, handling nested braces.

    Yields (start, end, name, arg_type, style) tuples.
    """
    i = 0
    n = len(pattern)
    while i < n:
        if pattern[i] == '{':
            # Find the argument name
            j = i + 1
            while j < n and (pattern[j].isalnum() or pattern[j] == '_'):
                j += 1

            name = pattern[i + 1:j]
            if not name:
                i += 1
                continue

            # Check for comma (typed argument)
            while j < n and pattern[j] == ' ':
                j += 1

            if j < n and pattern[j] == ',':
                # Typed argument: {name, type, ...}
                j += 1
                while j < n and pattern[j] == ' ':
                    j += 1

                # Read type
                type_start = j
                while j < n and pattern[j].isalnum():
                    j += 1
                arg_type = pattern[type_start:j]

                while j < n and pattern[j] == ' ':
                    j += 1

                style = None
                if j < n and pattern[j] == ',':
                    # Read style (rest until matching closing brace)
                    j += 1
                    while j < n and pattern[j] == ' ':
                        j += 1
                    style_start = j
                    depth = 1
                    while j < n and depth > 0:
                        if pattern[j] == '{':
                            depth += 1
                        elif pattern[j] == '}':
                            depth -= 1
                        j += 1
                    style = pattern[style_start:j - 1].strip()
                elif j < n and pattern[j] == '}':
                    j += 1
                else:
                    i += 1
                    continue

                yield (i, j, name, arg_type, style)
            elif j < n and pattern[j] == '}':
                # Simple argument: {name}
                j += 1
                yield (i, j, name, None, None)
            else:
                i += 1
                continue

            i = j
        else:
            i += 1


class MessageFormatter:
    """
    ICU MessageFormat-inspired string formatter.

    Supports:
    - Simple interpolation: ``{name}``
    - Plural: ``{count, plural, one {# item} other {# items}}``
    - Select: ``{gender, select, male {He} female {She} other {They}}``
    - Number: ``{price, number}``

    The ``#`` symbol in plural forms is replaced with the formatted count.

    Args:
        locale: Default locale for formatting

    Example::

        fmt = MessageFormatter("en")
        fmt.format("Hello, {name}!", name="World")
        # → "Hello, World!"

        fmt.format("{count, plural, one {# item} other {# items}}", count=5)
        # → "5 items"
    """

    def __init__(self, locale: str = "en"):
        self.locale = locale

    def format(self, pattern: str, locale: Optional[str] = None, **kwargs: Any) -> str:
        """
        Format a message pattern with the given arguments.

        Args:
            pattern: ICU-style message pattern
            locale: Override locale (optional)
            **kwargs: Named arguments for interpolation

        Returns:
            Formatted string
        """
        loc = locale or self.locale

        # Process ICU arguments from right to left to preserve indices
        args = list(_find_icu_args(pattern))
        args.reverse()

        result = pattern
        for start, end, name, arg_type, style in args:
            value = kwargs.get(name)
            if value is None:
                continue  # Leave unreplaced

            if arg_type is None:
                # Simple interpolation
                replacement = str(value)
            elif arg_type == "plural":
                replacement = self._format_plural(value, style or "", loc)
            elif arg_type == "select":
                replacement = self._format_select(value, style or "")
            elif arg_type == "number":
                replacement = format_number(value, loc)
            elif arg_type == "currency":
                currency_code = style or "USD"
                replacement = format_currency(value, currency_code, loc)
            elif arg_type == "date":
                replacement = format_date(value, loc, style=style or "medium")
            elif arg_type == "time":
                replacement = format_time(value, loc, style=style or "short")
            else:
                replacement = str(value)

            result = result[:start] + replacement + result[end:]

        return result

    def _format_plural(self, count: Number, style: str, locale: str) -> str:
        """Format a plural expression."""
        category = select_plural(locale, count)

        # Parse plural forms: one {# item} other {# items}
        forms: dict[str, str] = {}
        for m in _PLURAL_FORM_PATTERN.finditer(style):
            forms[m.group(1)] = m.group(2)

        # Try exact match (=0, =1, etc.)
        exact_key = f"={int(count)}" if isinstance(count, (int, float)) and count == int(count) else None
        if exact_key and exact_key in forms:
            template = forms[exact_key]
        elif category in forms:
            template = forms[category]
        elif "other" in forms:
            template = forms["other"]
        else:
            template = str(count)

        # Replace # with formatted number
        formatted_count = format_number(count, locale)
        return template.replace("#", formatted_count)

    def _format_select(self, value: Any, style: str) -> str:
        """Format a select expression."""
        forms: dict[str, str] = {}
        for m in _PLURAL_FORM_PATTERN.finditer(style):
            forms[m.group(1)] = m.group(2)

        str_value = str(value)
        if str_value in forms:
            return forms[str_value]
        return forms.get("other", str_value)


def format_message(pattern: str, locale: str = "en", **kwargs: Any) -> str:
    """
    Convenience function for one-shot message formatting.

    Args:
        pattern: ICU-style message pattern
        locale: Locale for formatting
        **kwargs: Named arguments

    Returns:
        Formatted string
    """
    return MessageFormatter(locale).format(pattern, locale=locale, **kwargs)


# ═══════════════════════════════════════════════════════════════════════════
# Number Formatting
# ═══════════════════════════════════════════════════════════════════════════

def _get_number_format(locale: str) -> Dict[str, str]:
    """Get number formatting rules for a locale with fallback."""
    if locale in _NUMBER_FORMATS:
        return _NUMBER_FORMATS[locale]
    # Try language-only
    lang = locale.split("-")[0]
    if lang in _NUMBER_FORMATS:
        return _NUMBER_FORMATS[lang]
    return _NUMBER_FORMATS["en"]


def format_number(value: Number, locale: str = "en", *, decimals: Optional[int] = None) -> str:
    """
    Format a number with locale-specific separators.

    Args:
        value: Number to format
        locale: BCP 47 locale tag
        decimals: Fixed decimal places (None = auto)

    Returns:
        Formatted number string

    Examples::

        >>> format_number(1234567.89, "en")
        '1,234,567.89'
        >>> format_number(1234567.89, "de")
        '1.234.567,89'
        >>> format_number(1234567.89, "fr")
        '1 234 567,89'
    """
    fmt = _get_number_format(locale)
    decimal_sep = fmt["decimal"]
    group_sep = fmt["group"]
    group_size = int(fmt["size"])

    if decimals is not None:
        value = round(float(value), decimals)

    # Split integer and fraction parts
    abs_val = abs(float(value))
    negative = float(value) < 0

    if decimals is not None:
        formatted = f"{abs_val:.{decimals}f}"
    else:
        formatted = f"{abs_val:f}".rstrip("0").rstrip(".")
        # If it's an integer, no decimal
        if abs_val == int(abs_val) and decimals is None:
            formatted = str(int(abs_val))

    parts = formatted.split(".")
    integer_part = parts[0]
    fraction_part = parts[1] if len(parts) > 1 else ""

    # Apply grouping
    if group_sep and len(integer_part) > group_size:
        groups = []
        while len(integer_part) > group_size:
            groups.insert(0, integer_part[-group_size:])
            integer_part = integer_part[:-group_size]
        if integer_part:
            groups.insert(0, integer_part)
        integer_part = group_sep.join(groups)

    result = integer_part
    if fraction_part:
        result += decimal_sep + fraction_part

    if negative:
        result = "-" + result

    return result


def format_decimal(value: Number, locale: str = "en", decimals: int = 2) -> str:
    """Format a decimal number with fixed precision."""
    return format_number(value, locale, decimals=decimals)


def format_percent(value: Number, locale: str = "en", decimals: int = 0) -> str:
    """
    Format a fraction as a percentage.

    Args:
        value: Fraction (0.42 → 42%)
        locale: Locale
        decimals: Decimal places

    Returns:
        Formatted percentage string
    """
    pct = float(value) * 100
    num_str = format_number(pct, locale, decimals=decimals)
    return f"{num_str}%"


def format_currency(
    value: Number,
    currency: str = "USD",
    locale: str = "en",
    *,
    decimals: int = 2,
) -> str:
    """
    Format a monetary value with currency symbol.

    Args:
        value: Amount
        currency: ISO 4217 currency code
        locale: Locale
        decimals: Decimal places

    Returns:
        Formatted currency string

    Examples::

        >>> format_currency(9.99, "USD", "en")
        '$9.99'
        >>> format_currency(9.99, "EUR", "de")
        '9,99 €'
    """
    symbol = _CURRENCY_SYMBOLS.get(currency.upper(), currency)
    num_str = format_number(value, locale, decimals=decimals)

    lang = locale.split("-")[0]
    # Symbol placement: before for en, ja, zh, ko, etc.  After for de, fr, etc.
    symbol_after = lang in ("de", "fr", "es", "it", "pt", "nl", "ru", "pl", "cs", "sk",
                            "hu", "ro", "sv", "da", "fi", "nb", "nn", "el", "tr", "vi")
    if symbol_after:
        return f"{num_str}\u00a0{symbol}"  # no-break space
    return f"{symbol}{num_str}"


def format_ordinal(value: int, locale: str = "en") -> str:
    """
    Format an ordinal number.

    Args:
        value: Integer
        locale: Locale

    Returns:
        Ordinal string (e.g. ``"3rd"`` for English)
    """
    lang = locale.split("-")[0]

    if lang == "en":
        if 11 <= (value % 100) <= 13:
            suffix = "th"
        else:
            suffix = _ORDINAL_SUFFIXES_EN.get(value % 10, "th")
        return f"{value}{suffix}"
    elif lang == "fr":
        return f"{value}{'er' if value == 1 else 'e'}"
    elif lang == "de":
        return f"{value}."
    elif lang == "es":
        return f"{value}.º"
    elif lang == "it":
        return f"{value}°"
    elif lang in ("ru", "uk"):
        return f"{value}-й"
    elif lang in ("ja", "ko", "zh"):
        return f"第{value}"
    else:
        return f"{value}."


# ═══════════════════════════════════════════════════════════════════════════
# Date/Time Formatting
# ═══════════════════════════════════════════════════════════════════════════

def format_date(
    value: date,
    locale: str = "en",
    *,
    style: str = "medium",
) -> str:
    """
    Format a date with locale-specific patterns.

    Args:
        value: Date or datetime object
        locale: BCP 47 locale tag
        style: Format style — ``"short"``, ``"medium"``, ``"long"``, ``"full"``

    Returns:
        Formatted date string
    """
    formats = _DATE_FORMATS.get(locale) or _DATE_FORMATS.get(locale.split("-")[0]) or _DATE_FORMATS["en"]
    pattern = formats.get(style, formats["medium"])

    try:
        return value.strftime(pattern)
    except (ValueError, AttributeError):
        return str(value)


def format_time(
    value: Union[time, datetime],
    locale: str = "en",
    *,
    style: str = "short",
) -> str:
    """
    Format a time with locale-specific patterns.

    Args:
        value: Time or datetime object
        locale: BCP 47 locale tag
        style: Format style — ``"short"``, ``"medium"``, ``"long"``

    Returns:
        Formatted time string
    """
    formats = _TIME_FORMATS.get(locale) or _TIME_FORMATS.get(locale.split("-")[0]) or _TIME_FORMATS["en"]
    pattern = formats.get(style, formats["short"])

    try:
        return value.strftime(pattern)
    except (ValueError, AttributeError):
        return str(value)


def format_datetime(
    value: datetime,
    locale: str = "en",
    *,
    date_style: str = "medium",
    time_style: str = "short",
    separator: str = " ",
) -> str:
    """
    Format a datetime with locale-specific patterns.

    Args:
        value: Datetime object
        locale: BCP 47 locale tag
        date_style: Date format style
        time_style: Time format style
        separator: Separator between date and time parts

    Returns:
        Formatted datetime string
    """
    d = format_date(value, locale, style=date_style)
    t = format_time(value, locale, style=time_style)
    return f"{d}{separator}{t}"
