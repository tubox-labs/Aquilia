"""
Aquilia Contract Messages -- localizable validation text.

Every validation message the Contracts subsystem produces passes through
:func:`contract_message`. When an :class:`~aquilia.i18n.I18nService` is active
for the current request, the message is resolved from the translation catalog
under ``contracts.<key>``; otherwise the built-in English default is formatted
directly.

This means an application that never configures i18n sees byte-identical
messages to previous releases, while one that does gets fully localized
validation errors without touching any Contract code.

Catalog keys use the ``contracts.`` namespace::

    {
      "contracts": {
        "required": "Este campo es obligatorio",
        "min_length": "Debe tener al menos {min} caracteres"
      }
    }

Placeholders are ICU-style (``{name}``), matching the rest of Aquilia's i18n.
"""

from __future__ import annotations

from typing import Any

__all__ = ["DEFAULT_MESSAGES", "contract_message"]


# Built-in English text, keyed by message id. These double as the format
# patterns used when no i18n service is active, so their wording is part of the
# public API — existing tests and client-side error matching depend on it.
DEFAULT_MESSAGES: dict[str, str] = {
    # Structural
    "required": "This field is required",
    "not_null": "This field may not be null",
    "expected_object": "Expected an object, got {type}",
    "expected_dict": "Expected a dictionary",
    "expected_list": "Expected a list of items",
    "unknown_field": "Unknown field '{field}' is not allowed",
    "invalid_type": "Invalid type: expected {expected}",
    "nesting_depth": "Nested Contract depth exceeds maximum of {max}",
    # Text
    "min_length": "Must be at least {min} characters",
    "max_length": "Must be at most {max} characters",
    "blank": "This field may not be blank",
    "pattern": "Invalid format",
    "invalid_email": "Invalid email address",
    "invalid_url": "Invalid URL",
    "invalid_slug": "Invalid slug (use letters, numbers, hyphens, underscores)",
    "invalid_ip": "Invalid IP address",
    "invalid_mac": "Invalid MAC address",
    "invalid_uuid": "Invalid UUID",
    # Numeric
    "min_value": "Must be at least {min}",
    "max_value": "Must be at most {max}",
    "min_bytes": "Must be at least {min} bytes",
    "max_bytes": "Must be at most {max} bytes",
    "multiple_of": "Must be a multiple of {multiple}",
    "not_an_integer": "Must be an integer",
    "not_a_number": "Must be a number",
    # Collections
    "min_items": "Must contain at least {min} items",
    "max_items": "Must contain at most {max} items",
    "not_unique": "Items must be unique",
    # Choice
    "invalid_choice": "Not a valid choice",
    # Paths
    "path_not_relative": "Path must be relative",
    "path_traversal": "Path may not contain '..' segments",
    "path_null_byte": "Path may not contain null bytes",
    "path_empty": "Path may not be empty",
}


def contract_message(key: str, /, **params: Any) -> str:
    """
    Resolve a validation message, localized when an i18n service is active.

    Args:
        key: Message id — a key of :data:`DEFAULT_MESSAGES`.
        **params: Interpolation values for the message's ICU placeholders.

    Returns:
        The localized message when a request-scoped
        :class:`~aquilia.i18n.I18nService` is available, otherwise the built-in
        English text with ``params`` substituted.

    Examples:
        >>> contract_message("min_length", min=8)
        'Must be at least 8 characters'

    Notes:
        Resolution never raises: a missing catalog, an unconfigured service, or
        a malformed pattern all fall back to the English default. A validation
        error must always be reportable — failing to render the *message* for a
        rejected payload would turn a 422 into a 500.
    """
    default = DEFAULT_MESSAGES.get(key, key)

    try:
        from aquilia.i18n.lazy import _locale_ref, _service_ref

        service = _service_ref.get()
        if service is not None:
            return service.t(
                f"contracts.{key}",
                locale=_locale_ref.get(),
                default=default,
                **params,
            )
    except Exception:
        # i18n is optional and must never break validation reporting.
        pass

    if not params:
        return default
    try:
        return default.format(**params)
    except (KeyError, IndexError, ValueError):
        return default
