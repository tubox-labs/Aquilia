from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from pathlib import Path
from typing import TypeAlias

JSONPrimitive: TypeAlias = str | int | float | bool | None
JSONValue: TypeAlias = JSONPrimitive | list["JSONValue"] | dict[str, "JSONValue"]
JSONObject: TypeAlias = dict[str, JSONValue]
JSONLikeMapping: TypeAlias = Mapping[str, JSONValue]
JSONLikeSequence: TypeAlias = Sequence[JSONValue]

PathLike: TypeAlias = str | Path
HeaderPair: TypeAlias = tuple[bytes, bytes]
HeaderMap: TypeAlias = dict[str, str]
RawHeaderList: TypeAlias = list[HeaderPair]

QueryStringMap: TypeAlias = dict[str, str]
PathParams: TypeAlias = dict[str, str | int | float | bool]

Timestamp: TypeAlias = datetime
Milliseconds: TypeAlias = float
MetadataMap: TypeAlias = dict[str, JSONValue]
