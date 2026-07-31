"""
Tests for EnumField / CompositeField dialect parameter handling and NestedContractFacet
type-annotation features.
"""

import typing
import uuid
from enum import Enum

import pytest

from aquilia.contracts import Contract, Facet, NestedContractFacet, ward
from aquilia.contracts.transforms import lower, strip
from aquilia.models import Model
from aquilia.models.enums import TextChoices
from aquilia.models.fields import (
    CIEmailField,
    CompositeField,
    DateTimeField,
    EnumField,
    TextField,
    UUIDField,
)


class UserStatus(TextChoices):
    """Lifecycle state of a user account."""

    ACTIVE = "active", "Active"
    SUSPENDED = "suspended", "Suspended"
    DISABLED = "disabled", "Disabled"


class AppRole(TextChoices):
    """Application roles."""

    OWNER = "owner", "Owner"
    ADMIN = "admin", "Admin"
    EDITOR = "editor", "Editor"
    AUTHOR = "author", "Author"
    CONTRIBUTOR = "contributor", "Contributor"
    SUBSCRIBER = "subscriber", "Subscriber"


class AuditUserModel(Model):
    """Application user test model."""

    table = "test_audit_users"

    id = UUIDField(primary_key=True, auto=True, default=uuid.uuid4)
    name = TextField(null=False)
    email = CIEmailField(unique=True, null=False)
    status = EnumField(
        enum_class=UserStatus,
        default=UserStatus.ACTIVE,
        null=False,
    )
    created_at = DateTimeField(auto_now_add=True)


class AuditUserNameContract(Contract):
    first_name: typing.Annotated[
        str,
        Facet.text(min_length=1, max_length=150) >> strip,
    ]
    last_name: typing.Annotated[
        str,
        Facet.text(min_length=1, max_length=150) >> strip,
    ]


class AuditUserRegistrationContractAnnotation(Contract[AuditUserModel]):
    """Test contract using type-annotation syntax for NestedContractFacet."""

    name: NestedContractFacet[AuditUserNameContract]
    email: typing.Annotated[str, Facet.email() >> strip >> lower]

    class Spec:
        model = AuditUserModel
        read_only_fields = ["created_at", "status"]

    @ward(mode="async")
    async def combine_name(self, data: dict[str, typing.Any]):
        name_val = data.get("name")
        if isinstance(name_val, dict):
            first = name_val.get("first_name", "")
            last = name_val.get("last_name", "")
            data["name"] = f"{first} {last}".strip()
        return data


class AuditUserRegistrationContractDirectClass(Contract[AuditUserModel]):
    """Test contract using direct Contract class annotation syntax."""

    name: AuditUserNameContract
    email: typing.Annotated[str, Facet.email() >> strip >> lower]

    class Spec:
        model = AuditUserModel
        read_only_fields = ["created_at", "status"]

    @ward(mode="async")
    async def combine_name(self, data: dict[str, typing.Any]):
        name_val = data.get("name")
        if isinstance(name_val, dict):
            first = name_val.get("first_name", "")
            last = name_val.get("last_name", "")
            data["name"] = f"{first} {last}".strip()
        return data


class AuditUserRegistrationContractListAnnotation(Contract):
    """Test contract using list[NestedContractFacet[...]] and list[...] annotation syntax."""

    names_facet: list[NestedContractFacet[AuditUserNameContract]]
    names_direct: list[AuditUserNameContract]


# ── Unit Tests ──────────────────────────────────────────────────────────────


def test_enum_field_to_db_with_dialect():
    """Verify EnumField.to_db accepts dialect parameter without error."""
    field = EnumField(enum_class=UserStatus, store_name=False)
    assert field.to_db(UserStatus.ACTIVE, dialect="sqlite") == "active"
    assert field.to_db(UserStatus.ACTIVE, dialect="postgresql") == "active"
    assert field.to_db(None, dialect="sqlite") is None

    field_name = EnumField(enum_class=UserStatus, store_name=True)
    assert field_name.to_db(UserStatus.ACTIVE, dialect="mysql") == "ACTIVE"


def test_composite_field_to_db_with_dialect():
    """Verify CompositeField.to_db accepts dialect parameter without error."""
    field = CompositeField(schema={"foo": TextField()}, strategy="json")
    val = {"foo": "bar"}
    assert field.to_db(val, dialect="sqlite") == '{"foo": "bar"}'
    assert field.to_db(val, dialect="postgresql") == '{"foo": "bar"}'
    assert field.to_db(None, dialect="sqlite") is None


def test_nested_contract_facet_annotations_resolution():
    """Verify ContractMeta correctly introspects type annotations for nested contracts."""
    # Type-annotation with NestedContractFacet
    facets1 = AuditUserRegistrationContractAnnotation._all_facets
    assert "name" in facets1
    assert isinstance(facets1["name"], NestedContractFacet)
    assert facets1["name"].target is AuditUserNameContract

    # Direct Contract class type annotation
    facets2 = AuditUserRegistrationContractDirectClass._all_facets
    assert "name" in facets2
    assert isinstance(facets2["name"], NestedContractFacet)
    assert facets2["name"].target is AuditUserNameContract

    # List annotations
    facets3 = AuditUserRegistrationContractListAnnotation._all_facets
    assert "names_facet" in facets3
    assert "names_direct" in facets3


@pytest.mark.asyncio
async def test_user_model_imprint_with_enum_field(tmp_path):
    """
    Integration test: Ensure contract sealing and model imprinting works seamlessly
    for models containing EnumField without raising EnumField.to_db dialect error.
    """
    from aquilia.db import AquiliaDatabase

    db_path = str(tmp_path / "test_enum_imprint.db")
    db = AquiliaDatabase(f"sqlite:///{db_path}")
    await db.connect()
    AuditUserModel._db = db

    try:
        await db.execute("""
            CREATE TABLE test_audit_users (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                status TEXT NOT NULL,
                created_at TEXT
            );
        """)

        payload = {
            "name": {"first_name": "Jane", "last_name": "Doe"},
            "email": "JANE.DOE@example.com",
        }

        contract = AuditUserRegistrationContractAnnotation(data=payload)
        is_valid = await contract.is_sealed_async()
        assert is_valid, f"Contract sealing failed: {contract.errors}"

        # Imprint back to DB model -- previously failed with:
        # EnumField.to_db() got an unexpected keyword argument 'dialect'
        user = await contract.imprint()

        assert user is not None
        assert user.name == "Jane Doe"
        assert user.email == "jane.doe@example.com"
        assert user.status == UserStatus.ACTIVE
    finally:
        await db.disconnect()
        AuditUserModel._db = None


class StatusEnum(Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"


class PriorityEnum(Enum):
    LOW = 1
    HIGH = 2


def test_enum_field_migration_generation_and_loading(tmp_path):
    """
    A model with EnumField columns must generate a migration that is valid
    Python, carries scalar defaults rather than ``repr()`` noise, and reloads
    into the same operations.

    The enum class itself has no literal source form, so it is written as an
    importable ``"module.QualName"`` string and resolved on load.
    """
    import ast
    from enum import Enum

    from aquilia.models import Model
    from aquilia.models.fields import EnumField, TextField, UUIDField
    from aquilia.models.migration import MigrationEngine, load_migration_module

    class MigrationUserModel(Model):
        table = "migration_users"

        id = UUIDField(primary_key=True)
        name = TextField()
        status = EnumField(enum_class=StatusEnum, default=StatusEnum.ACTIVE, max_length=50)
        priority = EnumField(enum_class=PriorityEnum, default=PriorityEnum.LOW)

    engine = MigrationEngine(tmp_path / "migrations")
    migration_file = engine.make_migrations([MigrationUserModel])

    assert migration_file is not None
    assert migration_file.exists()

    code = migration_file.read_text(encoding="utf-8")

    # 1. Valid Python syntax.
    ast.parse(code)

    # 2. No unquoted Enum repr like <StatusEnum.ACTIVE: 'active'>.
    assert "<StatusEnum" not in code
    assert "<PriorityEnum" not in code

    # 3. Defaults are the members' scalar values.
    assert 'default="active"' in code
    assert "default=1" in code

    # 4. The enum is named by an importable path, not embedded.
    assert f'enum_class="{__name__}.StatusEnum"' in code

    # 5. Reloads into equivalent operations, with the enum class resolved back.
    node = load_migration_module(migration_file)
    assert node.operations

    columns = node.operations[0].table.columns
    assert columns["status"].field_class == "EnumField"
    assert columns["status"].default == "active"
    assert columns["priority"].default == 1

    rebuilt = columns["status"].rebuild_field()
    assert rebuilt.enum_class is StatusEnum
