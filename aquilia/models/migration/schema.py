"""
Aquilia migrations -- schema state model.

This module defines the *state* layer of this migration system: an
immutable, fully-typed description of a database schema that preserves the
original model semantics instead of flattening them into primitive column
definitions.

Design rationale
----------------
Reducing every :class:`~aquilia.models.fields_module.Field` to a handful of
primitive attributes (name, SQL type, a few booleans) destroys information at the
very first hop of the pipeline, long before any SQL is produced -- and no amount
of care downstream can recover it. Generated-column expressions, many-to-many
relationships, index access methods, operator classes, partial-index predicates,
composite primary keys, ``unique_together``, collations, and comments all live
outside that primitive set.

The state layer is therefore built directly from live ``Field`` objects via
:meth:`Field.deconstruct`, and every state object retains enough information to
reconstruct its field faithfully. SQL generation is deferred to
:mod:`aquilia.models.migration.backends`, the *only* layer permitted to know
about dialects.

Layering
--------
::

    Model classes ──> schema.py (this module)  ──> operations/  ──> backends/
                      immutable state              state deltas     SQL text

Nothing in this module emits SQL, and nothing in this module imports a
backend. That separation is what makes operations backend-independent and
serialization deterministic.

Determinism
-----------
Every collection exposed here is an ordered ``tuple``, and every mapping is
iterated through ``sorted()`` at construction time. Two runs of the same
models -- in different processes, with different ``PYTHONHASHSEED`` values --
produce byte-identical state and therefore byte-identical migrations. Iterating
a raw ``set`` anywhere in this path would instead give a different operation
order on every interpreter run.

Example
-------
::

    from aquilia.models.migration.schema import ProjectState

    state = ProjectState.from_models([User, Post])
    table = state.tables["Post"]
    assert table.db_table == "posts"
    assert table.columns["author"].reference.table == "users"
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, Any, Literal

from ...faults.domains import MigrationFault

if TYPE_CHECKING:
    from ..base import Model
    from ..fields_module import Field

__all__ = [
    "STATE_VERSION",
    "NOT_PROVIDED",
    "NotProvided",
    "OnDelete",
    "IndexMethod",
    "Reference",
    "ColumnState",
    "IndexState",
    "ConstraintState",
    "CheckConstraintState",
    "UniqueConstraintState",
    "ExclusionConstraintState",
    "PrimaryKeyConstraintState",
    "ForeignKeyConstraintState",
    "TableState",
    "ProjectState",
    "normalize_referential_action",
]


logger = logging.getLogger("aquilia.models.migration.schema")

STATE_VERSION = 2
"""Serialized-state format version, written into every snapshot artifact.

Bumped only on a breaking change to the on-disk shape. Readers use it to
refuse a snapshot they cannot interpret rather than silently misreading it.
"""


# ── Sentinel ────────────────────────────────────────────────────────────────


class NotProvided:
    """Singleton marker meaning "no value was supplied", distinct from ``None``.

    Three states must be distinguishable for a column default:

    * no ``DEFAULT`` clause at all -- :data:`NOT_PROVIDED`
    * ``DEFAULT NULL`` -- ``None``
    * ``DEFAULT <value>`` -- anything else

    Using ``None`` for the first case would collide with the second, which is a
    real and load-bearing distinction: a nullable column with an explicit
    ``DEFAULT NULL`` behaves differently under ``INSERT`` than one with no
    default at all.

    Compare with ``is NOT_PROVIDED``; the type is falsy so ``if state.default:``
    reads naturally as "has a truthy default".
    """

    _instance: NotProvided | None = None

    def __new__(cls) -> NotProvided:
        """Return the one shared instance, creating it on first call."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        """Render as ``<NOT_PROVIDED>`` in tracebacks and ``repr()`` output."""
        return "<NOT_PROVIDED>"

    def __bool__(self) -> Literal[False]:
        """Always falsy, so "no default" and "falsy default" read alike in conditionals."""
        return False

    def __deepcopy__(self, memo: dict) -> NotProvided:
        """Return ``self`` -- the sentinel is a singleton and must survive ``deepcopy``."""
        return self

    def __copy__(self) -> NotProvided:
        """Return ``self`` -- the sentinel is a singleton and must survive ``copy``."""
        return self

    def __reduce__(self) -> str:
        """Pickle by name so unpickling yields the same singleton instance."""
        return "NOT_PROVIDED"


NOT_PROVIDED = NotProvided()
"""The sole :class:`NotProvided` instance. Test with ``is NOT_PROVIDED``."""


# ── Enumerated vocabularies ─────────────────────────────────────────────────

OnDelete = Literal["CASCADE", "SET NULL", "SET DEFAULT", "RESTRICT", "NO ACTION"]
"""Valid SQL referential actions, in their canonical (space-separated) spelling.

Aquilia model code accepts Python-style aliases (``"SET_NULL"``,
``"DO_NOTHING"``, ``"PROTECT"``); :func:`normalize_referential_action`
canonicalizes them on the way into state, so everything downstream of this
module sees only these five values and never has to re-normalize.
"""

IndexMethod = Literal["BTREE", "HASH", "GIN", "GIST", "BRIN", "SPGIST"]
"""Index access methods. Backends downgrade unsupported methods to ``BTREE``."""


_REFERENTIAL_ACTIONS: dict[str, OnDelete] = {
    "CASCADE": "CASCADE",
    "SET_NULL": "SET NULL",
    "SET NULL": "SET NULL",
    "SETNULL": "SET NULL",
    "SET_DEFAULT": "SET DEFAULT",
    "SET DEFAULT": "SET DEFAULT",
    "SETDEFAULT": "SET DEFAULT",
    "RESTRICT": "RESTRICT",
    "PROTECT": "RESTRICT",
    "NO_ACTION": "NO ACTION",
    "NO ACTION": "NO ACTION",
    "DO_NOTHING": "NO ACTION",
    "DO NOTHING": "NO ACTION",
    "DONOTHING": "NO ACTION",
}


def normalize_referential_action(action: str) -> OnDelete:
    """Canonicalize a referential action to its SQL spelling.

    Args:
        action: A Python-style constant (``"SET_NULL"``, ``"PROTECT"``,
            ``"DO_NOTHING"``) or an already-valid SQL keyword phrase
            (``"SET NULL"``). Case and surrounding whitespace are ignored.

    Returns:
        One of the five :data:`OnDelete` values.

    Raises:
        MigrationFault: If *action* is not a recognized referential action.
            Passing an unknown value straight through into DDL turns a
            typo like ``on_delete="CASCAED"`` into a syntax error surfacing at
            migration-apply time against a production database. Failing here
            surfaces it at model-import time instead.

    Example:
        >>> normalize_referential_action("set_null")
        'SET NULL'
    """
    key = action.upper().strip()
    resolved = _REFERENTIAL_ACTIONS.get(key)
    if resolved is None:
        raise MigrationFault(
            migration="schema-state",
            reason=(
                f"Unknown referential action {action!r}. Valid actions are: "
                f"CASCADE, SET NULL, SET DEFAULT, RESTRICT, NO ACTION "
                f"(Python aliases SET_NULL / DO_NOTHING / PROTECT are also accepted)."
            ),
        )
    return resolved


# ── Reference ───────────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class Reference:
    """A resolved foreign-key target: which table and column a column points at.

    Held by :attr:`ColumnState.reference`. Both a symbolic model name and a
    concrete table name are retained: the model name survives table renames and
    is what a human reads in a migration file, while the table name is what the
    backend actually emits. Storing a lowercased guess at the table name instead
    breaks whenever a model's ``Meta.table_name`` differs from its class name.

    Attributes:
        model: Target model's class name (e.g. ``"User"``). Symbolic; stable
            across table renames.
        table: Target database table name (e.g. ``"users"``).
        column: Target column name, normally the target's primary key.
        on_delete: Referential action when the referenced row is deleted.
        on_update: Referential action when the referenced key is updated.
        deferrable: Emit ``DEFERRABLE INITIALLY DEFERRED``. PostgreSQL only;
            other backends ignore it.
        db_constraint: When ``False``, the relationship is tracked in state and
            used for dependency ordering, but no SQL ``REFERENCES`` clause is
            emitted. Mirrors ``ForeignKey(db_constraint=False)``.
    """

    model: str
    table: str
    column: str = "id"
    on_delete: OnDelete = "CASCADE"
    on_update: OnDelete = "CASCADE"
    deferrable: bool = False
    db_constraint: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain JSON-safe dict, omitting default-valued keys.

        Returns:
            A dict always containing ``model``, ``table``, and ``column``, plus
            only those of ``on_delete``/``on_update``/``deferrable``/
            ``db_constraint`` that differ from their defaults. Omitting
            defaults keeps snapshots compact and, more importantly, keeps them
            stable when a default changes meaning in a later release.
        """
        data: dict[str, Any] = {"model": self.model, "table": self.table, "column": self.column}
        if self.on_delete != "CASCADE":
            data["on_delete"] = self.on_delete
        if self.on_update != "CASCADE":
            data["on_update"] = self.on_update
        if self.deferrable:
            data["deferrable"] = True
        if not self.db_constraint:
            data["db_constraint"] = False
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Reference:
        """Rebuild a :class:`Reference` from :meth:`to_dict` output.

        Args:
            data: A dict with at least ``table``; ``model`` falls back to the
                table name and ``column`` to ``"id"`` so that snapshots written
                by older releases still load.

        Returns:
            The reconstructed reference.
        """
        return cls(
            model=data.get("model") or data["table"],
            table=data["table"],
            column=data.get("column", "id"),
            on_delete=normalize_referential_action(data.get("on_delete", "CASCADE")),
            on_update=normalize_referential_action(data.get("on_update", "CASCADE")),
            deferrable=bool(data.get("deferrable", False)),
            db_constraint=bool(data.get("db_constraint", True)),
        )


# ── ColumnState ─────────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class ColumnState:
    """Immutable description of one database column, preserving field semantics.

    This is the state a migration records for one column. The critical property is
    :attr:`field_class` and :attr:`field_kwargs`: rather than storing only a
    resolved SQL type string, a ``ColumnState`` retains the originating field
    class and its full constructor arguments. That means the exact
    :class:`~aquilia.models.fields_module.Field` can be reconstructed --
    a ``GeneratedField``'s expression, an ``EnumField``'s member list, a
    ``DecimalField``'s precision all survive the round trip through a snapshot
    file and back.

    The SQL type is *derived*, not stored as the source of truth: backends call
    :meth:`sql_type` which delegates to the reconstructed field, so a custom
    user-defined field with its own ``sql_type()`` works automatically with no
    changes to the migration system. A hardcoded ``type_map`` would
    silently fell through to ``TEXT`` for anything it did not recognize.

    Attributes:
        name: Python attribute name on the model (e.g. ``"author"``).
        column: Database column name (e.g. ``"author_id"``). Differs from
            :attr:`name` for foreign keys and any field with ``db_column`` set.
            Operations must always emit :attr:`column`; emitting :attr:`name`
            is the classic bug that generates ``DROP COLUMN "author"`` for a column
            actually named ``author_id``.
        field_class: Concrete field class name (e.g. ``"CharField"``).
        field_kwargs: The field's ``deconstruct()`` output minus the keys
            promoted to explicit attributes below. Ordered deterministically.
        primary_key: Whether this column participates in the primary key.
        unique: Whether a single-column ``UNIQUE`` constraint applies.
        null: Whether ``NULL`` is permitted.
        default: Default value, or :data:`NOT_PROVIDED` for no default clause.
        db_index: Whether a plain index should be created for this column.
        reference: Foreign-key target, or ``None``.
        generated: SQL expression for a generated column, or ``None``.
        generated_stored: ``True`` for ``STORED``, ``False`` for ``VIRTUAL``.
            Only meaningful when :attr:`generated` is set.
        collation: Column collation (e.g. ``"C"``, ``"utf8mb4_bin"``), or ``None``.
        comment: Column comment for ``COMMENT ON COLUMN`` / inline ``COMMENT``.
        auto_increment: Whether the database assigns this column's value.
            Derived from the field class being an auto-field -- never inferred
            from "primary key and integer-ish type", which is a bug that
            turned natural integer keys into ``AUTOINCREMENT`` columns.
    """

    name: str
    column: str
    field_class: str
    # Participates in equality: a change to max_length, max_digits, or any other
    # field argument is a real schema change. Excluding it from comparison would
    # make `CharField(max_length=20)` and `CharField(max_length=300)` compare
    # equal, so the autodetector would never emit an AlterField for a widened
    # column.
    field_kwargs: dict[str, Any] = field(default_factory=dict)
    primary_key: bool = False
    unique: bool = False
    null: bool = False
    default: Any = NOT_PROVIDED
    db_index: bool = False
    reference: Reference | None = None
    generated: str | None = None
    generated_stored: bool = True
    collation: str | None = None
    comment: str = ""
    auto_increment: bool = False

    # ── Construction from a live Field ──────────────────────────────────

    @classmethod
    def from_field(
        cls,
        name: str,
        fld: Field,
        *,
        resolve_table: Any = None,
    ) -> ColumnState:
        """Build a :class:`ColumnState` from a live model field.

        This is the single point at which model semantics enter the migration
        system. It reads the field's own ``deconstruct()`` output rather than
        introspecting attributes ad hoc, so any field that correctly implements
        ``deconstruct()`` -- including third-party and user-defined fields --
        round-trips without the migration system knowing about it.

        Args:
            name: The Python attribute name the field is bound to on the model.
            fld: The bound :class:`~aquilia.models.fields_module.Field` instance.
            resolve_table: Optional callable ``(to_ref) -> (model_name, table,
                pk_column)`` used to resolve a foreign key's target. Supplied by
                :meth:`TableState.from_model`, which has the full model list in
                scope. When ``None``, foreign keys resolve to a best-effort
                lowercase table name.

        Returns:
            The immutable column state.

        Raises:
            MigrationFault: If the field declares an unrecognized ``on_delete``
                or ``on_update`` action.

        Note:
            Many-to-many fields are *not* columns and must never be passed
            here; :meth:`TableState.from_model` routes them to
            :attr:`TableState.m2m` instead. Dropping them here would mean no
            junction table was ever created by a generated migration.
        """
        from ..fields_module import UNSET, AutoField, BigAutoField, ForeignKey, OneToOneField, SmallAutoField

        kwargs = dict(fld.deconstruct())
        field_class = kwargs.pop("type", type(fld).__name__)

        # Promote schema-significant keys to explicit attributes so diffing and
        # backends never have to reach into the opaque kwargs bag.
        primary_key = bool(kwargs.pop("primary_key", False))
        unique = bool(kwargs.pop("unique", False))
        null = bool(kwargs.pop("null", False))
        db_index = bool(kwargs.pop("db_index", False))
        kwargs.pop("db_column", None)

        raw_default = getattr(fld, "default", UNSET)
        if raw_default is UNSET or callable(raw_default):
            # A callable default is applied in Python at INSERT time and has no
            # SQL representation. Recording it as a literal would bake one
            # evaluation into the DDL forever (e.g. freezing `datetime.now` to
            # the moment makemigrations ran).
            default: Any = NOT_PROVIDED
            kwargs.pop("default", None)
        else:
            default = kwargs.pop("default", raw_default)

        reference: Reference | None = None
        if isinstance(fld, (ForeignKey, OneToOneField)):
            target = getattr(fld, "to", None)
            if resolve_table is not None:
                model_name, table_name, pk_column = resolve_table(target)
            else:
                model_name = target if isinstance(target, str) else getattr(target, "__name__", str(target))
                table_name = model_name.lower()
                pk_column = "id"
            reference = Reference(
                model=model_name,
                table=table_name,
                column=pk_column,
                on_delete=normalize_referential_action(getattr(fld, "on_delete", "CASCADE")),
                on_update=normalize_referential_action(getattr(fld, "on_update", "CASCADE")),
                db_constraint=bool(getattr(fld, "db_constraint", True)),
            )
            kwargs.pop("to", None)
            kwargs.pop("on_delete", None)
            kwargs.pop("on_update", None)
            kwargs.pop("related_name", None)

        generated = getattr(fld, "expression", None) if field_class == "GeneratedField" else None
        if generated is not None:
            # Promoted to explicit attributes; keeping them in field_kwargs too
            # would duplicate them into rebuild_field()'s constructor call.
            kwargs.pop("expression", None)
            kwargs.pop("db_persist", None)
        auto_increment = isinstance(fld, (AutoField, BigAutoField, SmallAutoField))

        return cls(
            name=name,
            column=fld.column_name or name,
            field_class=field_class,
            field_kwargs=_ordered(kwargs),
            primary_key=primary_key,
            unique=unique,
            null=null,
            default=default,
            db_index=db_index,
            reference=reference,
            generated=generated,
            generated_stored=bool(getattr(fld, "db_persist", True)),
            collation=getattr(fld, "db_collation", None),
            comment=getattr(fld, "help_text", "") or "",
            auto_increment=auto_increment,
        )

    @classmethod
    def of(
        cls,
        name: str,
        fld: Field,
        *,
        column: str | None = None,
        reference: Reference | None = None,
        generated: str | None = None,
        generated_stored: bool | None = None,
        collation: str | None = None,
        comment: str = "",
    ) -> ColumnState:
        """Build a column from a live field, overriding what a field cannot know.

        This is the constructor generated migration files use. A migration is
        read and edited by hand, so it names a real
        :class:`~aquilia.models.fields_module.Field` -- ``CharField(max_length=200)``
        -- rather than a dict of primitives. The field supplies every argument it
        was constructed with; the keyword arguments here supply the few facts that
        are resolved from the *project*, not the field, and so cannot be recovered
        from an unbound field instance.

        Args:
            name: The Python attribute name on the model.
            fld: The field instance, constructed exactly as it appears on the model.
            column: Database column name, when it differs from *name*. Required for
                a foreign key, whose column is ``author_id`` for an attribute
                ``author``.
            reference: The resolved foreign-key target. A field holds only a
                symbolic ``to="User"``; which *table* and *column* that names is a
                project-level fact, so a migration records it explicitly and stays
                correct even after the target model's ``Meta.table_name`` changes.
            generated: SQL expression for a generated column. Defaults to the
                field's own ``expression`` when it has one.
            generated_stored: ``True`` for ``STORED``, ``False`` for ``VIRTUAL``.
            collation: Column collation.
            comment: Column comment.

        Returns:
            The immutable column state.

        Raises:
            MigrationFault: If the field declares an unrecognized referential action.

        Example:
            >>> ColumnState.of("title", CharField(max_length=200, db_index=True))
            ColumnState(name='title', column='title', field_class='CharField', ...)

            >>> ColumnState.of(
            ...     "author",
            ...     ForeignKey("User", on_delete="CASCADE"),
            ...     column="author_id",
            ...     reference=Reference(model="User", table="users"),
            ... )
            ColumnState(name='author', column='author_id', ...)
        """
        state = cls.from_field(name, fld)
        changes: dict[str, Any] = {}
        if column is not None:
            changes["column"] = column
        if reference is not None:
            changes["reference"] = reference
        if generated is not None:
            changes["generated"] = generated
        if generated_stored is not None:
            changes["generated_stored"] = generated_stored
        if collation is not None:
            changes["collation"] = collation
        if comment:
            changes["comment"] = comment
        return state.evolve(**changes) if changes else state

    # ── Field reconstruction ────────────────────────────────────────────

    def rebuild_field(self) -> Field:
        """Reconstruct the originating :class:`Field` instance from this state.

        This is what allows a migration file loaded from disk to produce
        byte-identical DDL to the one produced from live models: rather than
        re-deriving a SQL type from a stored string, the actual field is
        rebuilt and asked for its own type. Custom fields work with no
        special-casing.

        Returns:
            A field instance equivalent to the one this state was built from.
            It is unbound (no owning model), which is sufficient for
            ``sql_type()`` and ``sql_column_def()``.

        Raises:
            MigrationFault: If :attr:`field_class` names a class that is not
                importable from :mod:`aquilia.models.fields_module` or
                :mod:`aquilia.models.fields`. This surfaces a renamed or
                deleted custom field at plan time, rather than as a confusing
                ``TEXT`` column at apply time.
        """
        field_cls = _lookup_field_class(self.field_class)
        kwargs: dict[str, Any] = dict(self.field_kwargs)
        kwargs.update(
            null=self.null,
            unique=self.unique,
            primary_key=self.primary_key,
            db_index=self.db_index,
        )
        if self.default is not NOT_PROVIDED:
            kwargs["default"] = self.default
        if self.reference is not None:
            kwargs["to"] = self.reference.model
            kwargs["on_delete"] = self.reference.on_delete
            kwargs["on_update"] = self.reference.on_update
            kwargs["db_constraint"] = self.reference.db_constraint
        if self.generated is not None:
            kwargs["expression"] = self.generated
            kwargs["db_persist"] = self.generated_stored

        # A nested field (GeneratedField.output_field) is serialized as its own
        # deconstruct() dict; rebuild it into a live instance so the outer
        # field can resolve its SQL type from it.
        nested = kwargs.get("output_field")
        if isinstance(nested, dict):
            kwargs["output_field"] = ColumnState(
                name=self.name,
                column=self.column,
                field_class=nested.get("type", "TextField"),
                field_kwargs=_ordered({k: v for k, v in nested.items() if k != "type"}),
            ).rebuild_field()

        try:
            instance = field_cls(**_drop_unsupported(field_cls, kwargs))
        except MigrationFault:
            raise
        except Exception as exc:  # pragma: no cover -- defensive
            raise MigrationFault(
                migration="schema-state",
                reason=(
                    f"Cannot reconstruct field {self.field_class!r} for column "
                    f"{self.column!r}: {exc}. The field's __init__ signature may have "
                    f"changed since this migration was generated."
                ),
            ) from exc

        instance.name = self.column
        instance.attr_name = self.name
        return instance

    def sql_type(self, dialect: str) -> str:
        """Return the SQL column type for *dialect*, delegated to the real field.

        Args:
            dialect: Target dialect name (``"sqlite"``, ``"postgresql"``,
                ``"mysql"``, ``"oracle"``).

        Returns:
            The dialect-specific type string, e.g. ``"VARCHAR(200)"``.

        Raises:
            MigrationFault: Propagated from :meth:`rebuild_field` if the field
                class cannot be resolved.
        """
        return self.rebuild_field().sql_type(dialect)

    # ── Serialization ───────────────────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a deterministic, JSON-safe dict.

        Keys are emitted in a fixed order and default-valued keys are omitted,
        so two equal states always produce byte-identical JSON. That property is
        what makes the snapshot checksum meaningful.

        Returns:
            The serialized column state.
        """
        data: dict[str, Any] = {
            "name": self.name,
            "column": self.column,
            "field_class": self.field_class,
        }
        if self.field_kwargs:
            data["field_kwargs"] = _ordered(self.field_kwargs)
        for key, value in (
            ("primary_key", self.primary_key),
            ("unique", self.unique),
            ("null", self.null),
            ("db_index", self.db_index),
            ("auto_increment", self.auto_increment),
        ):
            if value:
                data[key] = True
        if self.default is not NOT_PROVIDED:
            data["default"] = self.default
        if self.reference is not None:
            data["reference"] = self.reference.to_dict()
        if self.generated is not None:
            data["generated"] = self.generated
            data["generated_stored"] = self.generated_stored
        if self.collation:
            data["collation"] = self.collation
        if self.comment:
            data["comment"] = self.comment
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ColumnState:
        """Rebuild a :class:`ColumnState` from :meth:`to_dict` output.

        Args:
            data: Serialized column state.

        Returns:
            The reconstructed state, byte-identical on re-serialization.
        """
        ref = data.get("reference")
        return cls(
            name=data["name"],
            column=data.get("column", data["name"]),
            field_class=data["field_class"],
            field_kwargs=_ordered(data.get("field_kwargs", {})),
            primary_key=bool(data.get("primary_key", False)),
            unique=bool(data.get("unique", False)),
            null=bool(data.get("null", False)),
            default=data.get("default", NOT_PROVIDED),
            db_index=bool(data.get("db_index", False)),
            reference=Reference.from_dict(ref) if ref else None,
            generated=data.get("generated"),
            generated_stored=bool(data.get("generated_stored", True)),
            collation=data.get("collation"),
            comment=data.get("comment", ""),
            auto_increment=bool(data.get("auto_increment", False)),
        )

    def evolve(self, **changes: Any) -> ColumnState:
        """Return a copy of this state with *changes* applied.

        The state is frozen; this is the supported way to derive a modified
        column (used by ``AlterField`` when applying itself to project state).

        Args:
            **changes: Attribute names and their new values.

        Returns:
            A new :class:`ColumnState`; this instance is unmodified.

        Example:
            >>> widened = column.evolve(null=True)
        """
        return replace(self, **changes)


# ── IndexState ──────────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class IndexState:
    """Immutable description of a database index.

    An index reduced to ``{name, columns, unique}`` loses everything else, and
    thereby silently downgraded a partial GIN index with operator classes into
    a plain B-tree index, or emitted ``CREATE INDEX "fx" ON "t" ()`` for an
    expression index whose expression it had discarded -- this retains the full
    index definition.

    Attributes:
        name: Index name. Required; :func:`auto_index_name` supplies a
            deterministic default when the model does not name it.
        columns: Plain column names, in index order. Order is significant
            (leftmost-prefix matching). Mutually exclusive with
            :attr:`expressions` in practice, though both may be set for a
            mixed index on backends that allow it.
        expressions: SQL expressions forming index keys, e.g. ``'LOWER("email")'``.
        unique: Emit ``CREATE UNIQUE INDEX``.
        method: Access method. Backends downgrade to ``BTREE`` where unsupported.
        condition: Predicate for a partial index (``WHERE (...)``), or ``None``.
        opclasses: Per-column operator classes, positionally aligned with
            :attr:`columns` (e.g. ``("gin_trgm_ops",)``).
        include: Non-key columns for a covering index (PostgreSQL ``INCLUDE``).
        tablespace: Tablespace for the index, or ``None``.
        comment: Index comment.

    Warning:
        :attr:`expressions` and :attr:`condition` are interpolated into DDL
        verbatim. They are trusted developer-authored SQL, never user input.
    """

    name: str
    columns: tuple[str, ...] = ()
    expressions: tuple[str, ...] = ()
    unique: bool = False
    method: IndexMethod = "BTREE"
    condition: str | None = None
    opclasses: tuple[str, ...] = ()
    include: tuple[str, ...] = ()
    tablespace: str | None = None
    comment: str = ""

    def __post_init__(self) -> None:
        """Validate that the index has at least one key.

        Raises:
            MigrationFault: If neither :attr:`columns` nor :attr:`expressions`
                is populated. Otherwise an expression index renders as
                ``CREATE INDEX "fx" ON "posts" ();`` -- a syntax error that
                surfaces only when the migration is applied.
        """
        if not self.columns and not self.expressions:
            raise MigrationFault(
                migration="schema-state",
                reason=(
                    f"Index {self.name!r} has neither columns nor expressions. "
                    f"An index must have at least one key. If this came from a "
                    f"FunctionalIndex, ensure its `expression` argument is set."
                ),
            )

    @property
    def keys(self) -> tuple[str, ...]:
        """All index keys -- columns first, then expressions, in emission order."""
        return self.columns + self.expressions

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a deterministic, JSON-safe dict, omitting defaults."""
        data: dict[str, Any] = {"name": self.name}
        if self.columns:
            data["columns"] = list(self.columns)
        if self.expressions:
            data["expressions"] = list(self.expressions)
        if self.unique:
            data["unique"] = True
        if self.method != "BTREE":
            data["method"] = self.method
        if self.condition:
            data["condition"] = self.condition
        if self.opclasses:
            data["opclasses"] = list(self.opclasses)
        if self.include:
            data["include"] = list(self.include)
        if self.tablespace:
            data["tablespace"] = self.tablespace
        if self.comment:
            data["comment"] = self.comment
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> IndexState:
        """Rebuild an :class:`IndexState` from :meth:`to_dict` output."""
        return cls(
            name=data["name"],
            columns=tuple(data.get("columns", ())),
            expressions=tuple(data.get("expressions", ())),
            unique=bool(data.get("unique", False)),
            method=data.get("method", "BTREE"),
            condition=data.get("condition"),
            opclasses=tuple(data.get("opclasses", ())),
            include=tuple(data.get("include", ())),
            tablespace=data.get("tablespace"),
            comment=data.get("comment", ""),
        )


def auto_index_name(table: str, keys: tuple[str, ...] | list[str], *, unique: bool = False) -> str:
    """Generate a deterministic index name for an unnamed index.

    The name is derived from the table and keys, with non-identifier characters
    replaced so that expression indexes produce a valid name too. A short hash
    suffix is appended when truncation is needed, keeping the result within the
    63-character identifier limit shared by PostgreSQL and MySQL while staying
    collision-free and stable across runs.

    Args:
        table: Table the index belongs to.
        keys: Column names and/or expressions being indexed.
        unique: Whether the index is unique; selects the ``uidx``/``idx`` prefix.

    Returns:
        A deterministic, valid index identifier.

    Example:
        >>> auto_index_name("users", ["email"])
        'idx_users_email'
        >>> auto_index_name("users", ['LOWER("email")'], unique=True)
        'uidx_users_lower_email'
    """
    prefix = "uidx" if unique else "idx"
    parts = []
    for key in keys:
        cleaned = "".join(ch if ch.isalnum() else "_" for ch in str(key)).strip("_").lower()
        cleaned = "_".join(seg for seg in cleaned.split("_") if seg)
        parts.append(cleaned)
    body = "_".join(p for p in parts if p)
    name = f"{prefix}_{table}_{body}" if body else f"{prefix}_{table}"
    if len(name) <= 63:
        return name
    digest = hashlib.sha256(name.encode()).hexdigest()[:8]
    return f"{name[:54]}_{digest}"


# ── Constraints ─────────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class ConstraintState:
    """Base class for all table-level constraints.

    Representing constraints as raw SQL strings (``constraint_sql``) forces the
    system to
    regex-parsed them downstream to decide whether they could be translated
    into an index on SQLite. That made constraints undiffable (any whitespace
    change read as a modification), unreversible, and impossible to validate.

    Each constraint kind is modelled as a distinct typed subclass. The SQL is
    generated by the backend from structured data, never parsed back out of it.

    Attributes:
        name: Constraint name. Required -- an unnamed constraint cannot be
            dropped or diffed reliably.
    """

    name: str

    @property
    def kind(self) -> str:
        """Discriminator written into serialized output (e.g. ``"check"``)."""
        raise NotImplementedError

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-safe dict tagged with :attr:`kind`."""
        raise NotImplementedError

    @staticmethod
    def from_dict(data: dict[str, Any]) -> ConstraintState:
        """Rebuild the appropriate constraint subclass from serialized data.

        Args:
            data: A dict produced by any constraint's ``to_dict()``, carrying a
                ``kind`` discriminator.

        Returns:
            The reconstructed constraint.

        Raises:
            MigrationFault: If ``kind`` is unrecognized. Refusing an unknown
                constraint is safer than dropping it, which would silently
                remove a data-integrity guarantee from the schema.
        """
        kind = data.get("kind")
        subclass = _CONSTRAINT_KINDS.get(kind or "")
        if subclass is None:
            raise MigrationFault(
                migration="schema-state",
                reason=(
                    f"Unknown constraint kind {kind!r} in schema state. "
                    f"Known kinds: {', '.join(sorted(_CONSTRAINT_KINDS))}."
                ),
            )
        return subclass._load(data)

    @classmethod
    def _load(cls, data: dict[str, Any]) -> ConstraintState:
        """Subclass hook for deserialization; see each subclass's override."""
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class CheckConstraintState(ConstraintState):
    """A ``CHECK (expression)`` constraint.

    Attributes:
        name: Constraint name.
        check: Boolean SQL expression rows must satisfy, e.g. ``"price > 0"``.

    Warning:
        :attr:`check` is interpolated into DDL verbatim -- trusted developer
        SQL only, never user input.
    """

    check: str = ""

    @property
    def kind(self) -> str:
        """Always ``"check"``."""
        return "check"

    def to_dict(self) -> dict[str, Any]:
        """Serialize to ``{"kind": "check", "name": ..., "check": ...}``."""
        return {"kind": "check", "name": self.name, "check": self.check}

    @classmethod
    def _load(cls, data: dict[str, Any]) -> CheckConstraintState:
        """Rebuild from serialized data."""
        return cls(name=data["name"], check=data.get("check", ""))


@dataclass(frozen=True, slots=True)
class UniqueConstraintState(ConstraintState):
    """A ``UNIQUE (columns...)`` constraint, optionally partial or expression-based.

    Attributes:
        name: Constraint name.
        columns: Column names that must be jointly unique.
        expressions: SQL expressions that must be jointly unique. A constraint
            with expressions cannot be a table constraint on any backend and is
            emitted as a unique index instead -- the backend decides, not a
            regex over generated SQL.
        condition: Predicate restricting which rows the constraint covers.
            Forces index-based emission.
        deferrable: Emit ``DEFERRABLE INITIALLY DEFERRED`` (PostgreSQL).
        include: Covering columns (PostgreSQL).
    """

    columns: tuple[str, ...] = ()
    expressions: tuple[str, ...] = ()
    condition: str | None = None
    deferrable: bool = False
    include: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Validate that the constraint covers at least one column or expression.

        Raises:
            MigrationFault: If both :attr:`columns` and :attr:`expressions` are
                empty, which would emit ``UNIQUE ()``.
        """
        if not self.columns and not self.expressions:
            raise MigrationFault(
                migration="schema-state",
                reason=f"UniqueConstraint {self.name!r} covers no columns or expressions.",
            )

    @property
    def kind(self) -> str:
        """Always ``"unique"``."""
        return "unique"

    @property
    def requires_index(self) -> bool:
        """Whether this must be emitted as a unique index rather than a table constraint.

        True when the constraint is partial or expression-based -- no SQL
        dialect supports either form as an inline table constraint.
        """
        return bool(self.expressions or self.condition)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a deterministic dict, omitting defaults."""
        data: dict[str, Any] = {"kind": "unique", "name": self.name}
        if self.columns:
            data["columns"] = list(self.columns)
        if self.expressions:
            data["expressions"] = list(self.expressions)
        if self.condition:
            data["condition"] = self.condition
        if self.deferrable:
            data["deferrable"] = True
        if self.include:
            data["include"] = list(self.include)
        return data

    @classmethod
    def _load(cls, data: dict[str, Any]) -> UniqueConstraintState:
        """Rebuild from serialized data."""
        return cls(
            name=data["name"],
            columns=tuple(data.get("columns", ())),
            expressions=tuple(data.get("expressions", ())),
            condition=data.get("condition"),
            deferrable=bool(data.get("deferrable", False)),
            include=tuple(data.get("include", ())),
        )


@dataclass(frozen=True, slots=True)
class ExclusionConstraintState(ConstraintState):
    """A PostgreSQL ``EXCLUDE USING method (col WITH op, ...)`` constraint.

    Attributes:
        name: Constraint name.
        expressions: ``(column_or_expression, operator)`` pairs, e.g.
            ``(("room_id", "="), ("during", "&&"))``.
        method: Index access method backing the constraint (default ``GIST``).
        condition: Predicate restricting covered rows.
        deferrable: Emit ``DEFERRABLE INITIALLY DEFERRED``.

    Note:
        Backends that do not support exclusion constraints report this via
        their capability flags; the operation then raises rather than silently
        emitting a comment, so an unsupported integrity guarantee is never
        quietly dropped.
    """

    expressions: tuple[tuple[str, str], ...] = ()
    method: IndexMethod = "GIST"
    condition: str | None = None
    deferrable: bool = False

    @property
    def kind(self) -> str:
        """Always ``"exclude"``."""
        return "exclude"

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a deterministic dict, omitting defaults."""
        data: dict[str, Any] = {
            "kind": "exclude",
            "name": self.name,
            "expressions": [list(pair) for pair in self.expressions],
            "method": self.method,
        }
        if self.condition:
            data["condition"] = self.condition
        if self.deferrable:
            data["deferrable"] = True
        return data

    @classmethod
    def _load(cls, data: dict[str, Any]) -> ExclusionConstraintState:
        """Rebuild from serialized data."""
        return cls(
            name=data["name"],
            expressions=tuple((pair[0], pair[1]) for pair in data.get("expressions", ())),
            method=data.get("method", "GIST"),
            condition=data.get("condition"),
            deferrable=bool(data.get("deferrable", False)),
        )


@dataclass(frozen=True, slots=True)
class PrimaryKeyConstraintState(ConstraintState):
    """An explicit, possibly composite, ``PRIMARY KEY (columns...)`` constraint.

    Used when the primary key spans more than one column. Single-column keys
    are expressed through :attr:`ColumnState.primary_key` instead, which lets
    the backend emit the inline form. There is no inline form for composite
    keys at all.

    Attributes:
        name: Constraint name.
        columns: Ordered columns forming the key.
    """

    columns: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Validate the key covers at least one column.

        Raises:
            MigrationFault: If :attr:`columns` is empty.
        """
        if not self.columns:
            raise MigrationFault(
                migration="schema-state",
                reason=f"PrimaryKeyConstraint {self.name!r} covers no columns.",
            )

    @property
    def kind(self) -> str:
        """Always ``"primary_key"``."""
        return "primary_key"

    def to_dict(self) -> dict[str, Any]:
        """Serialize to ``{"kind": "primary_key", "name": ..., "columns": [...]}``."""
        return {"kind": "primary_key", "name": self.name, "columns": list(self.columns)}

    @classmethod
    def _load(cls, data: dict[str, Any]) -> PrimaryKeyConstraintState:
        """Rebuild from serialized data."""
        return cls(name=data["name"], columns=tuple(data.get("columns", ())))


@dataclass(frozen=True, slots=True)
class ForeignKeyConstraintState(ConstraintState):
    """A named, possibly composite, table-level ``FOREIGN KEY`` constraint.

    Column-level references are carried by :attr:`ColumnState.reference` and
    emitted inline. This class covers the cases that cannot be inline: a
    composite foreign key, or one that must be added after table creation to
    break a circular dependency between two tables.

    Attributes:
        name: Constraint name.
        columns: Local columns forming the key.
        target: Referenced table name.
        target_columns: Referenced columns, positionally aligned with
            :attr:`columns`.
        on_delete: Referential action on delete.
        on_update: Referential action on update.
        deferrable: Emit ``DEFERRABLE INITIALLY DEFERRED``.
    """

    columns: tuple[str, ...] = ()
    target: str = ""
    target_columns: tuple[str, ...] = ()
    on_delete: OnDelete = "CASCADE"
    on_update: OnDelete = "CASCADE"
    deferrable: bool = False

    def __post_init__(self) -> None:
        """Validate that local and target column counts match.

        Raises:
            MigrationFault: If the two column tuples differ in length, which
                would produce a foreign key the database rejects.
        """
        if not self.columns or not self.target_columns:
            raise MigrationFault(
                migration="schema-state",
                reason=f"ForeignKeyConstraint {self.name!r} is missing local or target columns.",
            )
        if len(self.columns) != len(self.target_columns):
            raise MigrationFault(
                migration="schema-state",
                reason=(
                    f"ForeignKeyConstraint {self.name!r} references "
                    f"{len(self.target_columns)} target column(s) from "
                    f"{len(self.columns)} local column(s); counts must match."
                ),
            )

    @property
    def kind(self) -> str:
        """Always ``"foreign_key"``."""
        return "foreign_key"

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a deterministic dict, omitting defaults."""
        data: dict[str, Any] = {
            "kind": "foreign_key",
            "name": self.name,
            "columns": list(self.columns),
            "target": self.target,
            "target_columns": list(self.target_columns),
        }
        if self.on_delete != "CASCADE":
            data["on_delete"] = self.on_delete
        if self.on_update != "CASCADE":
            data["on_update"] = self.on_update
        if self.deferrable:
            data["deferrable"] = True
        return data

    @classmethod
    def _load(cls, data: dict[str, Any]) -> ForeignKeyConstraintState:
        """Rebuild from serialized data."""
        return cls(
            name=data["name"],
            columns=tuple(data.get("columns", ())),
            target=data.get("target", ""),
            target_columns=tuple(data.get("target_columns", ())),
            on_delete=normalize_referential_action(data.get("on_delete", "CASCADE")),
            on_update=normalize_referential_action(data.get("on_update", "CASCADE")),
            deferrable=bool(data.get("deferrable", False)),
        )


_CONSTRAINT_KINDS: dict[str, type[ConstraintState]] = {
    "check": CheckConstraintState,
    "unique": UniqueConstraintState,
    "exclude": ExclusionConstraintState,
    "primary_key": PrimaryKeyConstraintState,
    "foreign_key": ForeignKeyConstraintState,
}


# ── M2M ─────────────────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class ManyToManyState:
    """A many-to-many relationship and the junction table it implies.

    Without this state, ``ManyToManyField`` would be absent from snapshots and
    from initial-schema planning: a generated migration would never create the
    junction table, and the relationship would be broken at runtime on any
    database built from migrations.

    Attributes:
        name: Attribute name of the field on the owning model.
        table: Junction table name.
        source_column: Column referencing the owning model.
        target_column: Column referencing the related model.
        source_table: Owning model's table.
        target_table: Related model's table.
        source_target_column: Referenced column on the owning table.
        target_target_column: Referenced column on the related table.
        through: Name of an explicit through-model, or ``None`` for an implicit
            junction table. When set, the developer owns that table's schema and
            the migration system creates nothing.
    """

    name: str
    table: str
    source_column: str
    target_column: str
    source_table: str
    target_table: str
    source_target_column: str = "id"
    target_target_column: str = "id"
    through: str | None = None

    @property
    def implicit(self) -> bool:
        """Whether the migration system owns this junction table's schema."""
        return self.through is None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a deterministic dict, omitting defaults."""
        data: dict[str, Any] = {
            "name": self.name,
            "table": self.table,
            "source_column": self.source_column,
            "target_column": self.target_column,
            "source_table": self.source_table,
            "target_table": self.target_table,
        }
        if self.source_target_column != "id":
            data["source_target_column"] = self.source_target_column
        if self.target_target_column != "id":
            data["target_target_column"] = self.target_target_column
        if self.through:
            data["through"] = self.through
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ManyToManyState:
        """Rebuild a :class:`ManyToManyState` from :meth:`to_dict` output."""
        return cls(
            name=data["name"],
            table=data["table"],
            source_column=data["source_column"],
            target_column=data["target_column"],
            source_table=data["source_table"],
            target_table=data["target_table"],
            source_target_column=data.get("source_target_column", "id"),
            target_target_column=data.get("target_target_column", "id"),
            through=data.get("through"),
        )


# ── TableState ──────────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class TableState:
    """Immutable description of one model's table.

    Attributes:
        model: Model class name (e.g. ``"Post"``). The symbolic identity used
            throughout the migration system -- stable across table renames.
        db_table: Database table name (e.g. ``"posts"``).
        columns: Ordered mapping of attribute name to :class:`ColumnState`.
            Declaration order is preserved, since column order is visible in
            ``SELECT *`` and in some drivers' positional row access.
        indexes: Indexes, ordered by name.
        constraints: Table-level constraints, ordered by name.
        m2m: Many-to-many relationships declared on this model, ordered by name.
        options: Model-level options that affect DDL (``tablespace``,
            ``comment``, ``managed``, ``ordering``).
    """

    model: str
    db_table: str
    columns: dict[str, ColumnState] = field(default_factory=dict)
    indexes: tuple[IndexState, ...] = ()
    constraints: tuple[ConstraintState, ...] = ()
    m2m: tuple[ManyToManyState, ...] = ()
    # Participates in equality: a changed tablespace or table comment is a real
    # schema change that AlterModelOptions must be able to detect.
    options: dict[str, Any] = field(default_factory=dict)

    # ── Construction ────────────────────────────────────────────────────

    @classmethod
    def from_model(cls, model_cls: type[Model], *, resolve_table: Any = None) -> TableState:
        """Build a :class:`TableState` from a live model class.

        Collects, in order: column states from non-M2M fields; many-to-many
        relationships; indexes from ``Meta.indexes`` and from ``db_index=True``
        fields; constraints from ``Meta.constraints`` and ``Meta.unique_together``;
        and DDL-relevant ``Meta`` options.

        Args:
            model_cls: The model class to snapshot.
            resolve_table: Optional ``(to_ref) -> (model, table, pk_column)``
                resolver for foreign-key targets, supplied by
                :meth:`ProjectState.from_models`.

        Returns:
            The immutable table state.

        Raises:
            MigrationFault: If a field or ``Meta`` entry is malformed -- e.g. an
                index with no keys, or an unknown referential action.
        """
        from ..fields_module import ManyToManyField

        meta = model_cls._meta
        table = meta.table_name

        columns: dict[str, ColumnState] = {}
        m2m: list[ManyToManyState] = []

        # ``_fields`` and ``_m2m_fields`` are populated separately by the
        # metaclass: a ManyToManyField lives only in ``_m2m_fields``. Both must
        # be walked -- reading only ``_fields`` is why a naive pass never emits a
        # junction table for any many-to-many relationship.
        for attr_name, fld in model_cls._fields.items():
            if isinstance(fld, ManyToManyField):
                continue
            columns[attr_name] = ColumnState.from_field(attr_name, fld, resolve_table=resolve_table)

        for attr_name, fld in sorted(getattr(model_cls, "_m2m_fields", {}).items()):
            m2m.append(_m2m_state(attr_name, fld, model_cls, resolve_table))

        indexes = _collect_indexes(model_cls, table, columns)
        constraints = _collect_constraints(model_cls, table, columns)

        options: dict[str, Any] = {}
        if getattr(meta, "db_tablespace", ""):
            options["tablespace"] = meta.db_tablespace
        if getattr(meta, "ordering", None):
            options["ordering"] = list(meta.ordering)
        if not getattr(meta, "managed", True):
            options["managed"] = False
        comment = getattr(meta, "db_table_comment", "") or ""
        if comment:
            options["comment"] = comment

        return cls(
            model=model_cls.__name__,
            db_table=table,
            columns=columns,
            indexes=tuple(sorted(indexes, key=lambda i: i.name)),
            constraints=tuple(sorted(constraints, key=lambda c: c.name)),
            m2m=tuple(sorted(m2m, key=lambda m: m.name)),
            options=options,
        )

    @classmethod
    def of(
        cls,
        model: str,
        db_table: str,
        *,
        columns: list[ColumnState] | tuple[ColumnState, ...] = (),
        indexes: tuple[IndexState, ...] | list[IndexState] = (),
        constraints: tuple[ConstraintState, ...] | list[ConstraintState] = (),
        m2m: tuple[ManyToManyState, ...] | list[ManyToManyState] = (),
        options: dict[str, Any] | None = None,
    ) -> TableState:
        """Build a table from an ordered column *list*.

        This is the constructor generated migration files use. :attr:`columns` is
        a mapping internally -- lookup by attribute name is the common operation --
        but a mapping written out in source duplicates every column name as its own
        key, which is noise in a file meant to be read and reviewed. This takes the
        list and builds the mapping, preserving declaration order.

        Args:
            model: Model class name.
            db_table: Database table name.
            columns: The table's columns, in declaration order.
            indexes: Index definitions.
            constraints: Table-level constraints.
            m2m: Many-to-many relationships declared on this model.
            options: DDL-relevant ``Meta`` options.

        Returns:
            The immutable table state.

        Example:
            >>> TableState.of(
            ...     "Post",
            ...     "posts",
            ...     columns=[
            ...         ColumnState.of("id", AutoField(primary_key=True)),
            ...         ColumnState.of("title", CharField(max_length=200)),
            ...     ],
            ... )
            TableState(model='Post', db_table='posts', ...)
        """
        return cls(
            model=model,
            db_table=db_table,
            columns={column.name: column for column in columns},
            indexes=tuple(indexes),
            constraints=tuple(constraints),
            m2m=tuple(m2m),
            options=dict(options or {}),
        )

    # ── Queries ─────────────────────────────────────────────────────────

    @property
    def primary_key_columns(self) -> tuple[str, ...]:
        """Database column names forming the primary key, in declaration order.

        Reads an explicit :class:`PrimaryKeyConstraintState` when present
        (composite key), otherwise collects columns flagged
        :attr:`ColumnState.primary_key`.
        """
        for constraint in self.constraints:
            if isinstance(constraint, PrimaryKeyConstraintState):
                return constraint.columns
        return tuple(col.column for col in self.columns.values() if col.primary_key)

    def column_by_db_name(self, db_column: str) -> ColumnState | None:
        """Look up a column by its *database* name rather than its attribute name.

        Args:
            db_column: The database column name (e.g. ``"author_id"``).

        Returns:
            The matching column state, or ``None``.
        """
        for col in self.columns.values():
            if col.column == db_column:
                return col
        return None

    @property
    def referenced_tables(self) -> tuple[str, ...]:
        """Tables this table depends on, deduplicated and sorted.

        Includes column-level foreign keys and table-level foreign-key
        constraints, but excludes self-references (which never constrain
        creation order). Used to order ``CreateModel`` operations so a
        referenced table always exists first, and to order ``DeleteModel``
        operations in reverse.
        """
        targets: set[str] = set()
        for col in self.columns.values():
            if col.reference is not None and col.reference.table != self.db_table:
                targets.add(col.reference.table)
        for constraint in self.constraints:
            if isinstance(constraint, ForeignKeyConstraintState) and constraint.target != self.db_table:
                targets.add(constraint.target)
        return tuple(sorted(targets))

    # ── Serialization ───────────────────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a deterministic, JSON-safe dict."""
        data: dict[str, Any] = {
            "model": self.model,
            "db_table": self.db_table,
            "columns": [col.to_dict() for col in self.columns.values()],
        }
        if self.indexes:
            data["indexes"] = [idx.to_dict() for idx in self.indexes]
        if self.constraints:
            data["constraints"] = [c.to_dict() for c in self.constraints]
        if self.m2m:
            data["m2m"] = [m.to_dict() for m in self.m2m]
        if self.options:
            data["options"] = _ordered(self.options)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TableState:
        """Rebuild a :class:`TableState` from :meth:`to_dict` output."""
        columns = {}
        for col_data in data.get("columns", []):
            col = ColumnState.from_dict(col_data)
            columns[col.name] = col
        return cls(
            model=data["model"],
            db_table=data["db_table"],
            columns=columns,
            indexes=tuple(IndexState.from_dict(d) for d in data.get("indexes", [])),
            constraints=tuple(ConstraintState.from_dict(d) for d in data.get("constraints", [])),
            m2m=tuple(ManyToManyState.from_dict(d) for d in data.get("m2m", [])),
            options=_ordered(data.get("options", {})),
        )

    def evolve(self, **changes: Any) -> TableState:
        """Return a copy of this table state with *changes* applied.

        Args:
            **changes: Attribute names and their new values.

        Returns:
            A new :class:`TableState`; this instance is unmodified.
        """
        return replace(self, **changes)

    def with_column(self, column: ColumnState) -> TableState:
        """Return a copy with *column* added or replaced, preserving order.

        Args:
            column: The column state to insert. Replaces an existing column
                with the same :attr:`ColumnState.name` in place, otherwise
                appends.

        Returns:
            A new :class:`TableState`.
        """
        columns = dict(self.columns)
        columns[column.name] = column
        return replace(self, columns=columns)

    def without_column(self, name: str) -> TableState:
        """Return a copy with the column named *name* removed.

        Args:
            name: Attribute name of the column to drop.

        Returns:
            A new :class:`TableState`. Removing a column that does not exist is
            a no-op rather than an error, so replaying a partially-applied
            migration stays idempotent.
        """
        columns = {k: v for k, v in self.columns.items() if k != name}
        return replace(self, columns=columns)


# ── ProjectState ────────────────────────────────────────────────────────────


@dataclass
class ProjectState:
    """The full schema of every managed model -- the unit that gets diffed.

    A :class:`ProjectState` is built either from live model classes
    (:meth:`from_models`) or from a serialized snapshot (:meth:`from_dict`).
    The autodetector compares two of them; operations mutate one via
    :meth:`apply_operation` to track what the schema looks like partway through
    a migration, which is what makes correct dependency ordering possible.

    Unlike the other classes here this one is mutable, because operations apply
    themselves to it in sequence. Use :meth:`clone` before mutating a state you
    do not own.

    Attributes:
        tables: Mapping of model name to :class:`TableState`, sorted by model
            name for determinism.
        version: State format version; see :data:`STATE_VERSION`.
    """

    tables: dict[str, TableState] = field(default_factory=dict)
    version: int = STATE_VERSION

    # ── Construction ────────────────────────────────────────────────────

    @classmethod
    def from_models(cls, model_classes: list[type[Model]]) -> ProjectState:
        """Build a project state from live model classes.

        Abstract and unmanaged models are skipped: they own no table. Foreign
        keys are resolved against the supplied model list first and the global
        registry second, so a reference to a model outside *model_classes*
        still resolves to its real table name rather than a lowercase guess.

        Args:
            model_classes: The models to snapshot, in any order.

        Returns:
            The project state, with tables sorted by model name.

        Raises:
            MigrationFault: Propagated from field or ``Meta`` validation.

        Example:
            >>> state = ProjectState.from_models([User, Post])
            >>> sorted(state.tables)
            ['Post', 'User']
        """
        by_name = {m.__name__: m for m in model_classes}

        def resolve(to_ref: Any) -> tuple[str, str, str]:
            """Resolve a FK target to ``(model_name, table_name, pk_column)``."""
            target_cls = None
            if isinstance(to_ref, type):
                target_cls = to_ref
            elif isinstance(to_ref, str):
                simple = to_ref.split(".")[-1]
                target_cls = by_name.get(simple)
                if target_cls is None:
                    try:
                        from ..registry import ModelRegistry

                        target_cls = ModelRegistry.get(simple)
                    except Exception:  # pragma: no cover -- registry optional
                        target_cls = None
                if target_cls is None:
                    # Unresolvable forward reference: fall back to a
                    # conventional table name. Recorded symbolically so a later
                    # migration can still repair it.
                    return simple, simple.lower(), "id"

            model_name = target_cls.__name__
            table_name = getattr(target_cls._meta, "table_name", model_name.lower())
            pk_attr = getattr(target_cls, "_pk_attr", "id")
            pk_field = target_cls._fields.get(pk_attr)
            pk_column = getattr(pk_field, "column_name", None) or "id" if pk_field else "id"
            return model_name, table_name, pk_column

        tables: dict[str, TableState] = {}
        for model_cls in sorted(model_classes, key=lambda m: m.__name__):
            meta = model_cls._meta
            if getattr(meta, "abstract", False) or not getattr(meta, "managed", True):
                continue
            tables[model_cls.__name__] = TableState.from_model(model_cls, resolve_table=resolve)

        return cls(tables=tables)

    @classmethod
    async def from_database(
        cls,
        db: Any,
        *,
        model_classes: list[type[Model]] | None = None,
        exclude_tables: tuple[str, ...] = ("aquilia_migrations",),
    ) -> ProjectState:
        """Build state by introspecting a live database.

        Reads the tables, columns, indexes, and foreign keys the database
        actually has, so this state can be diffed against :meth:`from_models` to
        detect schema drift -- a schema changed outside the migration system, or
        a migration that did not apply cleanly.

        The result is necessarily coarser than :meth:`from_models`: a database
        reports storage types, not Aquilia field classes, so the field class is
        inferred from the column type and any field-level semantics the database
        does not store (validators, ``auto_now``, choices) are absent. Diff it
        for *structural* drift, not to regenerate models.

        Args:
            db: A connected :class:`~aquilia.db.engine.AquiliaDatabase`.
            model_classes: Models used to map table names back to model names, so
                a diff reports ``Post`` rather than a name guessed from
                ``posts``. Tables with no matching model get a derived name.
            exclude_tables: Tables to skip. The migration tracking table is
                excluded by default, as is anything the backend reports as
                internal (``sqlite_*``).

        Returns:
            The introspected state, with tables sorted by model name.

        Example:
            >>> live = await ProjectState.from_database(db, model_classes=models)
            >>> operations = detect_changes(live, ProjectState.from_models(models))
        """
        table_to_model = {
            model_cls._meta.table_name: model_cls.__name__
            for model_cls in (model_classes or ())
            if getattr(getattr(model_cls, "_meta", None), "table_name", None)
        }

        # Model state is consulted only where introspection is provably lossy;
        # it never invents a table or column the database does not have.
        declared_states = ProjectState.from_models(list(model_classes)).tables if model_classes else {}

        tables: dict[str, TableState] = {}
        for db_table in await db.get_tables():
            if db_table in exclude_tables or db_table.startswith("sqlite_"):
                continue
            model = table_to_model.get(db_table) or _model_name_from_table(db_table)
            declared = declared_states.get(model)
            tables[model] = await _introspect_table(
                db,
                db_table,
                model,
                table_to_model,
                declared.columns if declared else {},
            )

        return cls(tables=dict(sorted(tables.items())))

    def clone(self) -> ProjectState:
        """Return an independent copy safe to mutate.

        The nested :class:`TableState` objects are frozen and therefore shared
        rather than copied -- mutating the clone replaces entries in its own
        ``tables`` dict without affecting the original.

        Returns:
            A new :class:`ProjectState`.
        """
        return ProjectState(tables=dict(self.tables), version=self.version)

    # ── Queries ─────────────────────────────────────────────────────────

    def table_for(self, db_table: str) -> TableState | None:
        """Find a table state by its *database* table name.

        Args:
            db_table: The database table name (e.g. ``"posts"``).

        Returns:
            The matching table state, or ``None``.
        """
        for table in self.tables.values():
            if table.db_table == db_table:
                return table
        return None

    def resolve(self, identifier: str) -> TableState | None:
        """Find a table state by model name, falling back to database table name.

        Operations address tables by model name, which is the symbolic identity
        that survives a table rename. A database table name is also accepted, since
        hand-written migrations often use one -- the model name is tried first,
        being the canonical key and an exact lookup.

        Args:
            identifier: A model class name or a database table name.

        Returns:
            The matching table state, or ``None``.

        Example:
            >>> state.resolve("Post") is state.resolve("posts")
            True
        """
        table = self.tables.get(identifier)
        if table is not None:
            return table
        return self.table_for(identifier)

    def key_for(self, identifier: str) -> str | None:
        """Return the model-name key for *identifier*, whichever form it takes.

        Args:
            identifier: A model class name or a database table name.

        Returns:
            The model name used as this table's key in :attr:`tables`, or
            ``None`` when no table matches.
        """
        if identifier in self.tables:
            return identifier
        for model, table in self.tables.items():
            if table.db_table == identifier:
                return model
        return None

    def creation_order(self) -> tuple[str, ...]:
        """Return model names ordered so referenced tables are created first.

        Performs a deterministic depth-first topological sort over foreign-key
        dependencies. Cycles -- which are legal, e.g. two models referencing
        each other with one nullable side -- are broken at the point of
        detection rather than raising; the operation layer then defers the
        cycle-closing foreign key to a separate ``AddConstraint``.

        Returns:
            Model names in a valid creation order.

        Example:
            >>> state.creation_order()
            ('User', 'Post', 'Comment')
        """
        table_to_model = {t.db_table: name for name, t in self.tables.items()}
        ordered: list[str] = []
        visited: set[str] = set()
        visiting: set[str] = set()

        def visit(model: str) -> None:
            if model in visited or model in visiting:
                return
            visiting.add(model)
            table = self.tables.get(model)
            if table is not None:
                for dep_table in table.referenced_tables:
                    dep_model = table_to_model.get(dep_table)
                    if dep_model is not None and dep_model != model:
                        visit(dep_model)
            visiting.discard(model)
            visited.add(model)
            ordered.append(model)

        for model in sorted(self.tables):
            visit(model)
        return tuple(ordered)

    def deletion_order(self) -> tuple[str, ...]:
        """Return model names ordered so dependents are dropped before their targets.

        Exactly the reverse of :meth:`creation_order`. Dropping in alphabetical order
        instead fails whenever a parent table is dropped before a child still
        referencing it.

        Returns:
            Model names in a valid deletion order.
        """
        return tuple(reversed(self.creation_order()))

    # ── Mutation ────────────────────────────────────────────────────────

    def apply_operation(self, operation: Any) -> None:
        """Apply an operation's *state* effect to this project state.

        Delegates to the operation's ``state_forwards(state)`` hook. This is the
        state half of the state/database separation: it updates the in-memory
        schema model without touching a database, which is what lets the planner
        know the shape of the schema partway through a migration.

        Args:
            operation: Any object implementing ``state_forwards(ProjectState)``.

        Raises:
            MigrationFault: If *operation* does not implement the hook.
        """
        forwards = getattr(operation, "state_forwards", None)
        if forwards is None:
            raise MigrationFault(
                migration=type(operation).__name__,
                reason=(
                    f"Operation {type(operation).__name__} does not implement "
                    f"state_forwards(state). Every operation must declare how it "
                    f"changes project state, even if the change is a no-op."
                ),
            )
        forwards(self)

    # ── Serialization ───────────────────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        """Serialize the whole project state to a deterministic, JSON-safe dict.

        Returns:
            A dict with ``version`` and ``tables`` (a list ordered by model
            name). A list rather than a mapping keeps ordering explicit in the
            file itself rather than relying on dict-ordering guarantees.
        """
        return {
            "version": self.version,
            "tables": [self.tables[name].to_dict() for name in sorted(self.tables)],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProjectState:
        """Rebuild a :class:`ProjectState` from :meth:`to_dict` output.

        Args:
            data: Serialized project state.

        Returns:
            The reconstructed state.

        Raises:
            MigrationFault: If the state version is newer than this release
                understands. Refusing is safer than misreading a schema and
                generating a destructive migration from the misreading.
        """
        version = int(data.get("version", STATE_VERSION))
        if version > STATE_VERSION:
            raise MigrationFault(
                migration="schema-state",
                reason=(
                    f"Schema state version {version} is newer than this Aquilia "
                    f"release supports (max {STATE_VERSION}). Upgrade Aquilia before "
                    f"running migrations against this project."
                ),
            )
        tables = {}
        for table_data in data.get("tables", []):
            table = TableState.from_dict(table_data)
            tables[table.model] = table
        return cls(tables=tables, version=version)

    def checksum(self) -> str:
        """Return a stable 16-hex-character digest of this state.

        Because serialization is deterministic, the digest changes if and only
        if the schema changes. Hashing
        ``f"{revision}:{slug}:{len(operations)}"`` and was therefore blind to
        any change that preserved the operation count.

        Returns:
            The truncated SHA-256 digest.
        """
        raw = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(raw.encode()).hexdigest()[:16]


# ── Internal helpers ────────────────────────────────────────────────────────


def _ordered(mapping: dict[str, Any]) -> dict[str, Any]:
    """Return *mapping* with keys in sorted order, for deterministic output."""
    return {k: mapping[k] for k in sorted(mapping)}


_FIELD_CLASS_CACHE: dict[str, type] = {}


def _lookup_field_class(name: str) -> type:
    """Resolve a field class by name from the known field modules.

    Args:
        name: Concrete field class name (e.g. ``"CharField"``).

    Returns:
        The field class.

    Raises:
        MigrationFault: If no module exposes a class by that name.
    """
    cached = _FIELD_CLASS_CACHE.get(name)
    if cached is not None:
        return cached

    from .. import fields_module

    candidate = getattr(fields_module, name, None)
    if candidate is None:
        try:
            from .. import fields as fields_pkg

            candidate = getattr(fields_pkg, name, None)
        except Exception:  # pragma: no cover -- package always importable
            candidate = None

    if candidate is None or not isinstance(candidate, type):
        raise MigrationFault(
            migration="schema-state",
            reason=(
                f"Unknown field class {name!r}. It must be importable from "
                f"aquilia.models.fields_module or aquilia.models.fields. If this is a "
                f"custom field that was renamed or removed, restore it or edit the "
                f"migration to reference the new name."
            ),
        )
    _FIELD_CLASS_CACHE[name] = candidate
    return candidate


def _drop_unsupported(field_cls: type, kwargs: dict[str, Any]) -> dict[str, Any]:
    """Filter *kwargs* down to those the field's ``__init__`` actually accepts.

    Field signatures evolve; a snapshot written by an older release may carry a
    keyword a newer field no longer takes. Dropping it is preferable to raising,
    since the keyword is by definition not schema-significant to the current
    field. Fields accepting ``**kwargs`` receive everything unchanged.

    Args:
        field_cls: The field class about to be instantiated.
        kwargs: Candidate constructor arguments.

    Returns:
        The accepted subset.
    """
    import inspect

    try:
        signature = inspect.signature(field_cls.__init__)
    except (TypeError, ValueError):  # pragma: no cover -- builtins only
        return kwargs
    params = signature.parameters
    if any(p.kind is inspect.Parameter.VAR_KEYWORD for p in params.values()):
        return kwargs
    return {k: v for k, v in kwargs.items() if k in params}


def _m2m_state(attr_name: str, fld: Any, model_cls: type[Model], resolve_table: Any) -> ManyToManyState:
    """Build a :class:`ManyToManyState` from a bound ``ManyToManyField``."""
    source_table = model_cls._meta.table_name
    if resolve_table is not None:
        target_model, target_table, target_pk = resolve_table(fld.to)
    else:
        target_model = fld.to if isinstance(fld.to, str) else getattr(fld.to, "__name__", str(fld.to))
        target_table = target_model.lower()
        target_pk = "id"

    source_pk_attr = getattr(model_cls, "_pk_attr", "id")
    source_pk_field = model_cls._fields.get(source_pk_attr)
    source_pk = getattr(source_pk_field, "column_name", None) or "id" if source_pk_field else "id"

    src_col, tgt_col = fld.junction_columns(model_cls)
    through = fld.through
    if through is not None and not isinstance(through, str):
        through = getattr(through, "__name__", str(through))

    return ManyToManyState(
        name=attr_name,
        table=fld.db_table or f"{source_table}_{attr_name}",
        source_column=src_col,
        target_column=tgt_col,
        source_table=source_table,
        target_table=target_table,
        source_target_column=source_pk,
        target_target_column=target_pk,
        through=through,
    )


def _collect_indexes(model_cls: type[Model], table: str, columns: dict[str, ColumnState]) -> list[IndexState]:
    """Collect index states from ``Meta.indexes`` and ``db_index=True`` fields.

    Handles every index class Aquilia ships -- plain ``Index``, the
    PostgreSQL-specific ``GinIndex``/``GistIndex``/``BrinIndex``/``HashIndex``,
    and ``FunctionalIndex`` -- preserving the access method, partial condition,
    and operator classes.

    Args:
        model_cls: The model being snapshotted.
        table: Its database table name.
        columns: Already-built column states, used to map attribute names to
            database column names.

    Returns:
        Index states; duplicates by name are dropped, first occurrence winning.
    """
    attr_to_column = {name: col.column for name, col in columns.items()}
    result: list[IndexState] = []
    seen: set[str] = set()

    def add(state: IndexState) -> None:
        if state.name not in seen:
            seen.add(state.name)
            result.append(state)

    for idx in getattr(model_cls._meta, "indexes", []) or []:
        method: IndexMethod = "BTREE"
        condition = getattr(idx, "condition", None)
        opclasses = tuple(getattr(idx, "opclasses", ()) or ())
        raw_method = getattr(idx, "_index_type", "") or ""
        if raw_method.upper() in ("GIN", "GIST", "BRIN", "HASH", "SPGIST"):
            method = raw_method.upper()  # type: ignore[assignment]

        expression = getattr(idx, "expression", None)
        if expression:
            # FunctionalIndex: the key is an expression, not a column list.
            explicit_method = getattr(idx, "index_type", None)
            if explicit_method and explicit_method.upper() in ("GIN", "GIST", "BRIN", "HASH", "SPGIST"):
                method = explicit_method.upper()  # type: ignore[assignment]
            name = getattr(idx, "name", None) or auto_index_name(table, (expression,))
            add(
                IndexState(
                    name=name,
                    expressions=(expression,),
                    unique=bool(getattr(idx, "unique", False)),
                    method=method,
                    condition=condition,
                )
            )
            continue

        raw_fields = getattr(idx, "fields", ()) or ()
        if isinstance(raw_fields, str):
            raw_fields = [raw_fields]

        cols: list[str] = []
        exprs: list[str] = []
        for entry in raw_fields:
            if isinstance(entry, str):
                cols.append(attr_to_column.get(entry, entry))
            else:
                exprs.append(_compile_expression(entry, model_cls))

        name = getattr(idx, "name", None) or auto_index_name(table, tuple(cols) + tuple(exprs))
        add(
            IndexState(
                name=name,
                columns=tuple(cols),
                expressions=tuple(exprs),
                unique=bool(getattr(idx, "unique", False)),
                method=method,
                condition=condition,
                opclasses=opclasses,
            )
        )

    # Field-level db_index=True. A unique field already has a unique index from
    # its UNIQUE constraint, and a primary key is already indexed, so neither
    # needs a second one.
    for col in columns.values():
        if col.db_index and not col.primary_key and not col.unique:
            add(IndexState(name=auto_index_name(table, (col.column,)), columns=(col.column,)))

    return result


def _collect_constraints(
    model_cls: type[Model],
    table: str,
    columns: dict[str, ColumnState],
) -> list[ConstraintState]:
    """Collect constraint states from ``Meta.constraints`` and ``Meta.unique_together``.

    ``unique_together`` -- which, if not captured, silently
    vanished from any migration-built database -- is translated into named
    :class:`UniqueConstraintState` entries here.

    Args:
        model_cls: The model being snapshotted.
        table: Its database table name.
        columns: Already-built column states, for attribute-to-column mapping.

    Returns:
        Constraint states; duplicates by name are dropped.

    Raises:
        MigrationFault: If a constraint object is of an unrecognized type. Silently
            silently skipped these (``else: continue``), dropping the integrity
            guarantee without telling anyone.
    """
    attr_to_column = {name: col.column for name, col in columns.items()}
    result: list[ConstraintState] = []
    seen: set[str] = set()

    def add(state: ConstraintState) -> None:
        if state.name not in seen:
            seen.add(state.name)
            result.append(state)

    def map_field(entry: Any) -> tuple[str | None, str | None]:
        """Return ``(column, expression)`` -- exactly one is non-None."""
        if isinstance(entry, str) and "(" not in entry and '"' not in entry:
            return attr_to_column.get(entry, entry), None
        if isinstance(entry, str):
            return None, entry
        return None, _compile_expression(entry, model_cls)

    for constraint in getattr(model_cls._meta, "constraints", []) or []:
        cls_name = type(constraint).__name__
        name = getattr(constraint, "name", None)

        if cls_name == "CheckConstraint":
            add(
                CheckConstraintState(
                    name=name or f"ck_{table}_{len(result)}",
                    check=getattr(constraint, "check", ""),
                )
            )
        elif cls_name == "UniqueConstraint":
            cols: list[str] = []
            exprs: list[str] = []
            for entry in getattr(constraint, "fields", ()) or ():
                col, expr = map_field(entry)
                if col is not None:
                    cols.append(col)
                elif expr is not None:
                    exprs.append(expr)
            add(
                UniqueConstraintState(
                    name=name or auto_index_name(table, tuple(cols) + tuple(exprs), unique=True),
                    columns=tuple(cols),
                    expressions=tuple(exprs),
                    condition=getattr(constraint, "condition", None),
                    deferrable=bool(getattr(constraint, "deferrable", None)),
                )
            )
        elif cls_name == "ExclusionConstraint":
            add(
                ExclusionConstraintState(
                    name=name or f"ex_{table}",
                    expressions=tuple(
                        (str(col), str(op)) for col, op in (getattr(constraint, "expressions", ()) or ())
                    ),
                    method=(getattr(constraint, "index_type", "GIST") or "GIST").upper(),  # type: ignore[arg-type]
                    condition=getattr(constraint, "condition", None),
                    deferrable=bool(getattr(constraint, "deferrable", None)),
                )
            )
        elif hasattr(constraint, "deconstruct"):
            data = constraint.deconstruct()
            kind = data.get("type", cls_name)
            raise MigrationFault(
                migration="schema-state",
                reason=(
                    f"Constraint type {kind!r} on model {model_cls.__name__} is not "
                    f"understood by the migration system. Supported: CheckConstraint, "
                    f"UniqueConstraint, ExclusionConstraint."
                ),
            )
        else:
            raise MigrationFault(
                migration="schema-state",
                reason=(
                    f"Constraint object {constraint!r} on model {model_cls.__name__} is "
                    f"not a recognized constraint type and provides no deconstruct()."
                ),
            )

    # Meta.unique_together, which has no column-level equivalent.
    for group in getattr(model_cls._meta, "unique_together", []) or []:
        entries = (group,) if isinstance(group, str) else tuple(group)
        cols = tuple(attr_to_column.get(e, e) for e in entries)
        if cols:
            add(UniqueConstraintState(name=auto_index_name(table, cols, unique=True), columns=cols))

    # Composite primary key declared via Meta.
    composite = getattr(model_cls._meta, "primary_key", None)
    if composite:
        entries = (composite,) if isinstance(composite, str) else tuple(composite)
        cols = tuple(attr_to_column.get(e, e) for e in entries)
        if len(cols) > 1:
            add(PrimaryKeyConstraintState(name=f"pk_{table}", columns=cols))

    return result


def _compile_expression(expr: Any, model_cls: type[Model]) -> str:
    """Render an Aquilia expression object as inline SQL for use in DDL.

    Delegates to the existing schema-expression compiler so that ``F``,
    ``Func``, ``Value`` and friends render identically wherever they appear.

    Args:
        expr: An expression object or a raw SQL string.
        model_cls: The owning model, used to resolve field references.

    Returns:
        The compiled SQL fragment.
    """
    from ..expression import compile_schema_expression

    return compile_schema_expression(expr, model_cls)


# ── Database introspection ──────────────────────────────────────────────────

_TYPE_TO_FIELD: tuple[tuple[str, str], ...] = (
    # Ordered: the first substring that matches wins, so the more specific
    # spelling of an overlapping pair must come first ("BIGINT" before "INT",
    # "TIMESTAMP" before "TIME").
    ("BIGINT", "BigIntegerField"),
    ("SMALLINT", "SmallIntegerField"),
    ("INT", "IntegerField"),
    ("BOOL", "BooleanField"),
    ("TIMESTAMP", "DateTimeField"),
    ("DATETIME", "DateTimeField"),
    ("DATE", "DateField"),
    ("TIME", "TimeField"),
    ("DECIMAL", "DecimalField"),
    ("NUMERIC", "DecimalField"),
    ("DOUBLE", "FloatField"),
    ("FLOAT", "FloatField"),
    ("REAL", "FloatField"),
    ("JSONB", "JSONField"),
    ("JSON", "JSONField"),
    ("UUID", "UUIDField"),
    ("BLOB", "BinaryField"),
    ("BYTEA", "BinaryField"),
    ("CLOB", "TextField"),
    ("TEXT", "TextField"),
)


_AUTO_FOR_INTEGER: dict[str, str] = {
    "IntegerField": "AutoField",
    "BigIntegerField": "BigAutoField",
    "SmallIntegerField": "SmallAutoField",
}
"""Auto-field class for each integer width, used when a column is a primary key."""


def _model_name_from_table(db_table: str) -> str:
    """Derive a plausible model name from a table name.

    Used only for a table with no matching model class -- something created
    outside the ORM. Reverses the default ``Post`` -> ``posts`` convention:
    strips a trailing ``s`` and CamelCases the remaining words.

    Args:
        db_table: The database table name.

    Returns:
        A model-style name, e.g. ``"blog_posts"`` -> ``"BlogPost"``.
    """
    stem = db_table[:-1] if db_table.endswith("s") and not db_table.endswith("ss") else db_table
    return "".join(part.capitalize() for part in stem.split("_") if part) or db_table


def _field_class_for(data_type: str) -> str:
    """Infer an Aquilia field class from a database column type.

    Args:
        data_type: The type as the backend reports it, e.g. ``"VARCHAR(200)"``.

    Returns:
        The field class name. ``CharField`` when nothing more specific matches,
        since every backend can render an unknown type as text.
    """
    upper = data_type.upper()
    for needle, field_class in _TYPE_TO_FIELD:
        if needle in upper:
            return field_class
    return "CharField"


async def _introspect_table(
    db: Any,
    db_table: str,
    model: str,
    table_to_model: dict[str, str],
    declared_columns: dict[str, ColumnState],
) -> TableState:
    """Build a :class:`TableState` from a live table's metadata.

    Args:
        db: A connected database.
        db_table: The table to introspect.
        model: The model name to record for it.
        table_to_model: Table-to-model mapping, for naming foreign key targets.
        declared_columns: Columns from the matching model, consulted only for
            facts the database provably cannot report -- currently the width of
            an auto field, which SQLite renders identically for every width.
            Empty when no model matches the table.

    Returns:
        The introspected table state.
    """
    columns_raw = await db.get_columns(db_table)
    indexes_raw = await _safe_introspect(db, "get_indexes", db_table)
    foreign_keys = await _safe_introspect(db, "get_foreign_keys", db_table)

    indexes: list[IndexState] = []
    unique_columns: set[str] = set()
    for entry in indexes_raw:
        cols = tuple(entry.get("columns", ()))
        if not cols:
            continue
        unique = bool(entry.get("unique"))
        if unique and len(cols) == 1:
            unique_columns.add(cols[0])
        indexes.append(IndexState(name=entry["name"], columns=cols, unique=unique))

    references_by_column = {}
    for entry in foreign_keys:
        target_table = entry["to_table"]
        references_by_column[entry["from_column"]] = Reference(
            model=table_to_model.get(target_table) or _model_name_from_table(target_table),
            table=target_table,
            column=entry.get("to_column") or "id",
            on_delete=_normalize_action(entry.get("on_delete")),
            on_update=_normalize_action(entry.get("on_update")),
        )

    columns: dict[str, ColumnState] = {}
    for col in columns_raw:
        primary_key = bool(getattr(col, "primary_key", False))
        field_class = _field_class_for(col.data_type)
        auto_increment = primary_key and field_class in _AUTO_FOR_INTEGER
        if auto_increment:
            # No backend reports an "is auto-increment" flag through ColumnInfo,
            # and an integer primary key is an auto field in Aquilia's model
            # vocabulary. Reporting IntegerField here would raise a spurious
            # AlterField against the primary key of every table.
            #
            # Which width it is often cannot be recovered: SQLite renders every
            # auto field as plain INTEGER, so the declared class is preferred
            # over the inferred one when a model is available.
            field_class = _AUTO_FOR_INTEGER[field_class]
            declared = declared_columns.get(col.name)
            if declared is not None and declared.auto_increment:
                field_class = declared.field_class
        columns[col.name] = ColumnState(
            name=col.name,
            column=col.name,
            field_class=field_class,
            field_kwargs=_introspected_kwargs(col),
            primary_key=primary_key,
            unique=col.name in unique_columns and not primary_key,
            null=bool(getattr(col, "nullable", False)) and not primary_key,
            default=getattr(col, "default", None) if getattr(col, "default", None) is not None else NOT_PROVIDED,
            reference=references_by_column.get(col.name),
            auto_increment=auto_increment,
        )

    return TableState(
        model=model,
        db_table=db_table,
        columns=columns,
        indexes=tuple(sorted(indexes, key=lambda index: index.name)),
    )


def _introspected_kwargs(col: Any) -> dict[str, Any]:
    """Recover the field kwargs a column type still carries.

    Only ``max_length`` survives introspection -- it is encoded in the type as
    ``VARCHAR(200)``. A precision pair on a decimal is a different kwarg pair and
    is deliberately not guessed from the same parentheses.

    Args:
        col: A column descriptor from the backend.

    Returns:
        The recovered kwargs, empty when nothing is recoverable.
    """
    upper = str(col.data_type).upper()
    if "DECIMAL" in upper or "NUMERIC" in upper:
        match = re.search(r"\((\d+)\s*,\s*(\d+)\)", upper)
        if match:
            return {"max_digits": int(match.group(1)), "decimal_places": int(match.group(2))}
        return {}

    match = re.search(r"\((\d+)\)", upper)
    if match:
        return {"max_length": int(match.group(1))}
    if getattr(col, "max_length", None):
        return {"max_length": int(col.max_length)}
    return {}


def _normalize_action(action: Any) -> OnDelete:
    """Normalize a backend-reported referential action.

    Unlike :func:`normalize_referential_action`, an unrecognized value degrades
    to ``"NO ACTION"`` rather than raising: what a backend reports is a fact
    about an existing schema, not a mistake in Aquilia model code, and a diff
    should still be produced for it.

    Args:
        action: The action as reported, e.g. ``"NO ACTION"`` or ``None``.

    Returns:
        The matching action, or ``"NO ACTION"`` -- the SQL default, and so the
        safe assumption when the backend says nothing.
    """
    if not action:
        return "NO ACTION"
    return _REFERENTIAL_ACTIONS.get(str(action).strip().upper(), "NO ACTION")


async def _safe_introspect(db: Any, method: str, db_table: str) -> list[dict[str, Any]]:
    """Call an optional adapter introspection method, tolerating absence.

    Index and foreign-key introspection is adapter-specific and not every
    backend implements it. A backend that cannot report indexes should yield a
    coarser state, not fail the whole diff.

    Args:
        db: A connected database.
        method: The adapter method name, e.g. ``"get_indexes"``.
        db_table: The table to introspect.

    Returns:
        The reported rows, or an empty list when unavailable.
    """
    adapter = getattr(db, "_adapter", None)
    fn = getattr(adapter, method, None)
    if fn is None:
        return []
    try:
        return list(await fn(db_table))
    except Exception as exc:  # noqa: BLE001 - adapter-specific; degrade, don't fail
        logger.debug("%s(%s) unavailable on %s: %s", method, db_table, type(adapter).__name__, exc)
        return []
