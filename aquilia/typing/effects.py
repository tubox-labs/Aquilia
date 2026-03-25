from __future__ import annotations

from typing import NewType, Protocol, TypeAlias, TypeVar

EffectName = NewType("EffectName", str)
EffectMode = NewType("EffectMode", str)

EffectResourceT = TypeVar("EffectResourceT")

EffectMap: TypeAlias = dict[str, object]
EffectMetadata: TypeAlias = dict[str, object]


class EffectProviderProtocol(Protocol[EffectResourceT]):
    async def initialize(self) -> None: ...

    async def acquire(self, mode: str | None = None) -> EffectResourceT: ...

    async def release(self, resource: EffectResourceT, success: bool = True) -> None: ...

    async def finalize(self) -> None: ...
