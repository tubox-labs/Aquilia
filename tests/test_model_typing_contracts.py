from __future__ import annotations

from typing import cast
from unittest.mock import AsyncMock, MagicMock

import pytest

from aquilia.faults.domains import ModelRegistrationFault
from aquilia.models.base import Model
from aquilia.models.fields_module import CharField
from aquilia.models.manager import Manager


class ContractModelMetaA(Model):
    name = CharField(max_length=80)


class ContractModelMetaB(Model):
    email = CharField(max_length=120, db_column="email_addr")


def test_model_metaclass_builds_cached_field_maps() -> None:
    assert ContractModelMetaA._non_m2m_fields
    assert ContractModelMetaA._non_m2m_fields[0][0] in ContractModelMetaA._fields

    mapped_attr, mapped_field = ContractModelMetaA._col_to_attr["name"]
    assert mapped_attr == "name"
    assert mapped_field is ContractModelMetaA._fields["name"]

    assert ContractModelMetaA._reverse_fk_cache is None


def test_from_row_uses_column_to_attr_cache() -> None:
    instance = ContractModelMetaB.from_row({"email_addr": "alice@example.com"})
    typed_instance = cast(ContractModelMetaB, instance)
    assert typed_instance.email == "alice@example.com"


@pytest.mark.asyncio
async def test_unbound_manager_raises_model_registration_fault() -> None:
    manager = Manager()

    with pytest.raises(ModelRegistrationFault, match="Failed to register model '<unknown>'"):
        await manager.get(pk=1)


@pytest.mark.asyncio
async def test_manager_update_with_none_values_passes_empty_dict() -> None:
    qs = MagicMock()
    qs.update = AsyncMock(return_value=3)

    class StubManager(Manager):
        def __init__(self, queryset):
            self._queryset = queryset

        def get_queryset(self):
            return self._queryset

    manager = StubManager(qs)

    result = await manager.update(values=None)

    assert result == 3
    qs.update.assert_awaited_once_with({})
