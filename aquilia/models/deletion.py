"""
Aquilia Model Deletion -- on_delete behaviors for ForeignKey fields.

Provides constants and handler functions for CASCADE, SET_NULL,
PROTECT, SET_DEFAULT, SET(), DO_NOTHING, RESTRICT behaviors.

Usage:
    from aquilia.models.deletion import CASCADE, SET_NULL, PROTECT, SET

    class Post(Model):
        author = ForeignKey(User, on_delete=CASCADE)

    class Comment(Model):
        author = ForeignKey(User, on_delete=SET(get_sentinel_user))
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from .sql_builder import DeleteBuilder, UpdateBuilder

if TYPE_CHECKING:
    pass

logger = logging.getLogger("aquilia.models.deletion")

# Import fault classes for fault-system integration
from ..faults.domains import ProtectedDeleteFault, RestrictedDeleteFault

__all__ = [
    "CASCADE",
    "SET_NULL",
    "PROTECT",
    "SET_DEFAULT",
    "SET",
    "DO_NOTHING",
    "RESTRICT",
    "OnDeleteHandler",
    "ProtectedError",
    "RestrictedError",
    "normalize_on_delete",
]


# String constants matching SQL behavior (for backward compat with
# existing ForeignKey(on_delete="CASCADE") usage)
CASCADE = "CASCADE"
SET_NULL = "SET NULL"
PROTECT = "PROTECT"
SET_DEFAULT = "SET DEFAULT"
DO_NOTHING = "DO NOTHING"
RESTRICT = "RESTRICT"

# Normalization map for flexible on_delete string matching
_ON_DELETE_ALIASES = {
    "CASCADE": CASCADE,
    "SET_NULL": SET_NULL,
    "SET NULL": SET_NULL,
    "SETNULL": SET_NULL,
    "PROTECT": PROTECT,
    "SET_DEFAULT": SET_DEFAULT,
    "SET DEFAULT": SET_DEFAULT,
    "SETDEFAULT": SET_DEFAULT,
    "DO_NOTHING": DO_NOTHING,
    "DO NOTHING": DO_NOTHING,
    "DONOTHING": DO_NOTHING,
    "RESTRICT": RESTRICT,
}


def normalize_on_delete(action: Any) -> Any:
    """
    Normalize an ``on_delete`` value to its canonical constant string.

    Accepts the flexible spellings a user might write on a ForeignKey
    (``"SET_NULL"``, ``"SET NULL"``, ``"SETNULL"``, any case, with
    surrounding whitespace) and maps them all to the single canonical form
    used internally (e.g. ``SET_NULL = "SET NULL"``). ``SET`` instances
    (from ``SET(value)``/``SET(callable)``) are returned unchanged --
    normalization only applies to the string-constant behaviors.

    Args:
        action: The raw ``on_delete`` value from a ForeignKey -- one of
            the module constants, an equivalent string spelling, a
            ``SET`` instance, or (defensively) anything else.

    Returns:
        The canonical constant string, the original ``SET`` instance, or,
        if ``action`` is a string that doesn't match any known alias, the
        original string unchanged. Callers that need strict validation
        must check the result against the known constants themselves --
        this function does not raise on unrecognized values.
    """
    if isinstance(action, SET):
        return action
    if isinstance(action, str):
        upper = action.upper().strip()
        return _ON_DELETE_ALIASES.get(upper, action)
    return action


class OnDeleteHandler:
    """
    Callable that implements on_delete behavior at the application level.

    ForeignKey's ``on_delete=`` is *not* enforced by a SQL-level
    ``REFERENCES ... ON DELETE`` clause in the generated schema -- Aquilia
    implements every on_delete behavior itself, in Python, by issuing
    separate DELETE/UPDATE statements against the referencing table before
    deleting the target row. ``Model.delete_instance()`` (see
    ``aquilia/models/base.py``) looks up every model with a ForeignKey
    pointing at the instance's class via ``_get_reverse_fk_refs()``,
    builds one ``OnDeleteHandler`` per reference, and calls
    :meth:`handle` for each -- all within the same DB transaction as the
    final DELETE, so a failure partway through (e.g. a PROTECT check)
    rolls back any cascading already performed.

    Supports the string constants (``CASCADE``, ``SET_NULL``, ``PROTECT``,
    ``SET_DEFAULT``, ``DO_NOTHING``, ``RESTRICT``) and ``SET`` instances
    uniformly -- construct directly or via :meth:`for_action`.

    Caveat -- cascades are only one level deep: deleting a CASCADE-linked
    row does not recursively re-run on_delete handling for *its* own
    referencing rows (no grandchild cascading), since the cascade DELETE
    is issued as raw SQL rather than by calling ``delete_instance()`` on
    each affected row. Multi-level CASCADE chains (A -> B -> C) will only
    remove B's rows when A is deleted; C's rows referencing B are left
    behind unless the database schema itself enforces
    ``ON DELETE CASCADE`` at the SQL level.
    """

    def __init__(self, action: Any, value: Any = None):
        """
        Args:
            action: An on_delete string constant (or equivalent alias
                string, normalized via :func:`normalize_on_delete`), or a
                ``SET`` instance. If a ``SET`` instance is given, ``value``
                is ignored -- the value/callable is taken from the ``SET``
                instance itself.
            value: The replacement value to use when ``action`` normalizes
                to ``SET_DEFAULT``. Unused for every other action.
        """
        if isinstance(action, SET):
            self._set_instance = action
            self.action = "_SET_CALLABLE"
            self.value = None
        else:
            self._set_instance = None
            self.action = normalize_on_delete(action)
            self.value = value

    async def handle(
        self,
        db,
        source_model,
        target_field_name: str,
        pk_value: Any,
    ) -> int:
        """
        Execute the on_delete action against ``source_model``'s table for
        every row whose FK column (``target_field_name``) equals
        ``pk_value`` -- i.e. every row that references the object about to
        be deleted.

        Behavior per action (SQL actually issued):
            - ``CASCADE``: ``DELETE FROM <table> WHERE <fk_col> = ?`` --
              removes every referencing row outright.
            - ``SET_NULL``: ``UPDATE <table> SET <fk_col> = NULL WHERE
              <fk_col> = ?``.
            - ``SET_DEFAULT``: same UPDATE, but sets ``<fk_col>`` to
              ``self.value`` (the value passed to ``__init__``) instead of
              NULL.
            - ``SET(...)`` (``self.action == "_SET_CALLABLE"``): same
              UPDATE, but the value is computed by calling
              ``self._set_instance.resolve()`` at delete time (so a
              callable can e.g. look up a "deleted user" sentinel PK).
            - ``PROTECT``: runs a ``SELECT COUNT(*)`` first; if any
              referencing rows exist, raises :class:`ProtectedError`
              *without* modifying anything, aborting the whole delete
              (since this runs inside the same transaction as the delete,
              raising here rolls back any cascading already performed for
              other FKs).
            - ``RESTRICT``: identical check/behavior to ``PROTECT`` at the
              application level (raises :class:`RestrictedError` instead)
              -- the two are kept as distinct actions/exceptions so callers
              can distinguish "protected" from "restricted" semantics, but
              today they behave the same in Python. RESTRICT is intended
              to additionally mirror SQL-level ``ON DELETE RESTRICT`` when
              the database enforces real FK constraints; Aquilia's
              generated schema does not add such constraints, so in
              practice this check is the only enforcement.
            - ``DO_NOTHING`` or any unrecognized action: no-op, returns 0.

        Args:
            db: Database/connection used to execute the generated SQL.
            source_model: The Model class whose table holds the FK column
                (i.e. the model that references the object being deleted --
                NOT the model being deleted).
            target_field_name: Column name of the FK on ``source_model``'s
                table.
            pk_value: The (already DB-coerced) primary key value of the
                object being deleted.

        Returns:
            Number of rows affected by the DELETE/UPDATE (``0`` for
            PROTECT/RESTRICT when no referencing rows exist, and for
            DO_NOTHING/unrecognized actions).

        Raises:
            ProtectedError: If ``action`` is ``PROTECT`` and at least one
                referencing row exists.
            RestrictedError: If ``action`` is ``RESTRICT`` and at least one
                referencing row exists.
        """
        table = source_model._table_name

        if self.action == CASCADE:
            builder = DeleteBuilder(table)
            builder.where(f'"{target_field_name}" = ?', pk_value)
            sql, params = builder.build()
            cursor = await db.execute(sql, params)
            return cursor.rowcount

        elif self.action == SET_NULL:
            builder = UpdateBuilder(table)
            builder.set_dict({target_field_name: None})
            builder.where(f'"{target_field_name}" = ?', pk_value)
            sql, params = builder.build()
            cursor = await db.execute(sql, params)
            return cursor.rowcount

        elif self.action == SET_DEFAULT:
            default_val = self.value
            builder = UpdateBuilder(table)
            builder.set_dict({target_field_name: default_val})
            builder.where(f'"{target_field_name}" = ?', pk_value)
            sql, params = builder.build()
            cursor = await db.execute(sql, params)
            return cursor.rowcount

        elif self.action == "_SET_CALLABLE":
            # SET(value) or SET(callable)
            set_value = self._set_instance.resolve()
            builder = UpdateBuilder(table)
            builder.set_dict({target_field_name: set_value})
            builder.where(f'"{target_field_name}" = ?', pk_value)
            sql, params = builder.build()
            cursor = await db.execute(sql, params)
            return cursor.rowcount

        elif self.action == PROTECT:
            # Check if there are referencing rows
            row = await db.fetch_one(
                f'SELECT COUNT(*) as cnt FROM "{table}" WHERE "{target_field_name}" = ?',
                [pk_value],
            )
            count = row.get("cnt", 0) if row else 0
            if count > 0:
                raise ProtectedError(
                    f"Cannot delete: {count} {source_model.__name__} record(s) reference this object",
                    protected_objects=count,
                )
            return 0

        elif self.action == RESTRICT:
            # Similar to PROTECT but semantically different -- RESTRICT
            # is meant to mirror SQL RESTRICT (checked at DB level too)
            row = await db.fetch_one(
                f'SELECT COUNT(*) as cnt FROM "{table}" WHERE "{target_field_name}" = ?',
                [pk_value],
            )
            count = row.get("cnt", 0) if row else 0
            if count > 0:
                raise RestrictedError(
                    f"Cannot delete: {source_model.__name__} records reference this object (RESTRICT)",
                    restricted_objects=count,
                )
            return 0

        else:
            # DO_NOTHING or unrecognized -- no application-level action
            return 0

    @classmethod
    def for_action(cls, action: Any) -> OnDeleteHandler:
        """
        Factory method -- create an ``OnDeleteHandler`` from any raw
        ``on_delete`` value declared on a ForeignKey.

        Equivalent to calling the constructor directly, but normalizes
        plain string actions first via :func:`normalize_on_delete` (``SET``
        instances are passed straight through either way, since
        ``OnDeleteHandler.__init__`` already special-cases them). Prefer
        this over ``OnDeleteHandler(action)`` when ``action`` may be an
        unnormalized alias string coming straight from user-facing field
        configuration.
        """
        if isinstance(action, SET):
            return cls(action)
        return cls(normalize_on_delete(action))


class SET:
    """
    Factory for SET(value) / SET(callable) on_delete behavior.

    When the referenced object is deleted, set the FK column to the
    given value -- or call the given callable to compute the value.

    Usage:
        # Static value
        author = ForeignKey(User, on_delete=SET(0))

        # Callable (invoked at delete time)
        def get_sentinel_user():
            return 1  # sentinel user PK

        author = ForeignKey(User, on_delete=SET(get_sentinel_user))
    """

    def __init__(self, value: Any):
        """
        Args:
            value: A literal replacement value (e.g. ``0`` for a sentinel
                user PK), or a zero-argument callable invoked at delete
                time (via :meth:`resolve`) to compute the replacement --
                useful when the sentinel needs to be looked up dynamically
                rather than hardcoded.
        """
        self._value = value

    @property
    def value(self) -> Any:
        """The raw value or callable passed to ``__init__`` (for backward compatibility)."""
        return self._value

    def resolve(self) -> Any:
        """
        Resolve the SET value -- call it if it's a callable, otherwise
        return it as-is.

        Called by :meth:`OnDeleteHandler.handle` at the moment the
        cascading UPDATE is executed, so a callable can compute a
        different value on every delete (e.g. look up the current
        "deleted user" sentinel row).
        """
        if callable(self._value):
            return self._value()
        return self._value

    def __repr__(self) -> str:
        """Return ``SET(value)`` using the raw (unresolved) value/callable."""
        return f"SET({self._value!r})"

    def __eq__(self, other: Any) -> bool:
        """Two ``SET`` instances are equal iff their raw (unresolved) values/callables compare equal."""
        if isinstance(other, SET):
            return self._value == other._value
        return NotImplemented

    def __hash__(self) -> int:
        """Hash by the raw value; falls back to hashing by ``id()`` if the value itself is unhashable."""
        try:
            return hash(("SET", self._value))
        except TypeError:
            return hash(("SET", id(self._value)))


class ProtectedError(ProtectedDeleteFault, Exception):
    """Raised when trying to delete a protected object.

    Raised by :meth:`OnDeleteHandler.handle` when a ForeignKey with
    ``on_delete=PROTECT`` still has one or more rows referencing the
    object being deleted. Raised *before* any SQL for the delete itself
    (or later cascades for other FKs) executes further, and since
    ``delete_instance()`` runs the whole cascade inside one transaction,
    letting this propagate rolls back anything already cascaded for
    earlier FKs in the same delete.

    Inherits from ``ProtectedDeleteFault`` (Aquilia fault pipeline --
    carries ``code="PROTECTED_DELETE"``, structured ``metadata``, and
    flows through the standard fault middleware/logging) and ``Exception``
    (so existing ``except ProtectedError`` / ``except Exception`` call
    sites written before the fault-pipeline integration keep working
    unchanged).
    """

    def __init__(self, message: str, protected_objects: int = 0):
        """
        Args:
            message: Human-readable explanation, e.g. how many rows of
                which model reference the object.
            protected_objects: Count of referencing rows found, exposed
                as ``self.protected_objects`` and mirrored into the
                underlying fault's ``metadata["protected_count"]``.
        """
        self.protected_objects = protected_objects
        ProtectedDeleteFault.__init__(
            self,
            model="<protected>",
            reason=message,
            protected_count=protected_objects,
        )
        self.args = (message,)


class RestrictedError(RestrictedDeleteFault, Exception):
    """Raised when trying to delete a restricted object.

    Raised by :meth:`OnDeleteHandler.handle` when a ForeignKey with
    ``on_delete=RESTRICT`` still has one or more rows referencing the
    object being deleted. At the application level this behaves
    identically to :class:`ProtectedError`/``PROTECT`` -- the distinction
    exists to mirror SQL's separate ``PROTECT``/``RESTRICT`` semantics
    (RESTRICT additionally being enforced at the DB level when real FK
    constraints exist) and to let callers distinguish the two cases by
    exception type.

    Inherits from ``RestrictedDeleteFault`` (Aquilia fault pipeline --
    carries ``code="RESTRICTED_DELETE"`` and structured ``metadata``) and
    ``Exception`` (backward compatibility with existing except clauses).
    """

    def __init__(self, message: str, restricted_objects: int = 0):
        """
        Args:
            message: Human-readable explanation, e.g. how many rows of
                which model reference the object.
            restricted_objects: Count of referencing rows found, exposed
                as ``self.restricted_objects`` and mirrored into the
                underlying fault's ``metadata["restricted_count"]``.
        """
        self.restricted_objects = restricted_objects
        RestrictedDeleteFault.__init__(
            self,
            model="<restricted>",
            reason=message,
            restricted_count=restricted_objects,
        )
        self.args = (message,)
