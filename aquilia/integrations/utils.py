from __future__ import annotations

import dataclasses
from typing import Any


def resolve_config_value(val: Any) -> Any:
    """
    Unwrap Env, Secret, and PyConfig wrappers recursively to their runtime values.
    """
    from aquilia.pyconfig import AquilaConfig, Env, Secret, _class_to_dict

    if isinstance(val, Env):
        return val.resolve()

    if isinstance(val, Secret):
        return val.reveal()

    if isinstance(val, type):
        if issubclass(val, AquilaConfig):
            return resolve_config_value(val.to_dict())
        if getattr(val, "_is_aquila_section", False):
            return resolve_config_value(_class_to_dict(val))

    if isinstance(val, dict):
        return {k: resolve_config_value(v) for k, v in val.items()}

    if isinstance(val, list):
        return [resolve_config_value(item) for item in val]
    if isinstance(val, tuple):
        return tuple(resolve_config_value(item) for item in val)
    if isinstance(val, set):
        return {resolve_config_value(item) for item in val}

    if not isinstance(val, type) and hasattr(val, "to_dict") and callable(val.to_dict):
        return resolve_config_value(val.to_dict())

    return val


def resolve_integration_fields(cls: type) -> type:
    """
    Decorator for integration dataclasses to resolve Env, Secret, and PyConfig
    objects in fields at initialization time, before validation in __post_init__.
    """
    orig_post_init = getattr(cls, "__post_init__", None)

    def new_post_init(self: Any) -> None:
        for f in dataclasses.fields(self):
            val = getattr(self, f.name)
            resolved = resolve_config_value(val)
            object.__setattr__(self, f.name, resolved)

        if orig_post_init is not None:
            orig_post_init(self)

    cls.__post_init__ = new_post_init
    return cls
