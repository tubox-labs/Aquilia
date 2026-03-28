from __future__ import annotations

from aquilia.blueprints import Blueprint
from aquilia.blueprints.lenses import _ProjectedRef


class _TypedModel:
    _fields = {"name": object()}

    def __init__(self, **kwargs):
        self.name = kwargs.get("name")

    async def save(self, **kwargs):
        return None


class _TypedBlueprint(Blueprint[_TypedModel]):
    name: str

    class Spec:
        model = _TypedModel
        fields = ["name"]


def test_projection_subscript_still_returns_projected_ref():
    ref = _TypedBlueprint["summary"]
    assert isinstance(ref, _ProjectedRef)
    assert ref.projection == "summary"


def test_typed_blueprint_imprint_returns_model_instance():
    bp = _TypedBlueprint(data={"name": "Ada"})
    assert bp.is_sealed() is True

    import asyncio

    created = asyncio.run(bp.imprint())
    assert isinstance(created, _TypedModel)
    assert created.name == "Ada"
