"""
Aquilia EnumField -- store Python enums with database mapping.

Usage:
    from enum import Enum
    from aquilia.models.fields import EnumField

    class Color(Enum):
        RED = "red"
        GREEN = "green"
        BLUE = "blue"

    class Item(Model):
        color = EnumField(enum_class=Color, default=Color.RED)
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Generic, TypeVar

from aquilia.models.fields_module import Field, FieldValidationError

__all__ = ["EnumField"]

#: Bound to Enum -- inferred from EnumField's own `enum_class` constructor
#: argument (`EnumField(enum_class=Color)` binds E=Color), the same
#: convention ForeignKey uses for TModel via its `to` argument
#: (aquilia/models/fields_module.py). Passing the class itself -- the form model
#: code should use -- resolves `instance.color` to `Color` rather than `Any`. A
#: dotted string is also accepted, for reconstructing a field from a generated
#: migration file, but carries no type information.
E = TypeVar("E", bound=Enum)


def _resolve_enum_class(enum_class: type[Enum] | str) -> type[Enum]:
    """Return the Enum class, importing it when given as a dotted path.

    :meth:`EnumField.deconstruct` writes ``enum_class`` as
    ``"module.QualName"``, since an Enum class has no literal source form. This
    is the inverse, so a generated migration reconstructs the same field.

    Args:
        enum_class: An ``Enum`` subclass, or a ``"module.QualName"`` path to one.

    Returns:
        The resolved ``Enum`` subclass.

    Raises:
        FieldValidationError: If the path has no module component, cannot be
            imported, names a missing attribute, or resolves to something that
            is not an ``Enum`` subclass. Raising here surfaces the problem when
            the field is declared, rather than as an ``AttributeError`` from the
            middle of choices generation.
    """
    if not isinstance(enum_class, str):
        if isinstance(enum_class, type) and issubclass(enum_class, Enum):
            return enum_class
        raise FieldValidationError("enum_class", f"expected an Enum subclass, got {enum_class!r}")

    module_path, _, qualname = enum_class.rpartition(".")
    if not module_path:
        raise FieldValidationError(
            "enum_class",
            f"{enum_class!r} is not importable: expected a 'module.QualName' path, which is what deconstruct() writes",
        )

    import importlib

    try:
        resolved: Any = importlib.import_module(module_path)
        for part in qualname.split("."):
            resolved = getattr(resolved, part)
    except (ImportError, AttributeError) as exc:
        raise FieldValidationError(
            "enum_class",
            f"cannot import {enum_class!r}: {exc}. The enum must remain importable "
            f"for any migration referencing it to load",
        ) from exc

    if not (isinstance(resolved, type) and issubclass(resolved, Enum)):
        raise FieldValidationError("enum_class", f"{enum_class!r} resolved to {resolved!r}, not an Enum")
    return resolved


class EnumField(Field[E], Generic[E]):
    """
    Stores a Python Enum value in the database.

    By default, stores the enum *value* (not name) as a VARCHAR.
    Supports both string-valued and integer-valued enums.

    Args:
        enum_class: The Enum class to use
        max_length: Maximum length for string storage (default 50)
        store_name: If True, store the enum *name* instead of value

    Usage:
        class Color(Enum):
            RED = "red"
            GREEN = "green"

        class Item(Model):
            color = EnumField(enum_class=Color, default=Color.RED)

        item = await Item.objects.first()
        reveal_type(item.color)  # Color -- not Any, not the bare EnumField object
    """

    _field_type = "ENUM"

    def __init__(
        self,
        *,
        enum_class: type[E] | str,
        max_length: int = 50,
        store_name: bool = False,
        **kwargs,
    ):
        """
        Args:
            enum_class: The ``Enum`` subclass this field stores members of.
                Also binds the field's generic type parameter ``E`` (see
                the ``E`` ``TypeVar`` above), so ``instance.<field>``
                type-checks as ``enum_class``, not ``Any``.

                A ``"module.QualName"`` string is also accepted and imported
                on the spot. This is the form :meth:`deconstruct` writes, so
                that a generated migration file naming
                ``EnumField(enum_class="myapp.models.Status")`` reconstructs
                the same field. Prefer passing the class itself in model code,
                where it type-checks.
            max_length: Column width used for string storage when the
                enum's values are not all integers (see ``sql_type``).
                Ignored when ``sql_type()`` resolves to ``INTEGER``.
            store_name: If True, persist the member's ``.name`` (e.g.
                ``"RED"``) instead of its ``.value`` (e.g. ``"red"``).
                Useful when the enum's values aren't stable/serializable
                on their own, or when the DB column should read as the
                symbolic name.
            **kwargs: Passed through to ``Field.__init__`` (``null``,
                ``default``, ``unique``, etc.). If ``choices`` isn't
                supplied, it's auto-derived from ``enum_class`` as
                ``[(member.value, member.name), ...]``.
        """
        self.enum_class = _resolve_enum_class(enum_class)
        self.max_length = max_length
        self.store_name = store_name

        # Auto-generate choices from enum
        choices = [(m.value, m.name) for m in self.enum_class]
        kwargs.setdefault("choices", choices)

        super().__init__(**kwargs)

    def validate(self, value: Any) -> Any:
        """
        Coerce and validate ``value`` into an ``enum_class`` member.

        Accepts, in order:
            1. An ``enum_class`` member directly -- returned as-is.
            2. A raw value equal to some member's ``.value`` (e.g.
               ``"red"`` for ``Color.RED``) -- resolved via
               ``enum_class(value)``.
            3. A member name string (e.g. ``"RED"``) -- looked up via
               ``enum_class.__members__``.

        Args:
            value: The value to validate, in any of the forms above (or
                ``None``).

        Returns:
            The resolved ``enum_class`` member, or ``None`` if ``value``
            is ``None`` and the field allows null.

        Raises:
            FieldValidationError: If ``value`` is ``None`` and the field
                isn't nullable, or if ``value`` doesn't match any member
                by value or by name.
        """
        if value is None:
            if self.null:
                return None
            raise FieldValidationError(self.name, "Cannot be null")

        # Accept enum member directly
        if isinstance(value, self.enum_class):
            return value

        # Accept raw value
        try:
            return self.enum_class(value)
        except ValueError:
            pass

        # Accept name
        if isinstance(value, str) and value in self.enum_class.__members__:
            return self.enum_class[value]

        raise FieldValidationError(
            self.name,
            f"Invalid value '{value}' for {self.enum_class.__name__}. Valid: {[m.value for m in self.enum_class]}",
            value,
        )

    def to_python(self, value: Any) -> Any:
        """
        Convert a raw/database value to an ``enum_class`` member.

        Tries, in order: pass-through if already a member, lookup by
        value (``enum_class(value)``), then lookup by name (via
        ``enum_class.__members__``).

        Unlike ``validate()``, this never raises: if ``value`` doesn't
        match any member by value or name (e.g. a stale/legacy value
        left over from a since-changed enum), it is returned unchanged
        rather than coerced or rejected.
        """
        if value is None:
            return None
        if isinstance(value, self.enum_class):
            return value
        # Try by value first
        try:
            return self.enum_class(value)
        except (ValueError, KeyError):
            pass
        # Try by name
        if isinstance(value, str) and value in self.enum_class.__members__:
            return self.enum_class[value]
        return value

    def to_db(self, value: Any, dialect: str = "sqlite") -> Any:
        """
        Convert an ``enum_class`` member to its database-storable form.

        Purpose:
            Serializes Python Enum instances or raw storable enum values into
            database column format (either string member name or underlying value),
            compatible with database dialect transformations.

        Lifecycle:
            Invoked during model persistence operations (``Model.save()``,
            ``Model.create()``, bulk operations, and query filtering) by the ORM
            model layer before building SQL parameter tuples.

        Execution Order:
            1. Handle ``None`` (returns ``None`` immediately).
            2. If value is an instance of ``enum_class``: return ``value.name`` if
               ``store_name=True``, otherwise return ``value.value``.
            3. Return non-enum value unchanged (assumed to be raw DB storable form).

        Parameters:
            value (Any):
                The Python value to transform. May be an Enum instance, scalar value,
                or ``None``.
            dialect (str, optional):
                The database engine dialect (e.g., ``"sqlite"``, ``"postgresql"``,
                ``"mysql"``). Defaults to ``"sqlite"``.

        Returns:
            Any:
                The database-ready representation (e.g., str name, int/str value, or None).

        Exceptions:
            None directly raised. Invalid conversions are handled gracefully by returning
            the raw value.

        Notes:
            Maintains signature compatibility with base ``Field.to_db(self, value, dialect="sqlite")``.

        Internal Behaviour:
            Transparently unwraps Enum instances according to ``self.store_name``.

        Edge Cases:
            - Unrecognized string/int values pass through unchanged for DB driver coercion.
            - Null values pass through as ``None``.

        Examples:
            >>> field = EnumField(enum_class=UserStatus, store_name=False)
            >>> field.to_db(UserStatus.ACTIVE, dialect="sqlite")
            'active'
            >>> field.to_db(UserStatus.ACTIVE, dialect="postgresql")
            'active'
        """
        if value is None:
            return None
        if isinstance(value, self.enum_class):
            return value.name if self.store_name else value.value
        return value

    def sql_type(self, dialect: str = "sqlite") -> str:
        """
        Return the SQL column type for this field.

        Resolves to ``INTEGER`` if every member's ``.value`` is an
        ``int`` (i.e. an ``IntegerChoices``-style enum); otherwise
        ``VARCHAR(max_length)`` for string-valued enums.
        """
        # Check if all values are integers
        all_int = all(isinstance(m.value, int) for m in self.enum_class)
        if all_int:
            return "INTEGER"
        return f"VARCHAR({self.max_length})"

    def deconstruct(self) -> dict[str, Any]:
        """Serialize this field's definition for migration snapshotting and schema diffing.

        Purpose:
            Serializes the full configuration of this ``EnumField`` instance into a
            JSON-friendly dictionary format required by the migration generator.

        Lifecycle:
            Invoked during model snapshot generation (``create_snapshot()``) or field
            deconstruction.

        Execution Order:
            1. Call ``super().deconstruct()`` to obtain base Field attributes.
            2. Inject ``enum_class`` string reference (module + qualname).
            3. Inject ``max_length`` and ``store_name`` options.
            4. Unwrap Enum default instance into primitive database-storable value.

        Parameters:
            None.

        Returns:
            dict[str, Any]: Deconstructed metadata dictionary containing field definition.

        Exceptions:
            None directly raised.

        Notes:
            Extends base ``deconstruct()`` by unwrapping Enum member defaults via ``to_db()``
            so migration snapshots receive scalar primitives (strings/ints).

        Internal Behaviour:
            Maps ``enum_class`` to dotted import path and calls ``to_db(self.default)``
            if a non-callable default is defined.

        Edge Cases:
            - Unset or None defaults pass through without modification.
            - Enum instance defaults are unwrapped via ``to_db()``.

        Examples:
            >>> field = EnumField(enum_class=UserStatus, default=UserStatus.ACTIVE)
            >>> field.deconstruct()["default"]
            'active'
        """
        d = super().deconstruct()
        d["enum_class"] = f"{self.enum_class.__module__}.{self.enum_class.__qualname__}"
        d["max_length"] = self.max_length
        d["store_name"] = self.store_name
        if self.has_default() and not callable(self.default):
            from enum import Enum

            if isinstance(self.default, Enum):
                d["default"] = self.to_db(self.default)
        return d
