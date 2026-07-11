"""
Data Utilities - Provides flexible data structures for the framework.
"""

from typing import Any


class CallableList(list):
    __slots__ = ("_method",)

    def __init__(self, val, method):
        super().__init__(val)
        self._method = method

    def __call__(self, *args, **kwargs):
        return self._method(*args, **kwargs)


class CallableDict(dict):
    __slots__ = ("_method",)

    def __init__(self, val, method):
        super().__init__(val)
        self._method = method

    def __call__(self, *args, **kwargs):
        return self._method(*args, **kwargs)


class CallableSet(set):
    __slots__ = ("_method",)

    def __init__(self, val, method):
        super().__init__(val)
        self._method = method

    def __call__(self, *args, **kwargs):
        return self._method(*args, **kwargs)


class CallableStr(str):
    def __new__(cls, val, method):
        obj = str.__new__(cls, val)
        obj._method = method
        return obj

    def __call__(self, *args, **kwargs):
        return self._method(*args, **kwargs)


class CallableTuple(tuple):
    def __new__(cls, val, method):
        obj = tuple.__new__(cls, val)
        obj._method = method
        return obj

    def __call__(self, *args, **kwargs):
        return self._method(*args, **kwargs)


class CallableInt(int):
    def __new__(cls, val, method):
        obj = int.__new__(cls, val)
        obj._method = method
        return obj

    def __call__(self, *args, **kwargs):
        return self._method(*args, **kwargs)


class CallableFloat(float):
    def __new__(cls, val, method):
        obj = float.__new__(cls, val)
        obj._method = method
        return obj

    def __call__(self, *args, **kwargs):
        return self._method(*args, **kwargs)


class CallableFallback:
    __slots__ = ("_val", "_method")

    def __init__(self, val: Any, method: Any):
        self._val = val
        self._method = method

    def __call__(self, *args, **kwargs):
        return self._method(*args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._val, name)

    def __getitem__(self, item: Any) -> Any:
        return self._val[item]

    def __len__(self) -> int:
        return len(self._val)

    def __iter__(self) -> Any:
        return iter(self._val)

    def __repr__(self) -> str:
        return repr(self._val)

    def __str__(self) -> str:
        return str(self._val)

    def __eq__(self, other: Any) -> bool:
        return self._val == other

    def __bool__(self) -> bool:
        return bool(self._val)


def wrap_callable_attribute(value: Any, method: Any) -> Any:
    """
    Wrap a value in a subclass that also behaves like a callable dict method.
    This solves namespace collisions when a dictionary has keys matching standard method names.
    """
    if isinstance(value, list):
        return CallableList(value, method)
    if isinstance(value, dict):
        return CallableDict(value, method)
    if isinstance(value, set):
        return CallableSet(value, method)
    if isinstance(value, str):
        return CallableStr(value, method)
    if isinstance(value, tuple):
        return CallableTuple(value, method)
    if isinstance(value, int) and not isinstance(value, bool):
        return CallableInt(value, method)
    if isinstance(value, float):
        return CallableFloat(value, method)
    return CallableFallback(value, method)


class DataObject(dict):
    """
    A dictionary subclass that supports dot-notation access to its keys.

    This is used for validated data in serializers and contracts to provide
    a Pydantic-like or JavaScript-like developer experience.

    Example:
        data = DataObject({"name": {"first": "Kai", "last": "A."}})
        assert data.name.first == "Kai"
        assert data["name"]["last"] == "A."
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._frozen = False

    def _wrap_value(self, value: Any) -> Any:
        """Helper to convert mapping types to DataObject instances lazily."""
        if isinstance(value, dict):
            if not isinstance(value, DataObject):
                return DataObject(value)
            return value
        elif isinstance(value, list):
            return [self._wrap_value(v) for v in value]
        elif isinstance(value, tuple):
            return tuple(self._wrap_value(v) for v in value)
        elif isinstance(value, set):
            return {self._wrap_value(v) for v in value}
        return value

    def __getitem__(self, key: Any) -> Any:
        val = super().__getitem__(key)
        wrapped = self._wrap_value(val)
        if wrapped is not val:
            dict.__setitem__(self, key, wrapped)
        return wrapped

    def get(self, key: Any, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default

    def items(self):
        return [(k, self[k]) for k in self]

    def values(self):
        return [self[k] for k in self]

    def __getattribute__(self, name: str) -> Any:
        if not name.startswith("_"):
            try:
                if dict.__contains__(self, name):
                    value = self[name]
                    # If this name shadows a dict method, return a callable wrapper
                    if name in ("items", "keys", "values", "get", "pop", "copy", "update", "clear", "setdefault"):
                        method = getattr(super(), name)
                        return wrap_callable_attribute(value, method)
                    return value
            except KeyError:
                pass
        return super().__getattribute__(name)

    def __getattr__(self, name: str) -> Any:
        try:
            value = self[name]
            return value
        except KeyError:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'") from None

    def __setitem__(self, key: Any, value: Any) -> None:
        if getattr(self, "_frozen", False):
            raise TypeError("DataObject is frozen and cannot be modified")
        super().__setitem__(key, value)

    def __setattr__(self, name: str, value: Any) -> None:
        if name in ("_frozen",):
            super().__setattr__(name, value)
            return
        if getattr(self, "_frozen", False):
            raise TypeError("DataObject is frozen and cannot be modified")
        self[name] = value

    def __delitem__(self, key: Any) -> None:
        if getattr(self, "_frozen", False):
            raise TypeError("DataObject is frozen and cannot be modified")
        super().__delitem__(key)

    def __delattr__(self, name: str) -> None:
        if getattr(self, "_frozen", False):
            raise TypeError("DataObject is frozen and cannot be modified")
        try:
            del self[name]
        except KeyError:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'") from None

    def update(self, *args, **kwargs) -> None:
        if getattr(self, "_frozen", False):
            raise TypeError("DataObject is frozen and cannot be modified")
        temp = dict(*args, **kwargs)
        for k, v in temp.items():
            self[k] = v

    def setdefault(self, key: Any, default: Any = None) -> Any:
        if getattr(self, "_frozen", False):
            raise TypeError("DataObject is frozen and cannot be modified")
        if key not in self:
            self[key] = default
        return self[key]

    def pop(self, key: Any, *args) -> Any:
        if getattr(self, "_frozen", False):
            raise TypeError("DataObject is frozen and cannot be modified")
        return super().pop(key, *args)

    def popitem(self) -> tuple[Any, Any]:
        if getattr(self, "_frozen", False):
            raise TypeError("DataObject is frozen and cannot be modified")
        return super().popitem()

    def clear(self) -> None:
        if getattr(self, "_frozen", False):
            raise TypeError("DataObject is frozen and cannot be modified")
        super().clear()

    # ── Developer Convenience API ──────────────────────────────────────────

    def freeze(self) -> "DataObject":
        """Recursively freeze the DataObject and all nested DataObjects, making them immutable."""
        self._frozen = True
        for value in self.values():
            if isinstance(value, DataObject):
                value.freeze()
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, DataObject):
                        item.freeze()
        return self

    def is_frozen(self) -> bool:
        """Returns True if the DataObject is frozen."""
        return getattr(self, "_frozen", False)

    def to_dict(self, recursive: bool = True) -> dict[str, Any]:
        """Convert DataObject back to a plain nested Python dict."""
        if not recursive:
            return dict(self)
        return self._to_plain_value(self)

    def to_plain(self) -> dict[str, Any]:
        """Alias for to_dict(recursive=True) returning a standard nested python dict."""
        return self.to_dict(recursive=True)

    def _to_plain_value(self, value: Any) -> Any:
        """Recursively convert DataObjects back to plain Python structures."""
        if isinstance(value, (DataObject, dict)):
            return {k: self._to_plain_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._to_plain_value(v) for v in value]
        elif isinstance(value, tuple):
            return tuple(self._to_plain_value(v) for v in value)
        elif isinstance(value, set):
            return {self._to_plain_value(v) for v in value}
        return value

    def find(self, path: str, default: Any = None) -> Any:
        """
        Safely retrieve a nested value using a dot-separated path.
        Example: data.find("user.profile.name", "Guest")
        """
        if not path:
            return default
        parts = path.split(".")
        current: Any = self
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part, default)
            elif isinstance(current, DataObject):
                current = dict.get(current, part, default)
            elif hasattr(current, part):
                current = getattr(current, part, default)
            else:
                try:
                    current = current[part]
                except (KeyError, TypeError, IndexError):
                    try:
                        current = current[int(part)]
                    except (ValueError, IndexError, KeyError, TypeError):
                        return default
        return current

    def flatten(self, separator: str = ".") -> dict[str, Any]:
        """
        Flatten a nested DataObject into a single-level dictionary with dot-separated keys.
        """
        result = {}

        def _flatten_node(node, prefix):
            if isinstance(node, dict):
                for k, v in node.items():
                    _flatten_node(v, f"{prefix}{k}{separator}")
            elif isinstance(node, (list, tuple)):
                for i, v in enumerate(node):
                    _flatten_node(v, f"{prefix}{i}{separator}")
            else:
                key = prefix[: -len(separator)] if prefix else ""
                result[key] = node

        _flatten_node(self, "")
        return result

    def update_recursive(self, other: Any) -> "DataObject":
        """Recursively update this DataObject with values from another mapping."""
        if getattr(self, "_frozen", False):
            raise TypeError("DataObject is frozen and cannot be modified")
        if not isinstance(other, dict):
            raise TypeError("update_recursive expects a dictionary or DataObject")

        for key, value in other.items():
            if key in self and isinstance(self[key], DataObject) and isinstance(value, dict):
                self[key].update_recursive(value)
            else:
                self[key] = value
        return self

    def merge(self, other: Any) -> "DataObject":
        """
        Merge this DataObject with another dictionary and return a new DataObject.
        Does not mutate the original.
        """
        import copy

        new_obj = copy.deepcopy(self)
        if new_obj.is_frozen():
            new_obj._frozen = False
        new_obj.update_recursive(other)
        if self.is_frozen():
            new_obj.freeze()
        return new_obj

    def to_json(self, **kwargs) -> str:
        """Serialize the DataObject directly to a JSON string."""
        import json

        from aquilia.response import _json_default_serializer

        if "default" not in kwargs:
            kwargs["default"] = _json_default_serializer
        return json.dumps(self.to_plain(), **kwargs)

    def __repr__(self) -> str:
        frozen_str = " (frozen)" if getattr(self, "_frozen", False) else ""
        return f"DataObject({super().__repr__()}){frozen_str}"

    def __str__(self) -> str:
        import pprint

        return pprint.pformat(dict(self))
