"""
Data Utilities - Provides flexible data structures for the framework.
"""

from typing import Any


class DataObject(dict):
    """
    A dictionary subclass that supports dot-notation access to its keys.
    
    This is used for validated data in serializers and blueprints to provide
    a Pydantic-like or JavaScript-like developer experience.
    
    Example:
        data = DataObject({"name": {"first": "Kai", "last": "A."}})
        assert data.name.first == "Kai"
        assert data["name"]["last"] == "A."
    """

    def __getattr__(self, name: str) -> Any:
        try:
            value = self[name]
            # Recursively wrap nested dicts
            if isinstance(value, dict) and not isinstance(value, DataObject):
                value = DataObject(value)
                self[name] = value
            return value
        except KeyError:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'") from None

    def __setattr__(self, name: str, value: Any) -> None:
        self[name] = value

    def __delattr__(self, name: str) -> None:
        try:
            del self[name]
        except KeyError:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'") from None

    def __repr__(self) -> str:
        return f"DataObject({super().__repr__()})"
