"""
Aquilia CTE (Common Table Expression) System.

Supports:
- Non-recursive CTEs: WITH name AS (SELECT ...)
- Recursive CTEs: WITH RECURSIVE name AS (anchor UNION [ALL] recursive)
- Multiple CTEs in dependency order
- Integration with Q.with_cte() and Q.recursive_cte()
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .expression import Expression

if TYPE_CHECKING:
    pass

__all__ = ["CTEReference", "CTE", "RecursiveCTE", "CTECol"]


class CTECol(Expression):
    """Renders 'cte_name'.'column'."""

    def __init__(self, cte_name: str, column: str):
        self.cte_name = cte_name
        self.column = column

    def as_sql(self, dialect: str = "sqlite") -> tuple[str, list[Any]]:
        return f'"{self.cte_name}"."{self.column}"', []


class CTEReference:
    """Reference to a named CTE for use inside recursive queries."""

    def __init__(self, name: str, columns: list[str] | None = None):
        self.name = name
        self.columns = columns

    def col(self, column: str) -> CTECol:
        return CTECol(self.name, column)


class CTE:
    """
    A named Common Table Expression wrapping a QuerySet.

    Created via Q.cte(name). Register into a query with Q.with_cte(cte).
    """

    def __init__(self, name: str, queryset: Any):
        self._name = name
        self.queryset = queryset

    @property
    def name(self) -> str:
        return self._name

    def as_sql(self, dialect: str = "sqlite") -> tuple[str, list[Any]]:
        """Render as 'name AS (SELECT ...)'."""
        sql, params = self.queryset._build_select()
        return f'"{self.name}" AS ({sql})', params

    def col(self, column: str) -> CTECol:
        return CTECol(self.name, column)


class RecursiveCTE:
    """
    A recursive CTE: WITH RECURSIVE name AS (anchor UNION [ALL] recursive_part).
    """

    def __init__(
        self,
        name: str,
        anchor_qs: Any,
        recursive_qs: Any,
        union_all: bool = True,
    ):
        self._name = name
        self.anchor_qs = anchor_qs
        self.recursive_qs = recursive_qs
        self.union_all = union_all

    @property
    def name(self) -> str:
        return self._name

    def as_sql(self, dialect: str = "sqlite") -> tuple[str, list[Any]]:
        """
        Render as 'name AS (anchor UNION [ALL] recursive_part)'.
        """
        anchor_sql, anchor_params = self.anchor_qs._build_select()
        recursive_sql, recursive_params = self.recursive_qs._build_select()
        union = "UNION ALL" if self.union_all else "UNION"
        body = f"{anchor_sql} {union} {recursive_sql}"
        return f'"{self.name}" AS ({body})', anchor_params + recursive_params

    def col(self, column: str) -> CTECol:
        return CTECol(self.name, column)
