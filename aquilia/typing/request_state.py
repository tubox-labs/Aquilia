from __future__ import annotations

from typing import Any, TypeAlias

from .common import JSONValue

RequestIdentity: TypeAlias = object
RequestSession: TypeAlias = object
RequestControllerMatch: TypeAlias = object
RequestContainerRef: TypeAlias = object

RequestState: TypeAlias = dict[str, Any]
