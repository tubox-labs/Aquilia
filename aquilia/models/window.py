"""
Aquilia Window Expression System — OVER (PARTITION BY ... ORDER BY ...).

Window functions compute values across a set of rows related to the current
row, without collapsing them into a single output row (unlike aggregates).

Usage::

    from aquilia.models.window import (
        Window, Rank, DenseRank, RowNumber, Ntile,
        Lag, Lead, FirstValue, LastValue, NthValue,
        FrameType, FrameBound,
    )
    from aquilia.models import Sum

    # Rank within partition
    qs = await User.objects.annotate(
        rank=Window(Rank(), partition_by=['country'], order_by='-score')
    ).all()

    # Running total
    qs = await Sale.objects.annotate(
        running_total=Window(Sum('amount'), order_by='created_at')
    ).all()
"""

from __future__ import annotations

import enum
from typing import Any

from .expression import Expression, F, OrderBy, _coerce_expression

__all__ = [
    "Window",
    "WindowFunction",
    "Rank",
    "DenseRank",
    "RowNumber",
    "Ntile",
    "Lag",
    "Lead",
    "FirstValue",
    "LastValue",
    "NthValue",
    "FrameType",
    "FrameBound",
    "WindowFrame",
]


class FrameBoundType(str, enum.Enum):
    UNBOUNDED_PRECEDING = "UNBOUNDED PRECEDING"
    PRECEDING = "PRECEDING"  # N PRECEDING
    CURRENT_ROW = "CURRENT ROW"
    FOLLOWING = "FOLLOWING"  # N FOLLOWING
    UNBOUNDED_FOLLOWING = "UNBOUNDED FOLLOWING"


class FrameBound:
    """Represents one endpoint of a window frame boundary."""

    def __init__(self, bound_type: FrameBoundType, offset: int | None = None):
        self.bound_type = bound_type
        self.offset = offset

    def as_sql(self) -> str:
        if self.bound_type in (FrameBoundType.PRECEDING, FrameBoundType.FOLLOWING):
            if self.offset is None:
                raise ValueError(f"Offset is required for {self.bound_type}")
            return f"{self.offset} {self.bound_type.value}"
        return self.bound_type.value

    @classmethod
    def unbounded_preceding(cls) -> FrameBound:
        return cls(FrameBoundType.UNBOUNDED_PRECEDING)

    @classmethod
    def current_row(cls) -> FrameBound:
        return cls(FrameBoundType.CURRENT_ROW)

    @classmethod
    def unbounded_following(cls) -> FrameBound:
        return cls(FrameBoundType.UNBOUNDED_FOLLOWING)

    @classmethod
    def preceding(cls, n: int) -> FrameBound:
        return cls(FrameBoundType.PRECEDING, n)

    @classmethod
    def following(cls, n: int) -> FrameBound:
        return cls(FrameBoundType.FOLLOWING, n)


class FrameType(str, enum.Enum):
    ROWS = "ROWS"
    RANGE = "RANGE"
    GROUPS = "GROUPS"


class WindowFrame:
    """Renders 'ROWS BETWEEN ... AND ...'."""

    def __init__(self, frame_type: FrameType, start: FrameBound, end: FrameBound | None = None):
        self.frame_type = frame_type
        self.start = start
        self.end = end

    def as_sql(self) -> str:
        start_sql = self.start.as_sql()
        if self.end:
            end_sql = self.end.as_sql()
            return f"{self.frame_type.value} BETWEEN {start_sql} AND {end_sql}"
        return f"{self.frame_type.value} {start_sql}"


class WindowFunction(Expression):
    """Base for pure window functions."""

    function: str = ""

    def as_sql(self, dialect: str = "sqlite") -> tuple[str, list[Any]]:
        return f"{self.function}()", []


class Rank(WindowFunction):
    """RANK() window function."""

    function = "RANK"


class DenseRank(WindowFunction):
    """DENSE_RANK() window function."""

    function = "DENSE_RANK"


class RowNumber(WindowFunction):
    """ROW_NUMBER() window function."""

    function = "ROW_NUMBER"


class Ntile(WindowFunction):
    """NTILE(n) window function."""

    def __init__(self, num_buckets: int):
        self.num_buckets = num_buckets

    def as_sql(self, dialect: str = "sqlite") -> tuple[str, list[Any]]:
        return "NTILE(?)", [self.num_buckets]


class Lag(Expression):
    """LAG(expr, offset[, default]) window function."""

    def __init__(self, expression: Any, offset: int = 1, default: Any = None):
        self.expression = _coerce_expression(expression)
        self.offset = offset
        self.default = default

    def as_sql(self, dialect: str = "sqlite") -> tuple[str, list[Any]]:
        expr_sql, expr_params = self.expression.as_sql(dialect)
        params = expr_params + [self.offset]
        if self.default is not None:
            params.append(self.default)
            return f"LAG({expr_sql}, ?, ?)", params
        return f"LAG({expr_sql}, ?)", params


class Lead(Expression):
    """LEAD(expr, offset[, default]) window function."""

    def __init__(self, expression: Any, offset: int = 1, default: Any = None):
        self.expression = _coerce_expression(expression)
        self.offset = offset
        self.default = default

    def as_sql(self, dialect: str = "sqlite") -> tuple[str, list[Any]]:
        expr_sql, expr_params = self.expression.as_sql(dialect)
        params = expr_params + [self.offset]
        if self.default is not None:
            params.append(self.default)
            return f"LEAD({expr_sql}, ?, ?)", params
        return f"LEAD({expr_sql}, ?)", params


class FirstValue(Expression):
    """FIRST_VALUE(expr) window function."""

    def __init__(self, expression: Any):
        self.expression = _coerce_expression(expression)

    def as_sql(self, dialect: str = "sqlite") -> tuple[str, list[Any]]:
        expr_sql, expr_params = self.expression.as_sql(dialect)
        return f"FIRST_VALUE({expr_sql})", expr_params


class LastValue(Expression):
    """LAST_VALUE(expr) window function."""

    def __init__(self, expression: Any):
        self.expression = _coerce_expression(expression)

    def as_sql(self, dialect: str = "sqlite") -> tuple[str, list[Any]]:
        expr_sql, expr_params = self.expression.as_sql(dialect)
        return f"LAST_VALUE({expr_sql})", expr_params


class NthValue(Expression):
    """NTH_VALUE(expr, n) window function."""

    def __init__(self, expression: Any, n: int):
        self.expression = _coerce_expression(expression)
        self.n = n

    def as_sql(self, dialect: str = "sqlite") -> tuple[str, list[Any]]:
        expr_sql, expr_params = self.expression.as_sql(dialect)
        return f"NTH_VALUE({expr_sql}, ?)", expr_params + [self.n]


class Window(Expression):
    """
    Window expression: wraps an aggregate or window function with OVER (...).

    Args:
        expression: The window function or aggregate (e.g. Rank(), Sum('amount')).
        partition_by: Field name(s) or Expression(s) for PARTITION BY.
            Accepts: str, F(), list of str/F().
        order_by: Ordering for ORDER BY inside the window.
            Accepts: str (prefix '-' for DESC), OrderBy, or list of those.
        frame: Optional WindowFrame for ROWS/RANGE frame clause.
    """

    def __init__(
        self,
        expression: Expression,
        *,
        partition_by: str | list[str | Expression] | None = None,
        order_by: str | list[str] | OrderBy | list[OrderBy] | None = None,
        frame: WindowFrame | None = None,
    ):
        self.expression = expression

        self.partition_by = []
        if partition_by is not None:
            if not isinstance(partition_by, list):
                partition_by = [partition_by]
            for pb in partition_by:
                if isinstance(pb, str):
                    self.partition_by.append(F(pb))
                else:
                    self.partition_by.append(pb)

        self.order_by = []
        if order_by is not None:
            if not isinstance(order_by, list):
                order_by = [order_by]
            for ob in order_by:
                if isinstance(ob, str):
                    if ob.startswith("-"):
                        self.order_by.append(OrderBy(F(ob[1:]), descending=True))
                    else:
                        self.order_by.append(OrderBy(F(ob)))
                else:
                    self.order_by.append(ob)

        self.frame = frame

    def as_sql(self, dialect: str = "sqlite") -> tuple[str, list[Any]]:
        """
        Render as 'FUNC() OVER (PARTITION BY ... ORDER BY ... FRAME)'.
        Backend check: raise QueryFault on sqlite < 3.25 conceptually
        (we emit a warning comment, actual SQLite 3.25+ supports windows).
        """
        func_sql, params = self.expression.as_sql(dialect)

        over_parts = []

        if self.partition_by:
            pb_sqls = []
            for pb in self.partition_by:
                sql, p = pb.as_sql(dialect)
                pb_sqls.append(sql)
                params.extend(p)
            over_parts.append(f"PARTITION BY {', '.join(pb_sqls)}")

        if self.order_by:
            ob_sqls = []
            for ob in self.order_by:
                sql, p = ob.as_sql(dialect)
                ob_sqls.append(sql)
                params.extend(p)
            over_parts.append(f"ORDER BY {', '.join(ob_sqls)}")

        if self.frame:
            over_parts.append(self.frame.as_sql())

        over_clause = " ".join(over_parts)
        return f"{func_sql} OVER ({over_clause})", params
