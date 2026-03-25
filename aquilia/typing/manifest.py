from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, TypeAlias

from .common import JSONValue

ManifestName: TypeAlias = str
ModuleName: TypeAlias = str
ClassPath: TypeAlias = str
FeatureName: TypeAlias = str

ManifestObject: TypeAlias = type | str
ManifestCollection: TypeAlias = list[ManifestObject]
ManifestMetadata: TypeAlias = dict[str, JSONValue]


@dataclass(frozen=True)
class ManifestDescriptor:
    name: ManifestName
    module: ModuleName
    class_path: ClassPath


class ManifestLike(Protocol):
    name: str
