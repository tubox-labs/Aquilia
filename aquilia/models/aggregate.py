"""
Aquilia Aggregates -- Sum, Avg, Count, Max, Min for QuerySet.

Usage:
    from aquilia.models.aggregate import Sum, Avg, Count, Max, Min

    result = await Product.query().aggregate(
        total_price=Sum("price"),
        avg_price=Avg("price"),
        product_count=Count("id"),
        max_price=Max("price"),
        min_price=Min("price"),
    )
"""

from __future__ import annotations

from typing import Any

from .expression import Expression, F

__all__ = [
    "Aggregate",
    "Sum",
    "Avg",
    "Count",
    "Max",
    "Min",
    "StdDev",
    "Variance",
    "ArrayAgg",
    "StringAgg",
    "GroupConcat",
    "BoolAnd",
    "BoolOr",
]


class Aggregate(Expression):
    """
    Base class for aggregate functions.

    Subclasses define the SQL function name (SUM, AVG, COUNT, etc.).
    """

    function: str = ""
    template: str = "{function}({distinct}{expression})"

    def __init__(
        self,
        expression: str | Expression,
        *,
        distinct: bool = False,
        alias: str | None = None,
        filter_clause: str | None = None,
    ):
        """
        Args:
            expression: Field to aggregate, given as a field name (wrapped
                in ``F()``) or any ``Expression``.
            distinct: If True, render as ``FUNCTION(DISTINCT expr)``.
            alias: Optional label for this aggregate, stored for
                introspection/serialization only. Note that
                ``QuerySet.aggregate()`` derives the output column name from
                its keyword argument name, not from this attribute.
            filter_clause: Raw SQL boolean expression appended as
                ``FILTER (WHERE ...)`` (PostgreSQL / SQLite 3.25+; not
                supported on MySQL).

                .. warning::
                    Interpolated directly into the SQL string with **no
                    parameterization or escaping**. Never build it from
                    untrusted input.
        """
        if isinstance(expression, str):
            expression = F(expression)
        self.expression = expression
        self.distinct = distinct
        self.alias = alias
        self.filter_clause = filter_clause

    def as_sql(self, dialect: str = "sqlite") -> tuple[str, list[Any]]:
        """Render as ``FUNCTION([DISTINCT] expr) [FILTER (WHERE ...)]``."""
        expr_sql, expr_params = self.expression.as_sql(dialect)
        distinct_str = "DISTINCT " if self.distinct else ""
        sql = f"{self.function}({distinct_str}{expr_sql})"
        if self.filter_clause:
            sql += f" FILTER (WHERE {self.filter_clause})"
        return sql, expr_params

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.expression!r})"


class Sum(Aggregate):
    """SQL SUM() aggregate."""

    function = "SUM"


class Avg(Aggregate):
    """SQL AVG() aggregate."""

    function = "AVG"


class Count(Aggregate):
    """SQL COUNT() aggregate."""

    function = "COUNT"

    def __init__(self, expression: str | Expression = "*", **kwargs):
        """
        Args:
            expression: Field to count, or ``"*"`` (default) for ``COUNT(*)``.
            **kwargs: Forwarded to ``Aggregate.__init__`` (``distinct``, ``alias``, ``filter_clause``).
        """
        if expression == "*":
            # Special case: COUNT(*)
            super().__init__(expression="*", **kwargs)
        else:
            super().__init__(expression=expression, **kwargs)

    def as_sql(self, dialect: str = "sqlite") -> tuple[str, list[Any]]:
        """Render as ``COUNT([DISTINCT] *)`` when constructed with ``"*"``, else defer to ``Aggregate.as_sql``."""
        if isinstance(self.expression, F) and self.expression.name == "*":
            distinct_str = "DISTINCT " if self.distinct else ""
            return f"COUNT({distinct_str}*)", []
        return super().as_sql(dialect)


class Max(Aggregate):
    """SQL MAX() aggregate."""

    function = "MAX"


class Min(Aggregate):
    """SQL MIN() aggregate."""

    function = "MIN"


class StdDev(Aggregate):
    """SQL STDDEV() aggregate (PostgreSQL) / stdev (SQLite extension)."""

    function = "STDDEV"

    def as_sql(self, dialect: str = "sqlite") -> tuple[str, list[Any]]:
        """
        Render as ``STDDEV(expr)``.

        Caveat: SQLite has no native ``STDDEV`` -- it must be registered as
        a custom aggregate on the connection (e.g. via
        ``sqlite3.Connection.create_aggregate``), otherwise this raises a
        "no such function" error at execution time. The SQLite branch also
        bypasses ``distinct``/``filter_clause`` support, unlike the base
        ``Aggregate.as_sql`` used for other dialects.
        """
        if dialect == "sqlite":
            # SQLite doesn't have STDDEV natively; use a workaround
            expr_sql, expr_params = self.expression.as_sql(dialect)
            return f"STDDEV({expr_sql})", expr_params
        return super().as_sql(dialect)


class Variance(Aggregate):
    """SQL VARIANCE() aggregate."""

    function = "VARIANCE"

    def as_sql(self, dialect: str = "sqlite") -> tuple[str, list[Any]]:
        """
        Render as ``VARIANCE(expr)``.

        Caveat: same as ``StdDev`` -- SQLite has no native ``VARIANCE`` and
        requires a custom aggregate registered on the connection; the
        SQLite branch also bypasses ``distinct``/``filter_clause`` support.
        """
        if dialect == "sqlite":
            expr_sql, expr_params = self.expression.as_sql(dialect)
            return f"VARIANCE({expr_sql})", expr_params
        return super().as_sql(dialect)


# ── Extended Aggregates ──────────────────────────────────────────────────────


class ArrayAgg(Aggregate):
    """
    PostgreSQL ARRAY_AGG() -- collect values into an array.

    Falls back to GROUP_CONCAT on SQLite.

    Usage:
        result = await User.query().aggregate(names=ArrayAgg("name"))
    """

    function = "ARRAY_AGG"

    def __init__(
        self,
        expression: str | Expression,
        *,
        distinct: bool = False,
        ordering: str | None = None,
        **kwargs,
    ):
        """
        Args:
            expression: Field name or Expression to collect.
            distinct: If True, collect only distinct values.
            ordering: Field name to order collected values by; prefix with
                ``"-"`` for descending. Only honored on the PostgreSQL branch
                (see caveat on ``as_sql``).
            **kwargs: Forwarded to ``Aggregate.__init__`` (``alias``, ``filter_clause``).
        """
        super().__init__(expression, distinct=distinct, **kwargs)
        self.ordering = ordering

    def as_sql(self, dialect: str = "sqlite") -> tuple[str, list[Any]]:
        """
        Render as ``ARRAY_AGG([DISTINCT] expr [ORDER BY ...])`` on PostgreSQL.

        Falls back to ``GROUP_CONCAT([DISTINCT] expr)`` on SQLite.

        Caveat: on the SQLite branch, ``ordering`` is computed but never
        applied to the returned SQL -- SQLite's ``GROUP_CONCAT`` has no
        native ``ORDER BY`` sub-clause, so ordering is a no-op there.
        """
        expr_sql, expr_params = self.expression.as_sql(dialect)
        distinct_str = "DISTINCT " if self.distinct else ""

        if dialect == "sqlite":
            # SQLite fallback: GROUP_CONCAT
            order_str = ""
            if self.ordering:
                if self.ordering.startswith("-"):
                    order_str = f' ORDER BY "{self.ordering[1:]}" DESC'
                else:
                    order_str = f' ORDER BY "{self.ordering}" ASC'
            # Note: SQLite GROUP_CONCAT doesn't support ORDER BY natively inside
            return f"GROUP_CONCAT({distinct_str}{expr_sql})", expr_params
        else:
            # PostgreSQL
            order_str = ""
            if self.ordering:
                if self.ordering.startswith("-"):
                    order_str = f' ORDER BY "{self.ordering[1:]}" DESC'
                else:
                    order_str = f' ORDER BY "{self.ordering}" ASC'
            return f"ARRAY_AGG({distinct_str}{expr_sql}{order_str})", expr_params


class StringAgg(Aggregate):
    """
    PostgreSQL STRING_AGG() -- concatenate strings with a delimiter.

    Falls back to GROUP_CONCAT on SQLite/MySQL.

    Usage:
        result = await Tag.query().aggregate(all_tags=StringAgg("name", delimiter=", "))
    """

    function = "STRING_AGG"

    def __init__(
        self,
        expression: str | Expression,
        *,
        delimiter: str = ",",
        distinct: bool = False,
        ordering: str | None = None,
        **kwargs,
    ):
        """
        Args:
            expression: Field name or Expression to concatenate.
            delimiter: Separator placed between values (default ``","``).
            distinct: If True, concatenate only distinct values.
            ordering: Field name to order concatenated values by; prefix
                with ``"-"`` for descending. Only honored on the PostgreSQL
                branch.
            **kwargs: Forwarded to ``Aggregate.__init__`` (``alias``, ``filter_clause``).
        """
        super().__init__(expression, distinct=distinct, **kwargs)
        self.delimiter = delimiter
        self.ordering = ordering

    def as_sql(self, dialect: str = "sqlite") -> tuple[str, list[Any]]:
        """
        Render dialect-specific string aggregation.

        - SQLite: ``GROUP_CONCAT([DISTINCT] expr, ?)`` with *delimiter* parameterized.
        - MySQL: ``GROUP_CONCAT([DISTINCT] expr SEPARATOR '<delimiter>')``.

          .. warning::
              *delimiter* is interpolated directly into the SQL string on
              this branch (not parameterized) -- do not build it from
              untrusted input, and avoid delimiters containing ``'``.
        - PostgreSQL: ``STRING_AGG([DISTINCT] expr, ? [ORDER BY ...])`` with
          *delimiter* parameterized and *ordering* honored.
        """
        expr_sql, expr_params = self.expression.as_sql(dialect)
        distinct_str = "DISTINCT " if self.distinct else ""

        if dialect == "sqlite":
            return f"GROUP_CONCAT({distinct_str}{expr_sql}, ?)", expr_params + [self.delimiter]
        elif dialect == "mysql":
            sep = f" SEPARATOR '{self.delimiter}'"
            return f"GROUP_CONCAT({distinct_str}{expr_sql}{sep})", expr_params
        else:
            # PostgreSQL
            order_str = ""
            if self.ordering:
                if self.ordering.startswith("-"):
                    order_str = f' ORDER BY "{self.ordering[1:]}" DESC'
                else:
                    order_str = f' ORDER BY "{self.ordering}" ASC'
            return f"STRING_AGG({distinct_str}{expr_sql}, ?{order_str})", expr_params + [self.delimiter]


class GroupConcat(Aggregate):
    """
    MySQL/SQLite GROUP_CONCAT() aggregate.

    Usage:
        result = await Tag.query().aggregate(tags=GroupConcat("name", separator=", "))
    """

    function = "GROUP_CONCAT"

    def __init__(
        self,
        expression: str | Expression,
        *,
        separator: str = ",",
        distinct: bool = False,
        **kwargs,
    ):
        """
        Args:
            expression: Field name or Expression to concatenate.
            separator: Separator placed between values (default ``","``).
            distinct: If True, concatenate only distinct values.
            **kwargs: Forwarded to ``Aggregate.__init__`` (``alias``, ``filter_clause``).
        """
        super().__init__(expression, distinct=distinct, **kwargs)
        self.separator = separator

    def as_sql(self, dialect: str = "sqlite") -> tuple[str, list[Any]]:
        """
        Render as ``GROUP_CONCAT([DISTINCT] expr SEPARATOR '<separator>')`` on MySQL,
        or ``GROUP_CONCAT([DISTINCT] expr, ?)`` with *separator* parameterized elsewhere (SQLite).

        .. warning::
            On the MySQL branch, *separator* is interpolated directly into
            the SQL string (not parameterized) -- do not build it from
            untrusted input, and avoid separators containing ``'``.
        """
        expr_sql, expr_params = self.expression.as_sql(dialect)
        distinct_str = "DISTINCT " if self.distinct else ""

        if dialect == "mysql":
            sep = f" SEPARATOR '{self.separator}'"
            return f"GROUP_CONCAT({distinct_str}{expr_sql}{sep})", expr_params
        else:
            # SQLite
            return f"GROUP_CONCAT({distinct_str}{expr_sql}, ?)", expr_params + [self.separator]


class BoolAnd(Aggregate):
    """
    PostgreSQL BOOL_AND() -- returns true if ALL values are true.

    Falls back to MIN() on SQLite (treating 0/1).

    Usage:
        result = await User.query().aggregate(all_active=BoolAnd("active"))
    """

    function = "BOOL_AND"

    def as_sql(self, dialect: str = "sqlite") -> tuple[str, list[Any]]:
        """Render as ``MIN(expr)`` on SQLite (booleans stored as 0/1), else ``BOOL_AND(expr)``."""
        expr_sql, expr_params = self.expression.as_sql(dialect)
        if dialect == "sqlite":
            return f"MIN({expr_sql})", expr_params
        return f"BOOL_AND({expr_sql})", expr_params


class BoolOr(Aggregate):
    """
    PostgreSQL BOOL_OR() -- returns true if ANY value is true.

    Falls back to MAX() on SQLite (treating 0/1).

    Usage:
        result = await User.query().aggregate(any_active=BoolOr("active"))
    """

    function = "BOOL_OR"

    def as_sql(self, dialect: str = "sqlite") -> tuple[str, list[Any]]:
        """Render as ``MAX(expr)`` on SQLite (booleans stored as 0/1), else ``BOOL_OR(expr)``."""
        expr_sql, expr_params = self.expression.as_sql(dialect)
        if dialect == "sqlite":
            return f"MAX({expr_sql})", expr_params
        return f"BOOL_OR({expr_sql})", expr_params
