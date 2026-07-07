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

from ..fields_module import Field, FieldValidationError

__all__ = ["EnumField"]

#: Bound to Enum -- inferred from EnumField's own `enum_class` constructor
#: argument (`EnumField(enum_class=Color)` binds E=Color), the same
#: convention ForeignKey uses for TModel via its `to` argument
#: (aquilia/models/fields_module.py). Unlike ForeignKey's `to`, `enum_class`
#: never accepts a string forward-reference -- enums don't have the
#: circular-import problem models do -- so this generic binding has none of
#: FK's string-ref caveat: a plain, unannotated `color = EnumField(enum_class=Color)`
#: always resolves `instance.color` to `Color`, not `Any`.
E = TypeVar("E", bound=Enum)


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
        enum_class: type[E],
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
        self.enum_class = enum_class
        self.max_length = max_length
        self.store_name = store_name

        # Auto-generate choices from enum
        choices = [(m.value, m.name) for m in enum_class]
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

    def to_db(self, value: Any) -> Any:
        """
        Convert an ``enum_class`` member to its database-storable form.

        Returns ``value.name`` if ``store_name=True``, else
        ``value.value``. Non-enum values (already the raw stored form,
        or ``None``) pass through unchanged.
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
        """
        Serialize this field's definition for migrations.

        Extends the base ``deconstruct()`` output with a dotted-path
        reference to ``enum_class`` (``"module.QualName"``, so migrations
        can re-import it), plus ``max_length`` and ``store_name``.
        """
        d = super().deconstruct()
        d["enum_class"] = f"{self.enum_class.__module__}.{self.enum_class.__qualname__}"
        d["max_length"] = self.max_length
        d["store_name"] = self.store_name
        return d
