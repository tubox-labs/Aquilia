"""
Regression tests -- UUIDField(auto=True, primary_key=True) NULL insert bug.

Root cause (fixed):
    UUIDField.__init__ builds a ``kwargs`` dict that always contains a
    "default" key (pointing to the UNSET sentinel).  The original code
    then called ``kwargs.setdefault("default", uuid.uuid4)`` -- which is a
    no-op because the key already exists, even though its value is UNSET.
    super().__init__() therefore received ``default=UNSET``, which means
    ``Field.has_default()`` returned False, ``get_default()`` returned None,
    and no UUID was ever generated.  Saving such a model produced an INSERT
    with NULL in the PK column.

Fix:
    Replace ``kwargs.setdefault(...)`` with an explicit
    ``if auto and default is UNSET: kwargs["default"] = uuid.uuid4``
    check so the callable is only skipped when the caller actually passed an
    explicit default -- not when the default parameter still holds UNSET.

Coverage:
    - auto=True, no explicit default: UUID generated automatically
    - auto=True + explicit default=uuid4 (idempotent): still generates
    - auto=True + explicit custom callable: custom callable is honoured
    - auto=False (default): no UUID generated -- NULL accepted
    - DB round-trip via create() / from_row()
    - DB round-trip via save() (unsaved instance)
    - Multiple creates produce distinct UUIDs
    - ForeignKey pointing to a UUID PK still resolves correctly
    - Migration deconstruct() emits correct snapshot
    - to_python()/to_db() round-trip
    - validate() accepts uuid.UUID, str, rejects garbage
"""

from __future__ import annotations

import uuid

import pytest
import pytest_asyncio

from aquilia.db.engine import configure_database
from aquilia.models.base import Model, ModelRegistry
from aquilia.models.fields_module import (
    UNSET,
    CharField,
    FieldValidationError,
    ForeignKey,
    UUIDField,
)


# ── Model definitions ───────────────────────────────────────────────────────

class UUIDPkModel(Model):
    """Model whose only PK is a UUIDField(auto=True)."""
    table = "uuid_pk_model"
    id = UUIDField(auto=True, primary_key=True)
    name = CharField(max_length=50)


class UUIDPkModelCustomDefault(Model):
    """UUIDField(auto=True) plus an explicit default=uuid.uuid4 callable."""
    table = "uuid_pk_model_custom_default"
    id = UUIDField(auto=True, primary_key=True, default=uuid.uuid4)
    name = CharField(max_length=50)


class UUIDPkModelNoAuto(Model):
    """UUIDField with auto=False -- PK must be supplied explicitly."""
    table = "uuid_pk_model_no_auto"
    id = UUIDField(primary_key=True, null=True)
    name = CharField(max_length=50)


class UUIDFkChild(Model):
    """FK child pointing at UUIDPkModel."""
    table = "uuid_fk_child"
    id = UUIDField(auto=True, primary_key=True)
    parent = ForeignKey("UUIDPkModel", on_delete="CASCADE")
    label = CharField(max_length=50)


# ── Fixture ──────────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def db():
    database = configure_database("sqlite:///:memory:", alias="default")
    await database.connect()

    models = [UUIDPkModel, UUIDPkModelCustomDefault, UUIDPkModelNoAuto, UUIDFkChild]
    originals: dict = {}
    for m in models:
        ModelRegistry.register(m)
        originals[m] = m._db
        m._db = database
        await database.execute(m.generate_create_table_sql())

    yield database

    for m, orig in originals.items():
        m._db = orig
    await database.disconnect()


# ── Unit tests (no DB required) ──────────────────────────────────────────────

class TestUUIDFieldInit:
    def test_auto_true_no_explicit_default_has_default(self):
        """auto=True must set default=uuid.uuid4 callable."""
        field = UUIDField(auto=True, primary_key=True)
        assert field.has_default(), (
            "UUIDField(auto=True) must have a default; "
            "setdefault() bug caused has_default() to return False"
        )
        assert callable(field.default), "default must be a callable (uuid.uuid4)"

    def test_auto_true_get_default_returns_uuid(self):
        field = UUIDField(auto=True, primary_key=True)
        val = field.get_default()
        assert isinstance(val, uuid.UUID), f"Expected uuid.UUID, got {type(val)}"

    def test_auto_true_get_default_returns_fresh_each_time(self):
        field = UUIDField(auto=True, primary_key=True)
        a = field.get_default()
        b = field.get_default()
        assert a != b, "Each get_default() call must produce a unique UUID"

    def test_auto_true_with_explicit_default_honours_caller(self):
        """Caller-supplied default=uuid4 must survive even when auto=True."""
        field = UUIDField(auto=True, primary_key=True, default=uuid.uuid4)
        assert field.has_default()
        assert callable(field.default)
        assert isinstance(field.get_default(), uuid.UUID)

    def test_auto_true_with_fixed_uuid_default(self):
        """A fixed uuid.UUID() as default must be honoured."""
        fixed = uuid.UUID("12345678-1234-5678-1234-567812345678")
        field = UUIDField(auto=True, primary_key=True, default=fixed)
        assert field.has_default()
        assert field.get_default() == fixed

    def test_auto_false_no_default(self):
        """auto=False must NOT inject a default."""
        field = UUIDField(primary_key=True)
        assert not field.has_default()
        assert field.get_default() is None

    def test_auto_attribute_stored(self):
        field = UUIDField(auto=True)
        assert field.auto is True
        field2 = UUIDField(auto=False)
        assert field2.auto is False


class TestUUIDFieldValidation:
    def test_validate_uuid_object(self):
        field = UUIDField(auto=True, primary_key=True)
        field.name = "id"
        v = uuid.uuid4()
        assert field.validate(v) == v

    def test_validate_uuid_string(self):
        field = UUIDField(auto=True, primary_key=True)
        field.name = "id"
        s = str(uuid.uuid4())
        result = field.validate(s)
        assert isinstance(result, uuid.UUID)
        assert str(result) == s

    def test_validate_invalid_string(self):
        field = UUIDField(auto=True, primary_key=True)
        field.name = "id"
        with pytest.raises(FieldValidationError):
            field.validate("not-a-uuid")

    def test_validate_none_nullable(self):
        field = UUIDField(null=True)
        field.name = "id"
        assert field.validate(None) is None

    def test_validate_empty_string_becomes_none(self):
        field = UUIDField(null=True)
        field.name = "id"
        assert field.validate("") is None
        assert field.validate("   ") is None

    def test_validate_wrong_type(self):
        field = UUIDField(auto=True, primary_key=True)
        field.name = "id"
        with pytest.raises(FieldValidationError):
            field.validate(12345)


class TestUUIDFieldSerialisation:
    def test_to_python_string(self):
        field = UUIDField()
        s = "12345678-1234-5678-1234-567812345678"
        result = field.to_python(s)
        assert isinstance(result, uuid.UUID)

    def test_to_python_uuid(self):
        field = UUIDField()
        v = uuid.uuid4()
        assert field.to_python(v) == v

    def test_to_python_none(self):
        assert UUIDField().to_python(None) is None

    def test_to_db_uuid(self):
        field = UUIDField()
        v = uuid.uuid4()
        result = field.to_db(v)
        assert isinstance(result, str)
        assert result == str(v)

    def test_to_db_none(self):
        assert UUIDField().to_db(None) is None

    def test_roundtrip(self):
        field = UUIDField()
        v = uuid.uuid4()
        assert field.to_python(field.to_db(v)) == v


class TestUUIDFieldSQLType:
    def test_sqlite(self):
        assert UUIDField().sql_type("sqlite") == "VARCHAR(36)"

    def test_postgresql(self):
        assert UUIDField().sql_type("postgresql") == "UUID"

    def test_oracle(self):
        assert UUIDField().sql_type("oracle") == "VARCHAR2(36)"

    def test_mysql(self):
        assert UUIDField().sql_type("mysql") == "VARCHAR(36)"


class TestUUIDFieldDeconstruct:
    def test_deconstruct_includes_type(self):
        field = UUIDField(auto=True, primary_key=True)
        d = field.deconstruct()
        assert d["type"] == "UUIDField"
        assert d["primary_key"] is True


# ── Integration tests (require DB) ───────────────────────────────────────────

class TestUUIDPkCreate:
    @pytest.mark.asyncio
    async def test_create_sets_uuid_pk(self, db):
        """create() must populate id with a real UUID, not None."""
        obj = await UUIDPkModel.create(name="Alice")
        assert obj.id is not None, "id must not be None after create()"
        assert isinstance(obj.id, uuid.UUID), f"Expected uuid.UUID, got {type(obj.id)}"

    @pytest.mark.asyncio
    async def test_create_two_distinct_uuids(self, db):
        a = await UUIDPkModel.create(name="A")
        b = await UUIDPkModel.create(name="B")
        assert a.id != b.id, "Each create() must produce a distinct UUID"

    @pytest.mark.asyncio
    async def test_create_fetched_back_by_pk(self, db):
        obj = await UUIDPkModel.create(name="Fetch")
        fetched = await UUIDPkModel.get(pk=obj.id)
        assert fetched.name == "Fetch"
        assert fetched.id == obj.id

    @pytest.mark.asyncio
    async def test_create_custom_default_no_regression(self, db):
        """auto=True + explicit default=uuid.uuid4 must still generate UUIDs."""
        obj = await UUIDPkModelCustomDefault.create(name="Custom")
        assert obj.id is not None
        assert isinstance(obj.id, uuid.UUID)

    @pytest.mark.asyncio
    async def test_save_new_instance_gets_uuid(self, db):
        """save() on an unsaved instance must also produce a UUID PK."""
        obj = UUIDPkModel(name="SaveTest")
        # __init__ calls get_default() -> UUID should be set already
        assert obj.id is not None, (
            "id must be set by __init__ default resolution; "
            "it should not be None before save()"
        )
        await obj.save()
        fetched = await UUIDPkModel.get(pk=obj.id)
        assert fetched.name == "SaveTest"

    @pytest.mark.asyncio
    async def test_explicit_pk_supplied_to_create(self, db):
        """Caller-supplied PK must be used as-is."""
        fixed = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
        obj = await UUIDPkModel.create(id=fixed, name="Fixed")
        assert obj.id == fixed


class TestUUIDPkRoundtrip:
    @pytest.mark.asyncio
    async def test_from_row_deserialises_uuid(self, db):
        obj = await UUIDPkModel.create(name="Row")
        # Fetch via raw SQL to check from_row() deserialization
        row = await db.fetch_one(
            f'SELECT * FROM uuid_pk_model WHERE "id" = ?',
            [str(obj.id)],
        )
        assert row is not None
        restored = UUIDPkModel.from_row(row)
        assert restored.id == obj.id
        assert isinstance(restored.id, uuid.UUID)

    @pytest.mark.asyncio
    async def test_filter_by_uuid_pk(self, db):
        obj = await UUIDPkModel.create(name="FilterByUUID")
        results = await UUIDPkModel.objects.filter(id=obj.id).all()
        assert len(results) == 1
        assert results[0].id == obj.id


class TestUUIDForeignKey:
    @pytest.mark.asyncio
    async def test_fk_child_references_uuid_pk(self, db):
        parent = await UUIDPkModel.create(name="Parent")
        child = await UUIDFkChild.create(parent=parent, label="child-1")
        assert child.id is not None
        assert isinstance(child.id, uuid.UUID)

    @pytest.mark.asyncio
    async def test_multiple_children_same_parent(self, db):
        parent = await UUIDPkModel.create(name="SharedParent")
        c1 = await UUIDFkChild.create(parent=parent, label="c1")
        c2 = await UUIDFkChild.create(parent=parent, label="c2")
        assert c1.id != c2.id
