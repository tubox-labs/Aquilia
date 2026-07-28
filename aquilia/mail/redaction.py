"""
AquilaMail PII redaction.

Mail log lines and fault metadata naturally carry recipient addresses, and
those addresses are personal data: log aggregators, error trackers and
support tooling replicate them well outside the retention boundary the
application itself promises.

:func:`redact_pii` masks the identifying part of an address while keeping
enough structure to debug with — the domain stays intact, so "which tenant,
which provider, which MX" questions are still answerable, and a first/last
character of the local part keeps two different recipients distinguishable
in a log trail.

Redaction is opt-in via ``MailConfig.security.pii_redaction_enabled`` and is
applied by :class:`~aquilia.mail.service.MailService` to log output and fault
messages.  It is **not** applied to the message being delivered — that would
break the mail.

Examples::

    redact_pii("asha.rao@example.com")
    # 'a******o@example.com'

    redact_pii("delivery failed for bo@x.io and cc: eve@y.org")
    # 'delivery failed for b*@x.io and cc: e**@y.org'
"""

from __future__ import annotations

import re

__all__ = ["redact_email", "redact_pii"]

# Matches bare addresses inside arbitrary text (log lines, fault messages).
_ADDRESS_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")


def redact_email(address: str) -> str:
    """
    Mask the local part of a single email address.

    Args:
        address: A bare address, e.g. ``"asha@example.com"``.

    Returns:
        The address with its local part masked.  The first and last
        characters survive when the local part is at least three characters
        long, so distinct recipients remain distinguishable; shorter local
        parts keep only the first character.  Input without an ``@`` is
        returned unchanged.

    Examples::

        redact_email("asha.rao@example.com")   # 'a******o@example.com'
        redact_email("bo@x.io")                # 'b*@x.io'
        redact_email("a@x.io")                 # 'a@x.io'
        redact_email("not-an-address")         # 'not-an-address'
    """
    local, sep, domain = address.partition("@")
    if not sep:
        return address
    if len(local) <= 1:
        return f"{local}{sep}{domain}"
    if len(local) == 2:
        return f"{local[0]}*{sep}{domain}"
    return f"{local[0]}{'*' * (len(local) - 2)}{local[-1]}{sep}{domain}"


def redact_pii(text: str, *, enabled: bool = True) -> str:
    """
    Mask every email address appearing in a free-form string.

    Args:
        text: Text to scan — a log message, fault message, or metadata value.
        enabled: When ``False``, the text is returned unchanged.  Threading
            the flag through here keeps call sites free of conditionals.

    Returns:
        The text with each address's local part masked.

    Performance:
        One regex pass; suitable for the per-message logging path.

    Examples::

        redact_pii("all providers failed for a.b@c.io")
        # 'all providers failed for a*b@c.io'

        redact_pii("a.b@c.io", enabled=False)
        # 'a.b@c.io'
    """
    if not enabled or not text:
        return text
    return _ADDRESS_RE.sub(lambda m: redact_email(m.group(0)), text)
