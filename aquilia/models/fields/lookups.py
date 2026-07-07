"""
Aquilia Field Lookups -- extensible lookup system for query filters.

Lookups define how field__lookup=value translates to SQL predicates.
Each Lookup knows its SQL operator, how to prepare the RHS, and
whether it is case-sensitive.

Usage:
    from aquilia.models.fields.lookups import Exact, IExact, Contains

    # Lookups are automatically resolved by the Q query builder.
    # Custom lookups can be registered:
    register_lookup("year", YearLookup)

Structure of this module:

- ``Lookup`` -- the base class. Subclasses declare ``lookup_name`` (the
  ``field__<name>=value`` suffix) and ``sql_operator``, and may override
  ``as_sql()`` when the default ``"{field}" {operator} ?`` template isn't
  enough (e.g. ``LIKE`` patterns, ``BETWEEN``, dialect-specific functions).
- A family of built-in lookups covering equality, case-insensitive
  variants, substring/prefix/suffix matching, membership, comparisons,
  null checks, ranges, regex, and date-part extraction (year/month/day).
- A small module-level registry (``_REGISTRY``) mapping lookup name to
  ``Lookup`` subclass, populated at import time by ``_register_builtins()``
  and extensible at runtime via ``register_lookup()``. ``resolve_lookup()``
  is the main entry point consumers use to turn a
  ``(field_name, lookup_name, value)`` triple into a ``Lookup`` instance.

All ``LIKE``-based lookups (``contains``, ``startswith``, ``endswith`` and
their case-insensitive variants) escape user input via ``_escape_like`` and
use ``ESCAPE '\\'`` so that ``%``/``_``/``\\`` in the search value are
treated literally rather than as SQL wildcards -- this prevents
LIKE-pattern injection from user-controlled filter values. Every lookup
still binds its value(s) as query parameters (``?`` placeholders), never
by string-formatting the value into the SQL text, so normal SQL injection
is not a concern here either way.
"""

from __future__ import annotations

from typing import Any, ClassVar

__all__ = [
    "Lookup",
    "Exact",
    "IExact",
    "Contains",
    "IContains",
    "StartsWith",
    "IStartsWith",
    "EndsWith",
    "IEndsWith",
    "In",
    "Gt",
    "Gte",
    "Lt",
    "Lte",
    "IsNull",
    "Range",
    "Regex",
    "IRegex",
    "Date",
    "Year",
    "Month",
    "Day",
    "lookup_registry",
    "resolve_lookup",
]


class Lookup:
    """
    Base class for field lookups.

    Each lookup knows:
    - lookup_name: the name used in filter(field__lookup=val)
    - sql_operator: the SQL comparison operator
    - How to format the LHS / RHS of the comparison

    Subclasses that only need a different comparison operator (``Gt``,
    ``Lte``, etc.) can get away with overriding just the two class
    attributes; subclasses that need a different SQL shape (``LIKE``,
    ``BETWEEN``, ``IN (...)``, dialect-specific functions) override
    ``as_sql()`` instead.
    """

    lookup_name: ClassVar[str] = ""
    sql_operator: ClassVar[str] = "="
    bilateral: ClassVar[bool] = False  # Apply transform to both sides

    def __init__(self, field_name: str, value: Any):
        """
        Args:
            field_name: The database column name this lookup filters on.
                Used as-is (quoted) in the generated SQL -- callers are
                responsible for passing a trusted/validated column name,
                not raw user input.
            value: The right-hand-side comparison value. Interpretation is
                lookup-specific (e.g. a 2-tuple for ``Range``, an iterable
                for ``In``, a bool for ``IsNull``).
        """
        self.field_name = field_name
        self.value = value

    def as_sql(self, dialect: str = "sqlite") -> tuple[str, list[Any]]:
        """
        Return (sql_clause, params) for this lookup.

        Args:
            dialect: Target SQL dialect (e.g. ``"sqlite"``, ``"postgresql"``).
                The base implementation ignores this and always emits a
                dialect-neutral ``"{field}" {operator} ?`` clause;
                subclasses that need dialect-specific SQL (regex, date
                extraction, etc.) branch on this value.

        Returns:
            A ``(sql_clause, params)`` tuple where ``sql_clause`` is a SQL
            fragment using ``?`` placeholders and ``params`` is the
            ordered list of values to bind to those placeholders. Callers
            are expected to execute this via a parameterized query, never
            by interpolating ``params`` into the SQL text themselves.
        """
        lhs = f'"{self.field_name}"'
        return f"{lhs} {self.sql_operator} ?", [self.value]

    def __repr__(self) -> str:
        """Return a debug string of the form ``<ClassName: field=value>``."""
        return f"<{self.__class__.__name__}: {self.field_name}={self.value!r}>"


class Exact(Lookup):
    """Exact equality match: ``field__exact=value`` (also the default when
    no lookup suffix is given, e.g. ``field=value``)."""

    lookup_name = "exact"
    sql_operator = "="


def _escape_like(value: str) -> str:
    """Escape LIKE meta-characters to prevent LIKE pattern injection.

    Replaces ``\\``, ``%``, and ``_`` with their escaped equivalents
    so that user-supplied text is treated as literal characters.

    Args:
        value: The raw substring/prefix/suffix supplied by the caller
            (before any ``%`` wildcards are added around it).

    Returns:
        The escaped string, safe to embed between ``%``/wildcards and to
        pass as a bound parameter to a ``LIKE ... ESCAPE '\\'`` clause.

    Example:
        _escape_like("50%_off")  # -> "50\\%\\_off"
    """
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


class IExact(Lookup):
    """Case-insensitive exact match."""

    lookup_name = "iexact"

    def as_sql(self, dialect: str = "sqlite") -> tuple[str, list[Any]]:
        """Return a ``LOWER(field) = LOWER(?)`` clause bound to ``self.value``."""
        return f'LOWER("{self.field_name}") = LOWER(?)', [self.value]


class Contains(Lookup):
    """Case-sensitive substring match: ``field__contains=value``."""

    lookup_name = "contains"
    sql_operator = "LIKE"

    def as_sql(self, dialect: str = "sqlite") -> tuple[str, list[Any]]:
        """Return a ``LIKE '%value%'`` clause with LIKE metacharacters in
        ``self.value`` escaped via ``_escape_like``."""
        escaped = _escape_like(self.value)
        return f"\"{self.field_name}\" LIKE ? ESCAPE '\\'", [f"%{escaped}%"]


class IContains(Lookup):
    """Case-insensitive contains."""

    lookup_name = "icontains"

    def as_sql(self, dialect: str = "sqlite") -> tuple[str, list[Any]]:
        """Return a case-insensitive ``LIKE '%value%'`` clause, with
        ``self.value`` LIKE-escaped and both sides lower-cased."""
        escaped = _escape_like(self.value)
        return f"LOWER(\"{self.field_name}\") LIKE LOWER(?) ESCAPE '\\'", [f"%{escaped}%"]


class StartsWith(Lookup):
    """Case-sensitive prefix match: ``field__startswith=value``."""

    lookup_name = "startswith"

    def as_sql(self, dialect: str = "sqlite") -> tuple[str, list[Any]]:
        """Return a ``LIKE 'value%'`` clause with ``self.value`` LIKE-escaped."""
        escaped = _escape_like(self.value)
        return f"\"{self.field_name}\" LIKE ? ESCAPE '\\'", [f"{escaped}%"]


class IStartsWith(Lookup):
    """Case-insensitive startswith."""

    lookup_name = "istartswith"

    def as_sql(self, dialect: str = "sqlite") -> tuple[str, list[Any]]:
        """Return a case-insensitive ``LIKE 'value%'`` clause, with
        ``self.value`` LIKE-escaped and both sides lower-cased."""
        escaped = _escape_like(self.value)
        return f"LOWER(\"{self.field_name}\") LIKE LOWER(?) ESCAPE '\\'", [f"{escaped}%"]


class EndsWith(Lookup):
    """Case-sensitive suffix match: ``field__endswith=value``."""

    lookup_name = "endswith"

    def as_sql(self, dialect: str = "sqlite") -> tuple[str, list[Any]]:
        """Return a ``LIKE '%value'`` clause with ``self.value`` LIKE-escaped."""
        escaped = _escape_like(self.value)
        return f"\"{self.field_name}\" LIKE ? ESCAPE '\\'", [f"%{escaped}"]


class IEndsWith(Lookup):
    """Case-insensitive endswith."""

    lookup_name = "iendswith"

    def as_sql(self, dialect: str = "sqlite") -> tuple[str, list[Any]]:
        """Return a case-insensitive ``LIKE '%value'`` clause, with
        ``self.value`` LIKE-escaped and both sides lower-cased."""
        escaped = _escape_like(self.value)
        return f"LOWER(\"{self.field_name}\") LIKE LOWER(?) ESCAPE '\\'", [f"%{escaped}"]


class In(Lookup):
    """Membership test: ``field__in=[v1, v2, ...]``."""

    lookup_name = "in"

    def as_sql(self, dialect: str = "sqlite") -> tuple[str, list[Any]]:
        """
        Return an ``IN (?, ?, ...)`` clause with one placeholder per
        element of ``self.value``.

        Edge case: if ``self.value`` is empty (or falsy), returns the
        constant-false clause ``"1 = 0"`` with no params, so an empty
        ``in=[]`` lookup matches nothing rather than producing invalid SQL
        (``IN ()``) or matching everything.
        """
        if not self.value:
            return "1 = 0", []  # Always false
        placeholders = ", ".join("?" for _ in self.value)
        return f'"{self.field_name}" IN ({placeholders})', list(self.value)


class Gt(Lookup):
    """Strictly greater than: ``field__gt=value``."""

    lookup_name = "gt"
    sql_operator = ">"


class Gte(Lookup):
    """Greater than or equal to: ``field__gte=value``."""

    lookup_name = "gte"
    sql_operator = ">="


class Lt(Lookup):
    """Strictly less than: ``field__lt=value``."""

    lookup_name = "lt"
    sql_operator = "<"


class Lte(Lookup):
    """Less than or equal to: ``field__lte=value``."""

    lookup_name = "lte"
    sql_operator = "<="


class IsNull(Lookup):
    """Null check: ``field__isnull=True`` / ``field__isnull=False``."""

    lookup_name = "isnull"

    def as_sql(self, dialect: str = "sqlite") -> tuple[str, list[Any]]:
        """
        Return ``IS NULL`` when ``self.value`` is truthy, otherwise
        ``IS NOT NULL``. Either way the clause takes no bound parameters.
        """
        if self.value:
            return f'"{self.field_name}" IS NULL', []
        return f'"{self.field_name}" IS NOT NULL', []


class Range(Lookup):
    """Filter within a range: field__range=(lo, hi)."""

    lookup_name = "range"

    def as_sql(self, dialect: str = "sqlite") -> tuple[str, list[Any]]:
        """
        Return a ``BETWEEN ? AND ?`` clause (inclusive of both bounds, per
        standard SQL ``BETWEEN`` semantics).

        Args:
            dialect: Unused; the ``BETWEEN`` syntax is portable as-is.

        Raises:
            TypeError/ValueError: implicitly, if ``self.value`` cannot be
                unpacked into exactly two elements ``(lo, hi)``.
        """
        lo, hi = self.value
        return f'"{self.field_name}" BETWEEN ? AND ?', [lo, hi]


class Regex(Lookup):
    """Filter by regex (PostgreSQL: ~, SQLite: REGEXP if loaded)."""

    lookup_name = "regex"

    def as_sql(self, dialect: str = "sqlite") -> tuple[str, list[Any]]:
        """
        Return a dialect-appropriate regex match clause.

        On ``dialect == "postgresql"`` uses PostgreSQL's native ``~``
        case-sensitive regex operator. Otherwise emits a ``REGEXP``
        clause, which for SQLite only works if a ``REGEXP`` user-defined
        function has been registered on the connection (SQLite has no
        built-in ``REGEXP`` implementation) -- without it, SQLite raises
        an error at execution time rather than at SQL-generation time.
        """
        if dialect == "postgresql":
            return f'"{self.field_name}" ~ ?', [self.value]
        # SQLite: requires REGEXP function to be loaded
        return f'"{self.field_name}" REGEXP ?', [self.value]


class IRegex(Lookup):
    """Case-insensitive regex."""

    lookup_name = "iregex"

    def as_sql(self, dialect: str = "sqlite") -> tuple[str, list[Any]]:
        """
        Return a dialect-appropriate case-insensitive regex match clause.

        On PostgreSQL uses the ``~*`` case-insensitive regex operator.
        Otherwise lower-cases both the column and the pattern and applies
        ``REGEXP`` (same SQLite caveat as ``Regex.as_sql`` -- requires a
        registered ``REGEXP`` function). Note lower-casing the *pattern*
        is only correct for patterns without case-sensitive regex syntax
        (e.g. character-class ranges); it is a pragmatic approximation of
        case-insensitive matching, not a true ``(?i)`` flag.
        """
        if dialect == "postgresql":
            return f'"{self.field_name}" ~* ?', [self.value]
        return f'LOWER("{self.field_name}") REGEXP LOWER(?)', [self.value]


class Date(Lookup):
    """Extract date from datetime and compare."""

    lookup_name = "date"

    def as_sql(self, dialect: str = "sqlite") -> tuple[str, list[Any]]:
        """
        Return a clause comparing the date portion of a datetime column to
        ``self.value``.

        On PostgreSQL casts the column with ``::date``. On SQLite uses the
        ``DATE()`` function and stringifies ``self.value`` (SQLite has no
        native date type; dates are typically stored as ISO-8601 text).
        """
        if dialect == "postgresql":
            return f'("{self.field_name}")::date = ?', [self.value]
        return f'DATE("{self.field_name}") = ?', [str(self.value)]


class Year(Lookup):
    """Extract year and compare."""

    lookup_name = "year"

    def as_sql(self, dialect: str = "sqlite") -> tuple[str, list[Any]]:
        """
        Return a clause comparing the year component of a date/datetime
        column to ``self.value``.

        PostgreSQL: ``EXTRACT(YEAR FROM field) = ?``. SQLite:
        ``STRFTIME('%Y', field)`` cast to ``INTEGER`` for numeric
        comparison against ``self.value``.
        """
        if dialect == "postgresql":
            return f'EXTRACT(YEAR FROM "{self.field_name}") = ?', [self.value]
        return f'CAST(STRFTIME("%Y", "{self.field_name}") AS INTEGER) = ?', [self.value]


class Month(Lookup):
    """Extract month and compare."""

    lookup_name = "month"

    def as_sql(self, dialect: str = "sqlite") -> tuple[str, list[Any]]:
        """
        Return a clause comparing the month component (1-12) of a
        date/datetime column to ``self.value``.

        PostgreSQL: ``EXTRACT(MONTH FROM field) = ?``. SQLite:
        ``STRFTIME('%m', field)`` cast to ``INTEGER``.
        """
        if dialect == "postgresql":
            return f'EXTRACT(MONTH FROM "{self.field_name}") = ?', [self.value]
        return f'CAST(STRFTIME("%m", "{self.field_name}") AS INTEGER) = ?', [self.value]


class Day(Lookup):
    """Extract day and compare."""

    lookup_name = "day"

    def as_sql(self, dialect: str = "sqlite") -> tuple[str, list[Any]]:
        """
        Return a clause comparing the day-of-month component (1-31) of a
        date/datetime column to ``self.value``.

        PostgreSQL: ``EXTRACT(DAY FROM field) = ?``. SQLite:
        ``STRFTIME('%d', field)`` cast to ``INTEGER``.
        """
        if dialect == "postgresql":
            return f'EXTRACT(DAY FROM "{self.field_name}") = ?', [self.value]
        return f'CAST(STRFTIME("%d", "{self.field_name}") AS INTEGER) = ?', [self.value]


# ── Lookup Registry ──────────────────────────────────────────────────────────

_REGISTRY: dict[str, type[Lookup]] = {}


def _register_builtins() -> None:
    """
    Register all built-in lookups into the module-level ``_REGISTRY``.

    Called once at import time (see the module-level call right below the
    definition). Idempotent: re-invoking it simply re-assigns the same
    ``lookup_name -> class`` entries.
    """
    for cls in [
        Exact,
        IExact,
        Contains,
        IContains,
        StartsWith,
        IStartsWith,
        EndsWith,
        IEndsWith,
        In,
        Gt,
        Gte,
        Lt,
        Lte,
        IsNull,
        Range,
        Regex,
        IRegex,
        Date,
        Year,
        Month,
        Day,
    ]:
        _REGISTRY[cls.lookup_name] = cls


_register_builtins()


def lookup_registry() -> dict[str, type[Lookup]]:
    """
    Return a copy of the lookup registry.

    Returns:
        A new ``dict`` snapshot of ``lookup_name -> Lookup subclass``.
        A copy is returned (rather than the live ``_REGISTRY``) so callers
        can freely inspect or mutate the result without affecting lookup
        resolution elsewhere in the process.
    """
    return dict(_REGISTRY)


def register_lookup(name: str, cls: type[Lookup]) -> None:
    """
    Register a custom lookup type.

    Args:
        name: The lookup suffix consumers will use as ``field__<name>=value``.
        cls: A ``Lookup`` subclass to associate with *name*. Typically
            *name* matches ``cls.lookup_name``, but this isn't enforced --
            you can register the same class under multiple names, or
            register it under a name that overrides where it applies.

    Behavior:
        Mutates the shared, process-global ``_REGISTRY`` in place. If
        *name* is already registered (whether a built-in or a previously
        registered custom lookup), this silently replaces it -- there is
        no protection against accidentally shadowing an existing lookup
        (e.g. registering a custom ``"exact"``).
    """
    _REGISTRY[name] = cls


def resolve_lookup(field_name: str, lookup_name: str, value: Any) -> Lookup:
    """
    Resolve a lookup name to a Lookup instance.

    Args:
        field_name: The database field/column name
        lookup_name: The lookup suffix (e.g., "gt", "contains")
        value: The comparison value

    Returns:
        Lookup instance

    Raises:
        RegistryFault: If lookup_name is not registered in ``_REGISTRY``
            (neither a built-in nor previously registered via
            ``register_lookup``). The fault message lists all currently
            available lookup names to aid debugging.
    """
    cls = _REGISTRY.get(lookup_name)
    if cls is None:
        from aquilia.faults.domains import RegistryFault

        raise RegistryFault(
            name=lookup_name,
            message=f"Unknown lookup '{lookup_name}'. Available: {sorted(_REGISTRY.keys())}",
        )
    return cls(field_name, value)
