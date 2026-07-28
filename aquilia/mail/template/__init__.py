"""
AquilaMail ATS (Aquilia Template Syntax) — expression renderer.

ATS is the minimal template dialect used for mail bodies and subjects.  It
intentionally supports **expressions and filters only** — there is no
control flow, no loops, and no template inheritance.  Anything that looks
like unsupported syntax raises :class:`~aquilia.mail.faults.MailTemplateFault`
rather than being silently dropped into the outgoing message.

Why a separate dialect at all?  Mail bodies are rendered from data that is
frequently user-controlled (display names, order notes, support replies) and
are read in mail clients that render arbitrary markup.  ATS therefore
**HTML-escapes every interpolated value by default**, exactly like Jinja2 or
Django autoescaping, and requires an explicit ``| safe`` to opt out.

Syntax::

    << expr >>                  expression interpolation (auto-escaped)
    << expr | filter >>         filter application
    << expr | filter(arg) >>    filter with literal arguments
    << html_fragment | safe >>  opt out of escaping (use with care)

Dotted lookups traverse dicts and attributes: ``<< user.profile.name >>``.
An undefined name renders as an empty string rather than raising, so a
missing optional field can never block a transactional email.

Built-in filters: see :data:`FILTERS`.

Security:
    Interpolated values are escaped with :func:`html.escape` (including
    quotes) whenever ``autoescape`` is enabled — which is the default for
    every HTML render path.  ``| safe`` marks a value as pre-sanitised
    markup; only apply it to strings your own code produced.

Examples::

    from aquilia.mail.template import render_string

    render_string("Hi << user.name >>!", {"user": {"name": "<b>Asha</b>"}})
    # 'Hi &lt;b&gt;Asha&lt;/b&gt;!'

    render_string("Total: << price | currency('USD') >>", {"price": 12.5})
    # 'Total: USD 12.50'

    render_string("<< body | safe >>", {"body": "<p>ok</p>"})
    # '<p>ok</p>'
"""

from __future__ import annotations

import ast
import html
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

from ..faults import MailTemplateFault

__all__ = [
    "FILTERS",
    "configure",
    "register_filter",
    "render_string",
    "render_template",
]

# ── Syntax ──────────────────────────────────────────────────────────

# Matches << expr >> — the ATS expression delimiter.
_EXPR_RE = re.compile(r"<<\s*(.+?)\s*>>")

# Matches unsupported control-flow tags ([[% if %]], [[% for %]], ...).
# These are detected so they fail loudly instead of shipping raw tokens to
# a recipient's inbox.
_CONTROL_TAG_RE = re.compile(r"\[\[%\s*(\w+)")

# Splits a filter call into name and optional argument list.
_FILTER_CALL_RE = re.compile(r"^(?P<name>[A-Za-z_]\w*)\s*(?:\((?P<args>.*)\))?$", re.DOTALL)

# ── Template search paths (set via MailConfig or default) ───────────

_template_dirs: list[Path] = []


def configure(template_dirs: list[str] | None = None) -> None:
    """
    Set the template search directories.

    Called at :class:`~aquilia.mail.service.MailService` startup from
    ``MailConfig.templates.dirs``.  Passing ``None`` or an empty list is a
    no-op, so a partially configured app keeps whatever paths it had.

    Args:
        template_dirs: Directories searched, in order, by
            :func:`render_template`.
    """
    global _template_dirs
    if template_dirs:
        _template_dirs = [Path(d) for d in template_dirs]


# ── Filters ─────────────────────────────────────────────────────────


class _Safe(str):
    """
    Marker for markup that must not be escaped.

    Returned by the ``safe`` filter.  Subclassing :class:`str` keeps it
    usable by every downstream filter while letting the renderer detect the
    opt-out with an ``isinstance`` check.
    """

    __slots__ = ()


def _f_safe(value: Any) -> _Safe:
    """Mark a value as pre-sanitised markup (disables escaping)."""
    return _Safe("" if value is None else str(value))


def _f_escape(value: Any) -> str:
    """Force HTML escaping even inside a non-escaping render."""
    return html.escape("" if value is None else str(value), quote=True)


def _f_title(value: Any) -> str:
    """Title-case a string (``"asha rao"`` → ``"Asha Rao"``)."""
    return str(value or "").title()


def _f_upper(value: Any) -> str:
    """Upper-case a string."""
    return str(value or "").upper()


def _f_lower(value: Any) -> str:
    """Lower-case a string."""
    return str(value or "").lower()


def _f_trim(value: Any) -> str:
    """Strip leading and trailing whitespace."""
    return str(value or "").strip()


def _f_default(value: Any, fallback: str = "") -> Any:
    """Substitute ``fallback`` when the value is empty or ``None``."""
    return value if value not in (None, "") else fallback


def _f_truncate(value: Any, length: int = 80, suffix: str = "…") -> str:
    """
    Truncate to at most ``length`` characters, appending ``suffix``.

    Raises:
        MailTemplateFault: If ``length`` is not a positive integer.
    """
    try:
        limit = int(length)
    except (TypeError, ValueError):
        raise MailTemplateFault(f"truncate() length must be an integer, got {length!r}") from None
    if limit <= 0:
        raise MailTemplateFault(f"truncate() length must be > 0, got {limit}")
    text = str(value or "")
    return text if len(text) <= limit else text[:limit] + suffix


def _f_currency(value: Any, code: str = "USD", decimals: int = 2) -> str:
    """
    Format a number as ``"<code> <amount>"`` with fixed decimals.

    Raises:
        MailTemplateFault: If the value is not numeric.
    """
    try:
        amount = float(value)
    except (TypeError, ValueError):
        raise MailTemplateFault(f"currency() expects a number, got {value!r}") from None
    return f"{code} {amount:,.{int(decimals)}f}"


def _f_join(value: Any, separator: str = ", ") -> str:
    """Join an iterable into a string with ``separator``."""
    if isinstance(value, (str, bytes)) or value is None:
        return str(value or "")
    try:
        return separator.join(str(v) for v in value)
    except TypeError:
        return str(value)


def _f_length(value: Any) -> int:
    """Return the length of a sized value, or ``0`` when unsized."""
    try:
        return len(value)
    except TypeError:
        return 0


FILTERS: dict[str, Callable[..., Any]] = {
    "safe": _f_safe,
    "escape": _f_escape,
    "title": _f_title,
    "upper": _f_upper,
    "lower": _f_lower,
    "trim": _f_trim,
    "default": _f_default,
    "truncate": _f_truncate,
    "currency": _f_currency,
    "join": _f_join,
    "length": _f_length,
}
"""Registry of ATS filters, keyed by the name used after ``|``."""


def register_filter(name: str, fn: Callable[..., Any]) -> None:
    """
    Register a custom ATS filter.

    Args:
        name: Filter name as written in templates (after ``|``).
        fn: Callable receiving the piped value as its first argument,
            followed by any literal arguments from the template.

    Raises:
        MailTemplateFault: If the name is already registered.

    Examples::

        register_filter("shout", lambda v: f"{v}!!!")
        render_string("<< msg | shout >>", {"msg": "hi"})   # 'hi!!!'
    """
    if name in FILTERS:
        raise MailTemplateFault(f"Mail template filter {name!r} is already registered")
    FILTERS[name] = fn


# ── Rendering helpers ───────────────────────────────────────────────


def _resolve_dotted(name: str, context: dict[str, Any]) -> Any:
    """
    Resolve a dotted name against a context mapping.

    Traverses dict keys first, then attributes.  Unknown segments resolve
    to ``""`` so an optional field never aborts a send.

    Examples::

        _resolve_dotted("user.name", {"user": {"name": "Asha"}})   # 'Asha'
        _resolve_dotted("user.missing", {"user": {}})              # ''
    """
    parts = name.strip().split(".")
    current: Any = context
    for part in parts:
        if isinstance(current, dict):
            if part not in current:
                return ""  # undefined → empty string
            current = current[part]
        elif hasattr(current, part):
            current = getattr(current, part)
        else:
            return ""
    return current


def _parse_filter_args(raw: str, filter_name: str) -> list[Any]:
    """
    Parse a filter's literal argument list.

    Arguments are evaluated with :func:`ast.literal_eval`, so only literals
    (strings, numbers, booleans, ``None``, tuples/lists/dicts of literals)
    are accepted — never arbitrary expressions from a template file.

    Raises:
        MailTemplateFault: If the arguments are not valid Python literals.
    """
    raw = raw.strip()
    if not raw:
        return []
    try:
        parsed = ast.literal_eval(f"({raw},)")
    except (ValueError, SyntaxError):
        raise MailTemplateFault(
            f"Invalid arguments for filter {filter_name!r}: ({raw}). Only literal values are allowed."
        ) from None
    return list(parsed)


def _split_pipeline(expr: str) -> list[str]:
    """
    Split an ATS expression on ``|``, ignoring pipes inside string literals.

    ``"price | currency('USD|EUR')"`` must yield two segments, not three.
    """
    segments: list[str] = []
    buf: list[str] = []
    quote: str | None = None
    for ch in expr:
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = None
            continue
        if ch in "\"'":
            quote = ch
            buf.append(ch)
        elif ch == "|":
            segments.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    segments.append("".join(buf))
    return [s.strip() for s in segments]


def _apply_filter(value: Any, spec: str) -> Any:
    """
    Apply a single ``name`` / ``name(args...)`` filter spec to a value.

    Raises:
        MailTemplateFault: If the spec is malformed, the filter is unknown,
            or the filter rejects its arguments.
    """
    match = _FILTER_CALL_RE.match(spec)
    if not match:
        raise MailTemplateFault(f"Malformed mail template filter: {spec!r}")

    name = match.group("name")
    fn = FILTERS.get(name)
    if fn is None:
        known = ", ".join(sorted(FILTERS))
        raise MailTemplateFault(f"Unknown mail template filter {name!r}. Available filters: {known}")

    args = _parse_filter_args(match.group("args") or "", name)
    try:
        return fn(value, *args)
    except MailTemplateFault:
        raise
    except TypeError as e:
        raise MailTemplateFault(f"Filter {name!r} rejected its arguments: {e}") from e


def _substitute(match: re.Match[str], context: dict[str, Any], autoescape: bool) -> str:
    """
    Render a single ``<< expr >>`` match.

    The first pipeline segment is the value lookup; each remaining segment
    is a filter applied left to right.  The result is HTML-escaped unless
    ``autoescape`` is off or a filter returned a ``safe``-marked value.
    """
    segments = _split_pipeline(match.group(1))
    value = _resolve_dotted(segments[0], context)
    for spec in segments[1:]:
        value = _apply_filter(value, spec)

    if value is None:
        return ""
    if isinstance(value, _Safe):
        return str(value)
    text = str(value)
    return html.escape(text, quote=True) if autoescape else text


def _reject_control_flow(template_text: str) -> None:
    """
    Raise when a template uses control-flow tags ATS does not implement.

    Passing these through verbatim would ship raw ``[[% if ... %]]`` tokens
    to recipients, so an unrenderable template is treated as an error.

    Raises:
        MailTemplateFault: On any ``[[% ... %]]`` tag.
    """
    match = _CONTROL_TAG_RE.search(template_text)
    if match:
        raise MailTemplateFault(
            f"Mail template uses unsupported control-flow tag '[[% {match.group(1)} %]]'. "
            "ATS supports expressions and filters only — precompute the value in Python "
            "and interpolate it with << ... >>."
        )


# ── Public API ──────────────────────────────────────────────────────


def render_string(
    template_text: str,
    context: dict[str, Any],
    *,
    autoescape: bool = True,
) -> str:
    """
    Render an ATS template string.

    Args:
        template_text: ATS source text.
        context: Variables available to ``<< ... >>`` expressions.
        autoescape: HTML-escape interpolated values.  Keep enabled for HTML
            bodies; disable for plain-text bodies and subject headers, where
            escaping would corrupt the output (``&amp;`` in a subject line).

    Returns:
        The rendered string.

    Raises:
        MailTemplateFault: On unsupported control-flow tags, unknown or
            malformed filters, or invalid filter arguments.

    Examples::

        render_string("Hi << name >>", {"name": "Asha & Co"})
        # 'Hi Asha &amp; Co'

        render_string("Hi << name >>", {"name": "Asha & Co"}, autoescape=False)
        # 'Hi Asha & Co'
    """
    _reject_control_flow(template_text)
    return _EXPR_RE.sub(lambda m: _substitute(m, context, autoescape), template_text)


def render_template(
    template_name: str,
    context: dict[str, Any],
    *,
    template_dirs: list[str] | None = None,
    autoescape: bool | None = None,
) -> str:
    """
    Render a named ATS template file.

    Searches the directories configured via :func:`configure` (from
    ``MailConfig.templates.dirs``), then falls back to treating
    ``template_name`` as a filesystem path.

    Args:
        template_name: Template filename, e.g. ``"welcome.aqt"``.
        context: Variables for interpolation.
        template_dirs: Override the configured search directories.
        autoescape: Force escaping on or off.  When ``None`` (default),
            escaping is enabled for every extension except ``.txt``, which
            is treated as a plain-text body.

    Returns:
        The rendered template.

    Raises:
        MailTemplateFault: If the template cannot be found, or if rendering
            fails per :func:`render_string`.

    Examples::

        render_template("welcome.aqt", {"user": {"name": "Asha"}})
        render_template("receipt.txt", {"total": 9.99})   # no escaping
    """
    dirs = [Path(d) for d in template_dirs] if template_dirs else _template_dirs

    source: str | None = None
    for d in dirs:
        candidate = d / template_name
        if candidate.is_file():
            source = candidate.read_text(encoding="utf-8")
            break

    if source is None:
        # Not found in configured dirs — try template_name as a path
        p = Path(template_name)
        if p.is_file():
            source = p.read_text(encoding="utf-8")

    if source is None:
        searched = ", ".join(str(d) for d in dirs) if dirs else "(no dirs configured)"
        raise MailTemplateFault(
            f"Template '{template_name}' not found.  Searched: {searched}",
            template_name=template_name,
        )

    if autoescape is None:
        autoescape = not template_name.lower().endswith(".txt")

    return render_string(source, context, autoescape=autoescape)
