"""
Aquilia migrations -- operation base class and registry.

Defines the contract every migration operation implements, plus the registry
that lets a serialized migration file name an operation and get the class back.
Third-party and project-local operations register here too, which is what makes
the operation set extensible without patching the framework.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from dataclasses import fields as dataclass_fields
from enum import Enum
from typing import TYPE_CHECKING, Any, ClassVar

from aquilia.faults.domains import MigrationFault

if TYPE_CHECKING:
    from aquilia.models.migration.backends import SchemaBackend, Statement
    from aquilia.models.migration.schema import ProjectState

__all__ = [
    "OperationCategory",
    "Operation",
    "register_operation",
    "resolve_operation",
    "registered_operations",
]


class OperationCategory(Enum):
    """Broad classification of what an operation changes.

    Used by the optimizer to decide which operations may be reordered relative
    to each other, and by plan output to group related changes.

    Attributes:
        MODEL: Creates, drops, renames, or reconfigures a table.
        FIELD: Adds, drops, alters, or renames a column.
        INDEX: Adds, drops, or alters an index.
        CONSTRAINT: Adds, drops, or alters a table constraint.
        RELATION: Manages a many-to-many junction table.
        DATA: Moves or transforms row data rather than schema.
        SPECIAL: Raw SQL or arbitrary Python; makes no guarantees.
    """

    MODEL = "model"
    FIELD = "field"
    INDEX = "index"
    CONSTRAINT = "constraint"
    RELATION = "relation"
    DATA = "data"
    SPECIAL = "special"


@dataclass(frozen=True)
class Operation:
    """Base class for every migration operation.

    Subclasses are frozen dataclasses. Immutability matters here: the optimizer
    reorders and merges operations, the serializer writes them to disk, and the
    planner replays them against state -- an operation that mutated itself
    during any of those would produce a different migration on the second run.

    Subclasses must implement :meth:`state_forwards` and
    :meth:`database_forwards`, and should implement :meth:`reverse` where the
    change can be undone.

    Class attributes:
        category: What kind of change this makes; see :class:`OperationCategory`.
        reversible: Whether :meth:`reverse` returns a real inverse. When
            ``False``, a rollback plan annotates the operation rather than
            failing the whole rollback.
        destructive: Whether applying this loses data. Surfaced in plan output.
        atomic: Whether this may run inside a transaction. ``False`` for
            operations that emit non-transactional statements.
    """

    category: ClassVar[OperationCategory] = OperationCategory.SPECIAL
    reversible: ClassVar[bool] = True
    destructive: ClassVar[bool] = False
    atomic: ClassVar[bool] = True

    # ── Contract ────────────────────────────────────────────────────────

    def state_forwards(self, state: ProjectState) -> None:
        """Apply this operation's effect to *state*, in place.

        Args:
            state: The project state to mutate. Callers that need the original
                preserved must clone it first.

        Raises:
            NotImplementedError: Base implementation; subclasses must override.
        """
        raise NotImplementedError(f"{type(self).__name__} must implement state_forwards(state).")

    def database_forwards(self, state: ProjectState, backend: SchemaBackend) -> list[Statement]:
        """Emit the statements that apply this operation to a database.

        Args:
            state: Project state *before* this operation is applied, so the
                operation can read the schema it is about to change.
            backend: The dialect backend to render statements with.

        Returns:
            Statements in execution order.

        Raises:
            NotImplementedError: Base implementation; subclasses must override.
        """
        raise NotImplementedError(f"{type(self).__name__} must implement database_forwards(state, backend).")

    def reverse(self) -> Operation | None:
        """Return the operation that undoes this one.

        Returns:
            The inverse operation, or ``None`` when this change cannot be
            mechanically reversed. Returning ``None`` -- rather than raising, as
            raising would -- lets a rollback plan annotate the gap and continue with
            the operations that *can* be reversed.

        Example:
            >>> AddField(model="User", field=bio).reverse()
            RemoveField(model='User', field=bio)
        """
        return None

    def describe(self) -> str:
        """Return a one-line human-readable summary for plan and status output.

        Returns:
            A short description, e.g. ``"Add field User.bio"``.
        """
        return type(self).__name__

    # ── Introspection helpers ───────────────────────────────────────────

    def references_model(self, model: str) -> bool:
        """Return whether this operation touches *model*.

        Used by the optimizer to decide whether two operations may be reordered,
        and by the graph builder to compute inter-migration dependencies.

        Args:
            model: A model class name.

        Returns:
            ``True`` when the operation reads or writes that model.
        """
        return getattr(self, "model", None) == model

    def evolve(self, **changes: Any) -> Operation:
        """Return a copy of this operation with *changes* applied.

        Args:
            **changes: Field names and their new values.

        Returns:
            A new operation instance; this one is unmodified.
        """
        return replace(self, **changes)

    # ── Serialization ───────────────────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        """Serialize this operation to a JSON-safe, deterministic dict.

        The default implementation walks the subclass's dataclass fields in
        declaration order and serializes each value, recursing into schema-state
        objects. Subclasses rarely need to override it.

        Returns:
            A dict tagged with ``operation`` (the registered name) plus one key
            per dataclass field.
        """
        data: dict[str, Any] = {"operation": type(self).__name__}
        for spec in dataclass_fields(self):
            data[spec.name] = _serialize(getattr(self, spec.name))
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Operation:
        """Rebuild an operation from :meth:`to_dict` output.

        Args:
            data: Serialized operation data, carrying an ``operation`` key.

        Returns:
            The reconstructed operation.

        Raises:
            MigrationFault: If the named operation is not registered, or if the
                data is missing a required field.
        """
        name = data.get("operation")
        target = resolve_operation(name or "")

        # An operation whose fields need more than field-wise deserialization --
        # RunPython, whose callables must be re-imported -- overrides from_dict.
        # Dispatch to it, unless we are already inside that override.
        own = target.__dict__.get("from_dict")
        if own is not None and target is not cls:
            return own.__func__(target, data)

        kwargs: dict[str, Any] = {}
        for spec in dataclass_fields(target):
            if spec.name in data:
                kwargs[spec.name] = _deserialize(spec.name, data[spec.name], target)
        try:
            return target(**kwargs)
        except MigrationFault:
            raise
        except TypeError as exc:
            raise MigrationFault(
                migration="operation",
                reason=(
                    f"Cannot reconstruct operation {name!r} from serialized data: {exc}. "
                    f"The migration file may have been written by an incompatible "
                    f"Aquilia version."
                ),
            ) from exc


# ── Registry ────────────────────────────────────────────────────────────────

_OPERATIONS: dict[str, type[Operation]] = {}


def register_operation(operation_cls: type[Operation]) -> type[Operation]:
    """Register an operation class so serialized migrations can resolve it.

    Usable as a decorator. Custom operations must be registered before any
    migration referencing them is loaded -- typically at module import time in
    the project package that defines them.

    Args:
        operation_cls: The operation class to register.

    Returns:
        *operation_cls* unchanged, so this works as a decorator.

    Raises:
        MigrationFault: If a *different* class is already registered under the
            same name. Silently overwriting would make an existing migration
            file mean something new.

    Example:
        >>> @register_operation
        ... class EnablePostgresExtension(Operation):
        ...     ...
    """
    name = operation_cls.__name__
    existing = _OPERATIONS.get(name)
    if existing is not None and existing is not operation_cls:
        raise MigrationFault(
            migration="operation",
            reason=(
                f"An operation named {name!r} is already registered "
                f"({existing.__module__}.{existing.__qualname__}). Operation names must "
                f"be unique because migration files reference them by name."
            ),
        )
    _OPERATIONS[name] = operation_cls
    return operation_cls


def resolve_operation(name: str) -> type[Operation]:
    """Look up a registered operation class by name.

    Args:
        name: The operation class name as written in a migration file.

    Returns:
        The operation class.

    Raises:
        MigrationFault: If no operation is registered under *name*.
    """
    _ensure_builtins()
    target = _OPERATIONS.get(name)
    if target is None:
        raise MigrationFault(
            migration="operation",
            reason=(
                f"Unknown migration operation {name!r}. Known operations: "
                f"{', '.join(sorted(_OPERATIONS))}. Custom operations must be "
                f"registered with register_operation() before the migration loads."
            ),
        )
    return target


def registered_operations() -> tuple[str, ...]:
    """Return the sorted names of every registered operation."""
    _ensure_builtins()
    return tuple(sorted(_OPERATIONS))


_BUILTINS_LOADED = False


def _ensure_builtins() -> None:
    """Import the built-in operation modules so their registrations run."""
    global _BUILTINS_LOADED
    if _BUILTINS_LOADED:
        return
    _BUILTINS_LOADED = True
    from aquilia.models.migration.operations import (  # noqa: F401
        constraints,
        fields,
        indexes,
        models,
        relations,
        special,
    )


# ── Serialization helpers ───────────────────────────────────────────────────


def _serialize(value: Any) -> Any:
    """Recursively convert schema-state objects and containers to JSON-safe data."""
    if hasattr(value, "to_dict") and not isinstance(value, type):
        return value.to_dict()
    if isinstance(value, (list, tuple)):
        return [_serialize(item) for item in value]
    if isinstance(value, frozenset):
        return sorted(_serialize(item) for item in value)
    if isinstance(value, dict):
        return {k: _serialize(value[k]) for k in sorted(value)}
    return value


_STATE_FIELDS: dict[str, str] = {
    "table": "TableState",
    "old_table": "TableState",
    "new_table": "TableState",
    "field": "ColumnState",
    "old_field": "ColumnState",
    "new_field": "ColumnState",
    "index": "IndexState",
    "old_index": "IndexState",
    "new_index": "IndexState",
    "constraint": "ConstraintState",
    "old_constraint": "ConstraintState",
    "new_constraint": "ConstraintState",
    "relation": "ManyToManyState",
}


def _deserialize(field_name: str, value: Any, owner: type[Operation]) -> Any:
    """Rebuild a schema-state object from serialized data, by field name.

    Args:
        field_name: The dataclass field being populated, which determines which
            state class to reconstruct.
        value: The serialized value.
        owner: The operation class being reconstructed, used only for errors.

    Returns:
        The reconstructed value.
    """
    from aquilia.models.migration import schema as schema_module

    state_class = _STATE_FIELDS.get(field_name)
    if state_class is None or value is None:
        if isinstance(value, list):
            return tuple(value)
        return value

    target = getattr(schema_module, state_class)
    if isinstance(value, list):
        return tuple(target.from_dict(item) for item in value)
    if isinstance(value, dict):
        return target.from_dict(value)
    return value
