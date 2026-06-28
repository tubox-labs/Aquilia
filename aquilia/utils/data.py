"""
Data Utilities - Provides flexible data structures for the framework.
"""

from typing import Any


def wrap_callable_attribute(value: Any, method: Any) -> Any:
    """Wrap a value in a subclass that also behaves like a callable dict method."""
    if isinstance(value, list):

        class CallableList(list):
            def __call__(self, *args, **kwargs):
                return method(*args, **kwargs)

        return CallableList(value)

    if isinstance(value, dict):

        class CallableDict(dict):
            def __call__(self, *args, **kwargs):
                return method(*args, **kwargs)

        return CallableDict(value)

    if isinstance(value, set):

        class CallableSet(set):
            def __call__(self, *args, **kwargs):
                return method(*args, **kwargs)

        return CallableSet(value)

    if isinstance(value, str):

        class CallableStr(str):
            def __call__(self, *args, **kwargs):
                return method(*args, **kwargs)

        return CallableStr(value)

    class CallableFallback:
        def __init__(self, val: Any):
            self._val = val

        def __call__(self, *args, **kwargs):
            return method(*args, **kwargs)

        def __getattr__(self, name: str) -> Any:
            return getattr(self._val, name)

        def __repr__(self) -> str:
            return repr(self._val)

        def __str__(self) -> str:
            return str(self._val)

    return CallableFallback(value)


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

    def __getattribute__(self, name: str) -> Any:
        if not name.startswith("_"):
            try:
                if dict.__contains__(self, name):
                    value = dict.__getitem__(self, name)
                    # Recursively wrap nested dicts
                    if isinstance(value, dict) and not isinstance(value, DataObject):
                        value = DataObject(value)
                        dict.__setitem__(self, name, value)

                    if name in ("items", "keys", "values", "get", "pop", "copy", "update", "clear"):
                        method = getattr(super(), name)
                        return wrap_callable_attribute(value, method)

                    return value
            except KeyError:
                pass
        return super().__getattribute__(name)

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
