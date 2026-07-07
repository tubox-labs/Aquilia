"""
Aquilia Model Enums -- standard enum helpers for model fields.

Provides TextChoices and IntegerChoices for model fields.

Usage:
    from aquilia.models.enums import TextChoices, IntegerChoices

    class Status(TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        ARCHIVED = "archived", "Archived"

    class Priority(IntegerChoices):
        LOW = 1, "Low"
        MEDIUM = 2, "Medium"
        HIGH = 3, "High"

    class Article(Model):
        status = CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
        priority = IntegerField(choices=Priority.choices, default=Priority.LOW)
"""

from __future__ import annotations

from enum import Enum
from typing import Any

__all__ = [
    "TextChoices",
    "IntegerChoices",
    "Choices",
]


class _ChoicesMeta(type(Enum)):
    """
    Metaclass that adds ``.choices`` / ``.values`` / ``.names_list`` / ``.labels``
    class-level properties to ``Enum`` classes.

    ``TextChoices`` and ``IntegerChoices`` use this metaclass (instead of the
    plain ``EnumMeta``) so callers can introspect a whole choices enum at the
    *class* level (``Status.choices``) without instantiating or iterating it
    manually. Each property below iterates ``cls`` (i.e. the enum's members,
    in declaration order) and pulls out one facet of each member.
    """

    @property
    def choices(cls) -> list[tuple[Any, str]]:
        """
        ``[(value, label), ...]`` for every member, in declaration order.

        This is the shape expected by a field's ``choices=`` parameter, e.g.
        ``status = CharField(choices=Status.choices)``.
        """
        return [(m.value, m.label) for m in cls]

    @property
    def values(cls) -> list[Any]:
        """Raw ``.value`` of every member, in declaration order."""
        return [m.value for m in cls]

    @property
    def names_list(cls) -> list[str]:
        """Declared ``.name`` of every member (e.g. ``"DRAFT"``), in declaration order."""
        return [m.name for m in cls]

    @property
    def labels(cls) -> list[str]:
        """Human-readable ``.label`` of every member, in declaration order."""
        return [m.label for m in cls]


class TextChoices(str, Enum, metaclass=_ChoicesMeta):
    """
    String-valued choices enum.

    Combines ``str`` and ``Enum`` so members compare equal to (and behave
    like) their underlying string value -- ``Status.DRAFT == "draft"`` is
    ``True``, and a member can be passed anywhere a plain string is expected
    (dict keys, f-strings, a VARCHAR column) without an explicit ``.value``
    access.

    Each member carries both a ``value`` (what gets stored/compared) and a
    ``label`` (a human-readable display string for admin UIs, forms, etc.).
    Members may be defined as:
        NAME = "value", "Human Label"   → explicit label
        NAME = "value"                  → auto-generated label from name
            (underscores replaced with spaces and title-cased, e.g.
            ``IN_PROGRESS`` -> ``"In Progress"``)

    Use the ``.choices`` class property (added by ``_ChoicesMeta``) to get a
    ``[(value, label), ...]`` list for a field's ``choices=`` parameter.

    Example:
        class Status(TextChoices):
            DRAFT = "draft", "Draft"
            IN_PROGRESS = "in_progress"          # label auto -> "In Progress"
            PUBLISHED = "published", "Published"

        Status.DRAFT.value    # "draft"
        Status.DRAFT.label    # "Draft"
        Status.choices        # [("draft", "Draft"), ("in_progress", "In Progress"), ...]
    """

    def __new__(cls, value: str, label: str | None = None):
        """
        Construct the underlying ``str`` instance for this member.

        ``Enum`` calls ``__new__`` before ``__init__``, and member name
        resolution isn't guaranteed complete yet, so the label is stashed
        as-is (possibly ``None``) and finalized in ``__init__``.

        Args:
            value: The stored/compared string value for this member.
            label: Optional explicit human-readable label; if ``None``,
                one is derived from the member name in ``__init__``.
        """
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj._label = label  # may be None; fixed in __init__
        return obj

    def __init__(self, value: str, label: str | None = None):
        """
        Finalize this member's label.

        Keeps the explicit ``label`` passed to ``__new__`` if one was
        given; otherwise derives one from ``self.name`` (set by the
        ``Enum`` machinery before ``__init__`` runs) by replacing
        underscores with spaces and title-casing it.

        Args:
            value: Unused here beyond the signature -- already applied
                to the instance in ``__new__``.
            label: Optional explicit human-readable label.
        """
        # At this point self.name is set by Enum machinery
        if label is not None:
            self._label = label
        else:
            self._label = self.name.replace("_", " ").title()

    @property
    def label(self) -> str:
        """Human-readable label for this member (explicit or auto-generated)."""
        return self._label

    def __str__(self) -> str:
        """Return the plain string value, e.g. ``str(Status.DRAFT) == "draft"``."""
        return str(self.value)


class IntegerChoices(int, Enum, metaclass=_ChoicesMeta):
    """
    Integer-valued choices enum.

    Combines ``int`` and ``Enum`` so members compare equal to (and behave
    like) their underlying integer value -- ``Priority.LOW == 1`` is
    ``True``, and a member can be used anywhere a plain int is expected
    (arithmetic, sorting, an INTEGER column) without an explicit ``.value``
    access.

    Each member carries both a ``value`` (what gets stored/compared) and a
    ``label`` (a human-readable display string). Members may be defined as:
        NAME = 1, "Human Label"   → explicit label
        NAME = 1                  → auto-generated label from name
            (underscores replaced with spaces and title-cased)

    Use the ``.choices`` class property (added by ``_ChoicesMeta``) to get a
    ``[(value, label), ...]`` list for a field's ``choices=`` parameter.

    Example:
        class Priority(IntegerChoices):
            LOW = 1, "Low"
            MEDIUM = 2                 # label auto -> "Medium"
            HIGH = 3, "High"

        Priority.LOW.value    # 1
        Priority.LOW.label    # "Low"
        Priority.choices      # [(1, "Low"), (2, "Medium"), (3, "High")]
    """

    def __new__(cls, value: int, label: str | None = None):
        """
        Construct the underlying ``int`` instance for this member.

        ``Enum`` calls ``__new__`` before ``__init__``, and member name
        resolution isn't guaranteed complete yet, so the label is stashed
        as-is (possibly ``None``) and finalized in ``__init__``.

        Args:
            value: The stored/compared integer value for this member.
            label: Optional explicit human-readable label; if ``None``,
                one is derived from the member name in ``__init__``.
        """
        obj = int.__new__(cls, value)
        obj._value_ = value
        obj._label = label  # may be None; fixed in __init__
        return obj

    def __init__(self, value: int, label: str | None = None):
        """
        Finalize this member's label.

        Keeps the explicit ``label`` passed to ``__new__`` if one was
        given; otherwise derives one from ``self.name`` (set by the
        ``Enum`` machinery before ``__init__`` runs) by replacing
        underscores with spaces and title-casing it.

        Args:
            value: Unused here beyond the signature -- already applied
                to the instance in ``__new__``.
            label: Optional explicit human-readable label.
        """
        if label is not None:
            self._label = label
        else:
            self._label = self.name.replace("_", " ").title()

    @property
    def label(self) -> str:
        """Human-readable label for this member (explicit or auto-generated)."""
        return self._label

    def __str__(self) -> str:
        """Return the plain string form of the value, e.g. ``str(Priority.LOW) == "1"``."""
        return str(self.value)


# Backward-compatible alias: `Choices` was the original name for `TextChoices`.
Choices = TextChoices
