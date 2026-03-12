"""
Typed Session State for Aquilia.

Provides type-safe session state management with validation and auto-binding.

Example:
    >>> class CartState(SessionState):
    ...     items: List[str] = Field(default_factory=list)
    ...     total: float = 0.0

    >>> @stateful
    >>> async def add_to_cart(ctx, cart: CartState):
    ...     cart.items.append(item_id)
    ...     cart.total += price
"""

from dataclasses import MISSING
from typing import Any, TypeVar, get_type_hints

T = TypeVar("T", bound="SessionState")


class Field:
    """Field descriptor for SessionState."""

    def __init__(self, default=MISSING, default_factory=MISSING):
        self.default = default
        self.default_factory = default_factory

    def __set_name__(self, owner, name):
        self.name = name
        self.private_name = f"_{name}"

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        # FIX: Graceful missing key handling
        try:
            return getattr(obj, self.private_name)
        except AttributeError:
            return self._get_default()

    def __set__(self, obj, value):
        setattr(obj, self.private_name, value)

    def _get_default(self):
        if self.default_factory is not MISSING:
            return self.default_factory()
        if self.default is not MISSING:
            return self.default
        return None


class SessionState:
    """
    Base class for typed session state.

    Provides type-safe access to session data with validation.

    Example:
        >>> class UserPreferences(SessionState):
        ...     theme: str = Field(default="light")
        ...     language: str = Field(default="en")
        ...     notifications: bool = Field(default=True)

        >>> prefs = UserPreferences(session_data)
        >>> prefs.theme = "dark"
        >>> prefs.language = "fr"
    """

    def __init__(self, data: dict[str, Any]):
        self._data = data
        self._sync_from_data()

    def _sync_from_data(self):
        """Sync instance attributes from data dictionary."""
        hints = get_type_hints(self.__class__)

        for name, _type_hint in hints.items():
            if name.startswith("_"):
                continue

            if name in self._data:
                setattr(self, f"_{name}", self._data[name])
            else:
                field_obj = getattr(self.__class__, name, None)
                if isinstance(field_obj, Field):
                    default_value = field_obj._get_default()
                    setattr(self, f"_{name}", default_value)
                    self._data[name] = default_value

    def _sync_to_data(self):
        """Sync instance attributes to data dictionary."""
        hints = get_type_hints(self.__class__)

        for name in hints:
            if name.startswith("_"):
                continue

            value = getattr(self, f"_{name}", None)
            if value is not None:
                self._data[name] = value

    def __setattr__(self, name: str, value: Any):
        """Override setattr to sync to data dictionary."""
        if name.startswith("_"):
            super().__setattr__(name, value)
        else:
            super().__setattr__(f"_{name}", value)
            if hasattr(self, "_data"):
                self._data[name] = value

    def __getattribute__(self, name: str):
        """Override getattribute for field access."""
        if name.startswith("_") or name in (
            "_sync_from_data",
            "_sync_to_data",
            "get",
            "to_dict",
            "__getitem__",
            "__setitem__",
        ):
            return super().__getattribute__(name)

        try:
            cls_attr = getattr(self.__class__, name, None)
            if isinstance(cls_attr, Field):
                return super().__getattribute__(f"_{name}")
        except Exception:
            pass

        return super().__getattribute__(name)

    def __getitem__(self, key: str) -> Any:
        return self._data.get(key)

    def __setitem__(self, key: str, value: Any):
        self._data[key] = value
        if hasattr(self, f"_{key}"):
            super().__setattr__(f"_{key}", value)

    def get(self, key: str, default: Any = None) -> Any:
        """Get state value with default."""
        return self._data.get(key, default)

    def to_dict(self) -> dict[str, Any]:
        """Convert state to dictionary."""
        self._sync_to_data()
        return self._data.copy()

    def __repr__(self) -> str:
        hints = get_type_hints(self.__class__)
        fields_str = ", ".join(
            f"{name}={getattr(self, f'_{name}', None)!r}" for name in hints if not name.startswith("_")
        )
        return f"{self.__class__.__name__}({fields_str})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self._data == other._data


# Example typed states


class CartState(SessionState):
    """Shopping cart session state."""

    items: list = Field(default_factory=list)
    total: float = Field(default=0.0)
    currency: str = Field(default="USD")


class UserPreferencesState(SessionState):
    """User preferences session state."""

    theme: str = Field(default="light")
    language: str = Field(default="en")
    notifications: bool = Field(default=True)
    timezone: str = Field(default="UTC")


__all__ = [
    "SessionState",
    "Field",
    "CartState",
    "UserPreferencesState",
]
