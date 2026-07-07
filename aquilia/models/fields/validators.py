"""
Aquilia Field Validators -- reusable validation callables.

Provides a library of production-grade validators that can be
attached to any field via the ``validators=[...]`` parameter.

Usage:
    from aquilia.models.fields.validators import (
        MinValueValidator, MaxValueValidator, MinLengthValidator,
        RegexValidator, EmailValidator, URLValidator,
    )

    class Product(Model):
        price = DecimalField(validators=[MinValueValidator(0)])
        sku = CharField(max_length=20, validators=[
            RegexValidator(r'^[A-Z]{2}-\\d{4}$', "Invalid SKU format"),
        ])
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from decimal import Decimal
from typing import Any

__all__ = [
    "BaseValidator",
    "MinValueValidator",
    "MaxValueValidator",
    "MinLengthValidator",
    "MaxLengthValidator",
    "RegexValidator",
    "EmailValidator",
    "URLValidator",
    "SlugValidator",
    "ProhibitNullCharactersValidator",
    "DecimalValidator",
    "FileExtensionValidator",
    "StepValueValidator",
    "RangeValidator",
    "UniqueForDateValidator",
]


class ValidationError(ValueError):
    """
    Raised by validators when a value fails validation.

    Args:
        message: Human-readable description of the failure.
        code: Stable, machine-readable error code (e.g. ``"min_value"``,
            ``"invalid_email"``) suitable for i18n lookups or API error
            payloads. Defaults to ``"invalid"``.
        params: Optional dict of extra context (e.g. the offending limit)
            for callers that want to format their own message.
    """

    def __init__(self, message: str, code: str = "invalid", params: dict | None = None):
        self.message = message
        self.code = code
        self.params = params or {}
        super().__init__(message)


class BaseValidator:
    """
    Base class for all field validators.

    A validator is a callable: ``validator(value)`` raises
    ``ValidationError`` when ``value`` is invalid and returns ``None``
    (does nothing) when it's valid. Field code invokes each validator in
    ``field.validators`` this way during ``Field.validate()``.

    Subclasses typically only need to override ``is_valid()`` (and
    optionally ``get_message()`` for a value-dependent message) -- the
    ``__call__``/equality/repr plumbing here is shared.

    Class attributes:
        message: Default human-readable error message, used when the
            caller doesn't supply a custom one.
        code: Stable machine-readable error code exposed as
            ``ValidationError.code``.

    Two validator instances compare equal (``==``) when they are the same
    class and have identical configuration (``__dict__``), which lets
    migration/deconstruct diffing detect unchanged validators.
    """

    message: str = "Invalid value."
    code: str = "invalid"

    def __call__(self, value: Any) -> None:
        """
        Validate ``value``, raising ``ValidationError`` if it's invalid.

        Args:
            value: The value to check.

        Raises:
            ValidationError: If ``is_valid(value)`` is falsy. The message
                comes from ``get_message(value)`` and the error's
                ``code`` is this validator's ``code``.
        """
        if not self.is_valid(value):
            raise ValidationError(self.get_message(value), code=self.code)

    def is_valid(self, value: Any) -> bool:
        """Override in subclasses. Return True if value is valid."""
        return True

    def get_message(self, value: Any) -> str:
        """Return the error message for an invalid ``value``.

        Base implementation returns the static ``self.message``. Most
        subclasses override this to build a message that embeds their
        specific configuration (a limit, a length, etc.), falling back
        to ``self.message`` only when the caller supplied a custom one.
        """
        return self.message

    def __eq__(self, other: Any) -> bool:
        """Equal when ``other`` is the same class with identical configuration."""
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __repr__(self) -> str:
        """Debug representation, e.g. ``<BaseValidator>``."""
        return f"<{self.__class__.__name__}>"


class MinValueValidator(BaseValidator):
    """
    Validate that a numeric value is greater than or equal to a limit.

    ``None`` is always considered valid here -- combine with a non-null
    field (``null=False``) if ``None`` should itself be rejected.

    Args:
        limit_value: Inclusive lower bound. Any type supporting ``>=``
            against the values being validated (``int``, ``float``,
            ``Decimal``, ...).
        message: Optional message overriding the default "Ensure this
            value is greater than or equal to {limit_value}."

    Example:
        price = DecimalField(validators=[MinValueValidator(0)])
    """

    code = "min_value"

    def __init__(self, limit_value: int | float | Decimal, message: str | None = None):
        self.limit_value = limit_value
        if message:
            self.message = message

    def is_valid(self, value: Any) -> bool:
        """Return True if ``value`` is ``None`` or ``value >= limit_value``."""
        if value is None:
            return True
        return value >= self.limit_value

    def get_message(self, value: Any) -> str:
        """Return the custom message if supplied, else the default lower-bound message."""
        return (
            self.message
            if hasattr(self, "message") and self.message != "Invalid value."
            else (f"Ensure this value is greater than or equal to {self.limit_value}.")
        )

    def __repr__(self) -> str:
        """Debug representation, e.g. ``MinValueValidator(0)``."""
        return f"MinValueValidator({self.limit_value})"


class MaxValueValidator(BaseValidator):
    """
    Validate that a numeric value is less than or equal to a limit.

    ``None`` is always considered valid here -- combine with a non-null
    field (``null=False``) if ``None`` should itself be rejected.

    Args:
        limit_value: Inclusive upper bound. Any type supporting ``<=``
            against the values being validated (``int``, ``float``,
            ``Decimal``, ...).
        message: Optional message overriding the default "Ensure this
            value is less than or equal to {limit_value}."

    Example:
        rating = IntegerField(validators=[MaxValueValidator(5)])
    """

    code = "max_value"

    def __init__(self, limit_value: int | float | Decimal, message: str | None = None):
        self.limit_value = limit_value
        if message:
            self.message = message

    def is_valid(self, value: Any) -> bool:
        """Return True if ``value`` is ``None`` or ``value <= limit_value``."""
        if value is None:
            return True
        return value <= self.limit_value

    def get_message(self, value: Any) -> str:
        """Return the custom message if supplied, else the default upper-bound message."""
        return (
            self.message
            if hasattr(self, "message") and self.message != "Invalid value."
            else (f"Ensure this value is less than or equal to {self.limit_value}.")
        )

    def __repr__(self) -> str:
        """Debug representation, e.g. ``MaxValueValidator(5)``."""
        return f"MaxValueValidator({self.limit_value})"


class MinLengthValidator(BaseValidator):
    """
    Validate that a value's length is at least ``limit_value``.

    ``None`` is always considered valid. The value must support ``len()``
    (strings, lists, etc.).

    Args:
        limit_value: Minimum required length.
        message: Optional message overriding the default "Ensure this
            value has at least {limit_value} character(s) ...".
    """

    code = "min_length"

    def __init__(self, limit_value: int, message: str | None = None):
        self.limit_value = limit_value
        if message:
            self.message = message

    def is_valid(self, value: Any) -> bool:
        """Return True if ``value`` is ``None`` or ``len(value) >= limit_value``."""
        if value is None:
            return True
        return len(value) >= self.limit_value

    def get_message(self, value: Any) -> str:
        """Return the custom message if supplied, else the default min-length message
        (including the actual length of ``value``, or 0 if falsy)."""
        return (
            self.message
            if hasattr(self, "message") and self.message != "Invalid value."
            else (
                f"Ensure this value has at least {self.limit_value} character(s) (it has {len(value) if value else 0})."
            )
        )

    def __repr__(self) -> str:
        """Debug representation, e.g. ``MinLengthValidator(3)``."""
        return f"MinLengthValidator({self.limit_value})"


class MaxLengthValidator(BaseValidator):
    """
    Validate that a value's length is at most ``limit_value``.

    ``None`` is always considered valid. The value must support ``len()``
    (strings, lists, etc.).

    Args:
        limit_value: Maximum allowed length.
        message: Optional message overriding the default "Ensure this
            value has at most {limit_value} character(s) ...".
    """

    code = "max_length"

    def __init__(self, limit_value: int, message: str | None = None):
        self.limit_value = limit_value
        if message:
            self.message = message

    def is_valid(self, value: Any) -> bool:
        """Return True if ``value`` is ``None`` or ``len(value) <= limit_value``."""
        if value is None:
            return True
        return len(value) <= self.limit_value

    def get_message(self, value: Any) -> str:
        """Return the custom message if supplied, else the default max-length message
        (including the actual length of ``value``, or 0 if falsy)."""
        return (
            self.message
            if hasattr(self, "message") and self.message != "Invalid value."
            else (
                f"Ensure this value has at most {self.limit_value} character(s) (it has {len(value) if value else 0})."
            )
        )


class RegexValidator(BaseValidator):
    """
    Validate a value against a regular expression.

    Also the base class for the common format validators below
    (``EmailValidator``, ``URLValidator``, ``SlugValidator``).

    Args:
        regex: Pattern string, compiled once at construction time via
            ``re.compile(regex, flags)``.
        message: Optional message overriding the default "Enter a valid
            value."
        code: Optional error code overriding the default ``"invalid"``.
        inverse_match: If True, validation succeeds when the pattern does
            *not* match -- useful for "must not contain X" rules. Default
            ``False`` requires a match to succeed.
        flags: Optional ``re`` flags (e.g. ``re.IGNORECASE``) passed to
            ``re.compile``.

    Matching uses ``re.search`` (not ``re.match``/``re.fullmatch``), so an
    unanchored pattern can match anywhere in the string -- anchor with
    ``^``/``$`` if the whole value must conform.
    """

    code = "invalid"

    def __init__(
        self,
        regex: str,
        message: str | None = None,
        code: str | None = None,
        inverse_match: bool = False,
        flags: int = 0,
    ):
        self.regex = regex
        self._compiled = re.compile(regex, flags)
        self.inverse_match = inverse_match
        if message:
            self.message = message
        if code:
            self.code = code

    def is_valid(self, value: Any) -> bool:
        """
        Return True if ``value`` (coerced to ``str``) matches the pattern,
        or does not match when ``inverse_match=True``. ``None`` is always
        valid.
        """
        if value is None:
            return True
        value = str(value)
        matched = bool(self._compiled.search(value))
        return not matched if self.inverse_match else matched

    def get_message(self, value: Any) -> str:
        """Return the custom message if supplied, else "Enter a valid value."."""
        return (
            self.message if hasattr(self, "message") and self.message != "Invalid value." else ("Enter a valid value.")
        )

    def __repr__(self) -> str:
        """Debug representation, e.g. ``RegexValidator('^\\d+$')``."""
        return f"RegexValidator({self.regex!r})"


class EmailValidator(RegexValidator):
    """
    Validate that a value looks like a syntactically valid email address.

    Built on ``RegexValidator`` with a pattern covering the common
    ``local-part@domain`` shape. This is a syntax check only -- it does
    not verify that the domain exists or accepts mail.

    Args:
        message: Optional message overriding the default "Enter a valid
            email address."
    """

    _EMAIL_RE = (
        r"^[a-zA-Z0-9.!#$%&\'*+/=?^_`{|}~-]+@"
        r"[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?"
        r"(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$"
    )

    def __init__(self, message: str | None = None):
        super().__init__(
            self._EMAIL_RE,
            message=message or "Enter a valid email address.",
            code="invalid_email",
        )


class URLValidator(RegexValidator):
    """
    Validate that a value looks like a syntactically valid HTTP(S) URL.

    Args:
        message: Optional message overriding the default "Enter a valid
            URL."
        schemes: Stored on ``self.schemes`` for introspection, but *not*
            currently enforced -- the underlying regex only ever matches
            ``http://``/``https://`` regardless of what is passed here.
            Defaults to ``["http", "https"]``.
    """

    _URL_RE = (
        r"^https?://"
        r"(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*"
        r"[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?"
        r"(?::\d+)?"
        r"(?:/[^\s]*)?$"
    )

    def __init__(self, message: str | None = None, schemes: Sequence[str] | None = None):
        self.schemes = schemes or ["http", "https"]
        super().__init__(
            self._URL_RE,
            message=message or "Enter a valid URL.",
            code="invalid_url",
        )


class SlugValidator(RegexValidator):
    """
    Validate that a value contains only slug-safe characters: letters,
    numbers, hyphens, and underscores (``^[-a-zA-Z0-9_]+$``).

    Args:
        message: Optional message overriding the default "Enter a valid
            slug (letters, numbers, hyphens, underscores)."
    """

    def __init__(self, message: str | None = None):
        super().__init__(
            r"^[-a-zA-Z0-9_]+$",
            message=message or "Enter a valid slug (letters, numbers, hyphens, underscores).",
            code="invalid_slug",
        )


class ProhibitNullCharactersValidator(BaseValidator):
    """
    Reject strings containing NUL (``\\x00``) characters.

    Useful as a defense-in-depth guard on text fields before values reach
    a database driver or downstream system that may mishandle embedded
    NULs. ``None`` is always valid.
    """

    code = "null_characters_not_allowed"
    message = "Null characters are not allowed."

    def is_valid(self, value: Any) -> bool:
        """Return True if ``value`` is ``None`` or (as ``str``) contains no ``\\x00``."""
        if value is None:
            return True
        return "\x00" not in str(value)


class DecimalValidator(BaseValidator):
    """
    Validate that a value fits within a decimal's precision and scale.

    Mirrors typical SQL ``DECIMAL(max_digits, decimal_places)`` semantics:
    ``max_digits`` is the total number of significant digits allowed
    (both sides of the decimal point combined), and ``decimal_places`` is
    how many of those may fall after the decimal point.

    Args:
        max_digits: Total number of digits allowed.
        decimal_places: Number of digits allowed after the decimal point.
        message: Optional message overriding the default precision/scale
            message.

    ``None`` is always valid. A value that can't be converted to
    ``Decimal`` (via ``Decimal(str(value))``) is treated as invalid
    rather than raising -- ``is_valid`` itself never raises.
    """

    code = "invalid_decimal"

    def __init__(self, max_digits: int, decimal_places: int, message: str | None = None):
        self.max_digits = max_digits
        self.decimal_places = decimal_places
        if message:
            self.message = message

    def is_valid(self, value: Any) -> bool:
        """
        Return True if ``value`` fits within ``max_digits`` total digits
        and ``decimal_places`` fractional digits.

        Whole-number digits allowed = ``max_digits - decimal_places``.
        Returns False (never raises) if ``value`` can't be converted to
        ``Decimal``.
        """
        if value is None:
            return True
        try:
            d = Decimal(str(value))
        except Exception:
            return False
        sign, digits, exponent = d.as_tuple()
        num_digits = len(digits)
        decimals = -exponent if exponent < 0 else 0
        whole_digits = num_digits - decimals
        return whole_digits <= (self.max_digits - self.decimal_places) and decimals <= self.decimal_places

    def get_message(self, value: Any) -> str:
        """Return the custom message if supplied, else the default precision/scale message."""
        return (
            self.message
            if hasattr(self, "message") and self.message != "Invalid value."
            else (
                f"Ensure there are no more than {self.max_digits} digits total "
                f"and {self.decimal_places} decimal places."
            )
        )


class FileExtensionValidator(BaseValidator):
    """
    Validate a filename's extension against an allow-list.

    Args:
        allowed_extensions: Extensions to accept, e.g. ``["jpg", "png"]``
            or ``[".JPG", ".png"]`` -- each is normalized (lowercased,
            leading dot stripped) at construction time, so either form
            may be passed.
        message: Optional message overriding the default "File extension
            not allowed" message.

    Comparison is case-insensitive. A value with no ``.`` in it is
    treated as having an empty extension, which fails unless ``""`` is
    itself in ``allowed_extensions``. ``None`` is always valid.
    """

    code = "invalid_extension"

    def __init__(
        self,
        allowed_extensions: Sequence[str],
        message: str | None = None,
    ):
        self.allowed_extensions = [ext.lower().lstrip(".") for ext in allowed_extensions]
        if message:
            self.message = message

    def is_valid(self, value: Any) -> bool:
        """Return True if ``value`` is ``None`` or its extension (lowercased,
        without the leading dot) is in ``allowed_extensions``."""
        if value is None:
            return True
        ext = str(value).rsplit(".", 1)[-1].lower() if "." in str(value) else ""
        return ext in self.allowed_extensions

    def get_message(self, value: Any) -> str:
        """Return the custom message if supplied, else a message listing the allowed extensions."""
        return (
            self.message
            if hasattr(self, "message") and self.message != "Invalid value."
            else (f"File extension not allowed. Allowed: {', '.join(self.allowed_extensions)}.")
        )


class StepValueValidator(BaseValidator):
    """
    Validate that a value is a multiple of ``step``, measured from ``offset``.

    Mirrors HTML ``<input step>`` semantics: valid values are
    ``offset, offset + step, offset + 2*step, ...``. Comparisons use
    ``Decimal(str(value))`` arithmetic to avoid binary floating-point
    rounding artifacts.

    Args:
        step: The increment values must align to.
        offset: Baseline values are measured from (default 0).
        message: Optional message overriding the default "multiple of
            {step}" message.

    ``None`` is always valid.
    """

    code = "invalid_step"

    def __init__(
        self,
        step: int | float | Decimal,
        offset: int | float | Decimal = 0,
        message: str | None = None,
    ):
        self.step = step
        self.offset = offset
        if message:
            self.message = message

    def is_valid(self, value: Any) -> bool:
        """Return True if ``value`` is ``None`` or ``(value - offset) % step == 0``
        (computed via ``Decimal``)."""
        if value is None:
            return True
        return (Decimal(str(value)) - Decimal(str(self.offset))) % Decimal(str(self.step)) == 0

    def get_message(self, value: Any) -> str:
        """Return the custom message if supplied, else the default "multiple of {step}" message."""
        return (
            self.message
            if hasattr(self, "message") and self.message != "Invalid value."
            else (f"Ensure this value is a multiple of {self.step}.")
        )


class RangeValidator(BaseValidator):
    """
    Validate that a value falls within an inclusive ``[min_val, max_val]`` range.

    Unlike combining ``MinValueValidator`` + ``MaxValueValidator``, this is
    a single validator with both bounds optional: pass only ``min_val``
    for a lower-bound-only check, only ``max_val`` for an upper-bound-only
    check, or both for a full range.

    Args:
        min_val: Inclusive lower bound, or ``None`` for no lower bound.
        max_val: Inclusive upper bound, or ``None`` for no upper bound.
        message: Optional message overriding the default range message.

    ``None`` (the value being validated) is always considered valid.
    """

    code = "out_of_range"

    def __init__(
        self,
        min_val: int | float | Decimal | None = None,
        max_val: int | float | Decimal | None = None,
        message: str | None = None,
    ):
        self.min_val = min_val
        self.max_val = max_val
        if message:
            self.message = message

    def is_valid(self, value: Any) -> bool:
        """Return True if ``value`` is ``None``, or lies within whichever of
        ``min_val``/``max_val`` are set."""
        if value is None:
            return True
        if self.min_val is not None and value < self.min_val:
            return False
        return not (self.max_val is not None and value > self.max_val)

    def get_message(self, value: Any) -> str:
        """Return the custom message if supplied, else the default range message."""
        return (
            self.message
            if hasattr(self, "message") and self.message != "Invalid value."
            else (f"Ensure this value is between {self.min_val} and {self.max_val}.")
        )


class UniqueForDateValidator(BaseValidator):
    """
    Placeholder validator declaring "unique within a date scope" intent
    (e.g. a slug that must be unique per publish date).

    This is a placeholder -- actual enforcement requires DB-level checks.
    ``is_valid`` always returns True; the validator exists so the
    constraint can be declared and introspected (e.g. by migrations or
    admin tooling), but no uniqueness query is performed here. Real
    enforcement needs a composite UNIQUE constraint or an explicit
    pre-insert query at the database layer.

    Args:
        date_field: Name of the date field defining the uniqueness scope.
        message: Optional message (currently unused, since validation
            always succeeds).
    """

    code = "unique_for_date"

    def __init__(self, date_field: str, message: str | None = None):
        self.date_field = date_field
        if message:
            self.message = message

    def is_valid(self, value: Any) -> bool:
        """Always returns True -- see class docstring; real enforcement happens at the DB level."""
        # Placeholder -- real uniqueness check happens at the DB level
        return True
