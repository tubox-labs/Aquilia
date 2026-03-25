"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  COMPREHENSIVE TESTS — Model.find_or_create()                               ║
║                                                                              ║
║  Tests atomic find-or-create functionality with race-safe guarantees.       ║
║                                                                              ║
║  Coverage:                                                                   ║
║    1.  Basic Functionality — create new, find existing                       ║
║    2.  Defaults Behavior — applied on create only                           ║
║    3.  Create Defaults — override precedence                                 ║
║    4.  Unique Constraint Validation — single, composite, missing            ║
║    5.  Field Validation — invalid names, unknown fields                      ║
║    6.  Concurrency — parallel calls produce exactly one record              ║
║    7.  Edge Cases — empty defaults, auto fields, primary keys               ║
║    8.  QuerySet Integration — find_or_create via objects manager            ║
║    9.  UpsertIgnoreBuilder — SQL generation for all dialects                 ║
║                                                                              ║
║  Designed for zero tolerance: every assertion must pass.                     ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from aquilia.faults.domains import QueryFault
from aquilia.models.sql_builder import UpsertIgnoreBuilder


# ═══════════════════════════════════════════════════════════════════════════
# 1. UpsertIgnoreBuilder Tests
# ═══════════════════════════════════════════════════════════════════════════


class TestUpsertIgnoreBuilder:
    """Test UpsertIgnoreBuilder SQL generation."""

    def test_sqlite_basic(self):
        """SQLite generates INSERT ... ON CONFLICT DO NOTHING."""
        builder = UpsertIgnoreBuilder("users", dialect="sqlite")
        builder.columns("email", "name")
        builder.values("alice@test.com", "Alice")
        builder.conflict_target("email")
        sql, params = builder.build()

        assert 'INSERT INTO "users"' in sql
        assert "ON CONFLICT" in sql
        assert "DO NOTHING" in sql
        assert '"email"' in sql
        assert params == ["alice@test.com", "Alice"]

    def test_postgresql_basic(self):
        """PostgreSQL generates INSERT ... ON CONFLICT DO NOTHING."""
        builder = UpsertIgnoreBuilder("users", dialect="postgresql")
        builder.columns("email", "name")
        builder.values("alice@test.com", "Alice")
        builder.conflict_target("email")
        sql, params = builder.build()

        assert 'INSERT INTO "users"' in sql
        assert "ON CONFLICT" in sql
        assert "DO NOTHING" in sql
        assert params == ["alice@test.com", "Alice"]

    def test_mysql_basic(self):
        """MySQL generates INSERT IGNORE INTO."""
        builder = UpsertIgnoreBuilder("users", dialect="mysql")
        builder.columns("email", "name")
        builder.values("alice@test.com", "Alice")
        builder.conflict_target("email")
        sql, params = builder.build()

        assert "INSERT IGNORE INTO" in sql
        assert "ON CONFLICT" not in sql
        assert params == ["alice@test.com", "Alice"]

    def test_from_dict(self):
        """from_dict sets columns and values from dict."""
        builder = UpsertIgnoreBuilder("users", dialect="sqlite")
        builder.from_dict({"email": "alice@test.com", "name": "Alice"})
        builder.conflict_target("email")
        sql, params = builder.build()

        assert '"email"' in sql
        assert '"name"' in sql
        assert "alice@test.com" in params
        assert "Alice" in params

    def test_multiple_conflict_columns(self):
        """Composite unique constraint handled correctly."""
        builder = UpsertIgnoreBuilder("memberships", dialect="sqlite")
        builder.columns("user_id", "team_id", "role")
        builder.values(1, 2, "member")
        builder.conflict_target("user_id", "team_id")
        sql, params = builder.build()

        assert 'ON CONFLICT ("user_id", "team_id") DO NOTHING' in sql
        assert params == [1, 2, "member"]

    def test_chaining(self):
        """Methods return self for chaining."""
        builder = UpsertIgnoreBuilder("users", dialect="sqlite")
        result = builder.columns("email").values("test@test.com").conflict_target("email")
        assert result is builder


# ═══════════════════════════════════════════════════════════════════════════
# 2. SQL Dialect Specific Tests
# ═══════════════════════════════════════════════════════════════════════════


class TestDialectSpecific:
    """Test dialect-specific SQL generation."""

    def test_sqlite_on_conflict_syntax(self):
        """SQLite uses ON CONFLICT (...) DO NOTHING."""
        builder = UpsertIgnoreBuilder("users", dialect="sqlite")
        builder.from_dict({"email": "test@test.com"})
        builder.conflict_target("email")
        sql, _ = builder.build()

        assert "ON CONFLICT" in sql
        assert "DO NOTHING" in sql
        assert "INSERT IGNORE" not in sql

    def test_postgresql_on_conflict_syntax(self):
        """PostgreSQL uses ON CONFLICT (...) DO NOTHING."""
        builder = UpsertIgnoreBuilder("users", dialect="postgresql")
        builder.from_dict({"email": "test@test.com"})
        builder.conflict_target("email")
        sql, _ = builder.build()

        assert "ON CONFLICT" in sql
        assert "DO NOTHING" in sql
        assert "INSERT IGNORE" not in sql

    def test_mysql_insert_ignore_syntax(self):
        """MySQL uses INSERT IGNORE INTO."""
        builder = UpsertIgnoreBuilder("users", dialect="mysql")
        builder.from_dict({"email": "test@test.com"})
        builder.conflict_target("email")
        sql, _ = builder.build()

        assert "INSERT IGNORE INTO" in sql
        assert "ON CONFLICT" not in sql


# ═══════════════════════════════════════════════════════════════════════════
# 3. QuerySet Integration Tests
# ═══════════════════════════════════════════════════════════════════════════


class TestQuerySetIntegration:
    """Test find_or_create via QuerySet (objects manager)."""

    @pytest.mark.asyncio
    async def test_queryset_delegates_to_model(self):
        """QuerySet.find_or_create delegates to Model.find_or_create."""
        from aquilia.models.query import Q

        # Create a mock model class
        mock_model = MagicMock()
        mock_model.find_or_create = AsyncMock(return_value=(MagicMock(), True))

        # Create QuerySet with mock model
        qs = Q(model_cls=mock_model, db=None, table="test")

        result = await qs.find_or_create(
            email="test@test.com", defaults={"name": "Test"}, create_defaults={"role": "admin"}
        )

        # Verify delegation
        mock_model.find_or_create.assert_called_once_with(
            defaults={"name": "Test"}, create_defaults={"role": "admin"}, email="test@test.com"
        )


# ═══════════════════════════════════════════════════════════════════════════
# 4. Helper Method Unit Tests (using mocked internals)
# ═══════════════════════════════════════════════════════════════════════════


class TestValidateUniqueConstraint:
    """Test _validate_unique_constraint helper method."""

    def test_single_unique_field(self):
        """Single field with unique=True is valid."""
        # Create mock field objects
        mock_email_field = MagicMock()
        mock_email_field.unique = True
        mock_email_field.primary_key = False

        mock_name_field = MagicMock()
        mock_name_field.unique = False
        mock_name_field.primary_key = False

        # Create mock model with _fields and _meta
        mock_model = MagicMock()
        mock_model._fields = {"email": mock_email_field, "name": mock_name_field}
        mock_model._meta = MagicMock()
        mock_model._meta.unique_together = []
        mock_model._meta.constraints = []

        # Import the method and call it
        from aquilia.models.base import Model

        # Call the unbound method with our mock
        result = Model._validate_unique_constraint.__func__(mock_model, {"email"})
        assert result is True

    def test_primary_key_field(self):
        """Primary key field is valid for lookup."""
        mock_id_field = MagicMock()
        mock_id_field.unique = False
        mock_id_field.primary_key = True

        mock_model = MagicMock()
        mock_model._fields = {"id": mock_id_field}
        mock_model._meta = MagicMock()
        mock_model._meta.unique_together = []
        mock_model._meta.constraints = []

        from aquilia.models.base import Model

        result = Model._validate_unique_constraint.__func__(mock_model, {"id"})
        assert result is True

    def test_non_unique_field_rejected(self):
        """Non-unique field without constraint is rejected."""
        mock_name_field = MagicMock()
        mock_name_field.unique = False
        mock_name_field.primary_key = False

        mock_model = MagicMock()
        mock_model._fields = {"name": mock_name_field}
        mock_model._meta = MagicMock()
        mock_model._meta.unique_together = []
        mock_model._meta.constraints = []

        from aquilia.models.base import Model

        result = Model._validate_unique_constraint.__func__(mock_model, {"name"})
        assert result is False

    def test_unique_together(self):
        """unique_together constraint validates composite lookups."""
        mock_user_field = MagicMock()
        mock_user_field.unique = False
        mock_user_field.primary_key = False

        mock_team_field = MagicMock()
        mock_team_field.unique = False
        mock_team_field.primary_key = False

        mock_model = MagicMock()
        mock_model._fields = {"user_id": mock_user_field, "team_id": mock_team_field}
        mock_model._meta = MagicMock()
        mock_model._meta.unique_together = [("user_id", "team_id")]
        mock_model._meta.constraints = []

        from aquilia.models.base import Model

        result = Model._validate_unique_constraint.__func__(mock_model, {"user_id", "team_id"})
        assert result is True

    def test_unique_constraint_in_meta(self):
        """UniqueConstraint in Meta.constraints validates lookups."""
        from aquilia.models.fields_module import UniqueConstraint

        mock_email_field = MagicMock()
        mock_email_field.unique = False
        mock_email_field.primary_key = False

        mock_tenant_field = MagicMock()
        mock_tenant_field.unique = False
        mock_tenant_field.primary_key = False

        mock_model = MagicMock()
        mock_model._fields = {"email": mock_email_field, "tenant_id": mock_tenant_field}
        mock_model._meta = MagicMock()
        mock_model._meta.unique_together = []
        mock_model._meta.constraints = [
            UniqueConstraint(fields=["email", "tenant_id"], name="uq_email_tenant")
        ]

        from aquilia.models.base import Model

        result = Model._validate_unique_constraint.__func__(mock_model, {"email", "tenant_id"})
        assert result is True


class TestGetConflictColumns:
    """Test _get_conflict_columns helper method."""

    def test_single_unique_field(self):
        """Returns single unique field's column name."""
        mock_email_field = MagicMock()
        mock_email_field.unique = True
        mock_email_field.primary_key = False
        mock_email_field.column_name = "email_col"

        mock_model = MagicMock()
        mock_model._fields = {"email": mock_email_field}
        mock_model._meta = MagicMock()
        mock_model._meta.unique_together = []
        mock_model._meta.constraints = []

        from aquilia.models.base import Model

        result = Model._get_conflict_columns.__func__(mock_model, {"email"}, "sqlite")
        assert result == ["email_col"]

    def test_unique_together_columns(self):
        """Returns all columns from unique_together constraint."""
        mock_user_field = MagicMock()
        mock_user_field.unique = False
        mock_user_field.primary_key = False
        mock_user_field.column_name = "user_id"

        mock_team_field = MagicMock()
        mock_team_field.unique = False
        mock_team_field.primary_key = False
        mock_team_field.column_name = "team_id"

        mock_model = MagicMock()
        mock_model._fields = {"user_id": mock_user_field, "team_id": mock_team_field}
        mock_model._meta = MagicMock()
        mock_model._meta.unique_together = [("user_id", "team_id")]
        mock_model._meta.constraints = []

        from aquilia.models.base import Model

        result = Model._get_conflict_columns.__func__(mock_model, {"user_id", "team_id"}, "sqlite")
        assert set(result) == {"user_id", "team_id"}

    def test_fallback_to_lookup_fields(self):
        """Falls back to all lookup fields when no constraint matched."""
        mock_a_field = MagicMock()
        mock_a_field.unique = False
        mock_a_field.primary_key = False
        mock_a_field.column_name = "a_col"

        mock_b_field = MagicMock()
        mock_b_field.unique = False
        mock_b_field.primary_key = False
        mock_b_field.column_name = "b_col"

        mock_model = MagicMock()
        mock_model._fields = {"a": mock_a_field, "b": mock_b_field}
        mock_model._meta = MagicMock()
        mock_model._meta.unique_together = []
        mock_model._meta.constraints = []

        from aquilia.models.base import Model

        result = Model._get_conflict_columns.__func__(mock_model, {"a", "b"}, "sqlite")
        assert set(result) == {"a_col", "b_col"}


# ═══════════════════════════════════════════════════════════════════════════
# 5. Integration Tests with Patched Database
# ═══════════════════════════════════════════════════════════════════════════


class MockCursor:
    """Mock cursor for database operations."""

    def __init__(self, lastrowid=None, rowcount=0):
        self.lastrowid = lastrowid
        self.rowcount = rowcount


class MockDB:
    """Mock database for testing."""

    def __init__(self, dialect="sqlite"):
        self.dialect = dialect
        self.capabilities = MagicMock(supports_returning=False)
        self._execute_result = MockCursor(lastrowid=1)
        self._fetch_one_result = None
        self.execute_count = 0
        self.fetch_one_count = 0

    async def execute(self, sql, params=None):
        self.execute_count += 1
        return self._execute_result

    async def fetch_one(self, sql, params=None):
        self.fetch_one_count += 1
        return self._fetch_one_result


class TestFindOrCreateWithPatching:
    """Test find_or_create with database patching."""

    @pytest.mark.asyncio
    async def test_empty_lookup_raises(self):
        """Empty lookup kwargs raises QueryFault."""
        from aquilia.models.base import Model
        from aquilia.models.fields_module import CharField

        # Create a real minimal model
        class TestUser(Model):
            _table_name = "test_users"

            email = CharField(max_length=255, unique=True)

        with pytest.raises(QueryFault) as exc:
            await TestUser.find_or_create()

        assert "At least one lookup field" in str(exc.value)

    @pytest.mark.asyncio
    async def test_invalid_field_name_raises(self):
        """Invalid field names (SQL injection attempts) are rejected."""
        from aquilia.models.base import Model
        from aquilia.models.fields_module import CharField

        class TestUser(Model):
            _table_name = "test_users"

            email = CharField(max_length=255, unique=True)

        with pytest.raises(QueryFault) as exc:
            await TestUser.find_or_create(**{"email; DROP TABLE users--": "test"})

        assert "Invalid field name" in str(exc.value)

    @pytest.mark.asyncio
    async def test_unknown_field_raises(self):
        """Unknown field names raise QueryFault."""
        from aquilia.models.base import Model
        from aquilia.models.fields_module import CharField

        class TestUser(Model):
            _table_name = "test_users"

            email = CharField(max_length=255, unique=True)

        with pytest.raises(QueryFault) as exc:
            await TestUser.find_or_create(nonexistent="value")

        assert "Unknown field" in str(exc.value)

    @pytest.mark.asyncio
    async def test_missing_unique_constraint_raises(self):
        """Lookup on non-unique field raises QueryFault."""
        from aquilia.models.base import Model
        from aquilia.models.fields_module import CharField

        class TestUser(Model):
            _table_name = "test_users"

            name = CharField(max_length=255)  # Not unique

        with pytest.raises(QueryFault) as exc:
            await TestUser.find_or_create(name="Test")

        assert "unique constraint" in str(exc.value).lower()

    @pytest.mark.asyncio
    async def test_creates_new_record(self):
        """When no record exists, creates new and returns (instance, True)."""
        from aquilia.models.base import Model
        from aquilia.models.fields_module import CharField, IntegerField

        mock_db = MockDB()
        mock_db._execute_result = MockCursor(lastrowid=42)

        class TestUser(Model):
            _table_name = "test_users"

            email = CharField(max_length=255, unique=True)
            name = CharField(max_length=255, null=True)

            @classmethod
            def _get_db(cls):
                return mock_db

        instance, created = await TestUser.find_or_create(
            email="alice@test.com", defaults={"name": "Alice"}
        )

        assert created is True
        assert instance.id == 42
        assert instance.email == "alice@test.com"
        assert instance.name == "Alice"

    @pytest.mark.asyncio
    async def test_finds_existing_record(self):
        """When record exists, returns (instance, False) without modifying."""
        from aquilia.models.base import Model
        from aquilia.models.fields_module import CharField

        mock_db = MockDB()
        # Simulate conflict (no lastrowid)
        mock_db._execute_result = MockCursor(lastrowid=0, rowcount=0)
        # Return existing record on SELECT
        mock_db._fetch_one_result = {"id": 99, "email": "alice@test.com", "name": "Existing"}

        class TestUser(Model):
            _table_name = "test_users"

            email = CharField(max_length=255, unique=True)
            name = CharField(max_length=255, null=True)

            @classmethod
            def _get_db(cls):
                return mock_db

        instance, created = await TestUser.find_or_create(
            email="alice@test.com", defaults={"name": "Should Not Apply"}
        )

        assert created is False
        assert instance.id == 99
        assert instance.name == "Existing"  # Original name, not defaults
        assert mock_db.execute_count == 1  # INSERT attempted
        assert mock_db.fetch_one_count == 1  # SELECT for existing

    @pytest.mark.asyncio
    async def test_defaults_applied_on_create(self):
        """defaults are merged with lookup fields on creation."""
        from aquilia.models.base import Model
        from aquilia.models.fields_module import CharField

        mock_db = MockDB()
        mock_db._execute_result = MockCursor(lastrowid=1)

        class TestUser(Model):
            _table_name = "test_users"

            email = CharField(max_length=255, unique=True)
            name = CharField(max_length=255, null=True)
            role = CharField(max_length=50, null=True)

            @classmethod
            def _get_db(cls):
                return mock_db

        instance, created = await TestUser.find_or_create(
            email="alice@test.com", defaults={"name": "Alice", "role": "user"}
        )

        assert created is True
        assert instance.email == "alice@test.com"
        assert instance.name == "Alice"
        assert instance.role == "user"

    @pytest.mark.asyncio
    async def test_create_defaults_override_lookup_and_defaults(self):
        """create_defaults take precedence over lookup and defaults."""
        from aquilia.models.base import Model
        from aquilia.models.fields_module import CharField

        mock_db = MockDB()
        mock_db._execute_result = MockCursor(lastrowid=1)

        class TestUser(Model):
            _table_name = "test_users"

            email = CharField(max_length=255, unique=True)
            name = CharField(max_length=255, null=True)

            @classmethod
            def _get_db(cls):
                return mock_db

        instance, created = await TestUser.find_or_create(
            email="lookup@test.com",
            defaults={"name": "Default Name"},
            create_defaults={"email": "stored@test.com", "name": "Override Name"},
        )

        assert created is True
        # create_defaults should override both lookup and defaults
        assert instance.email == "stored@test.com"
        assert instance.name == "Override Name"

    @pytest.mark.asyncio
    async def test_empty_defaults_dict(self):
        """Empty defaults dict is handled correctly."""
        from aquilia.models.base import Model
        from aquilia.models.fields_module import CharField

        mock_db = MockDB()
        mock_db._execute_result = MockCursor(lastrowid=1)

        class TestUser(Model):
            _table_name = "test_users"

            email = CharField(max_length=255, unique=True)

            @classmethod
            def _get_db(cls):
                return mock_db

        # Should not raise
        instance, created = await TestUser.find_or_create(email="test@test.com", defaults={})
        assert created is True

    @pytest.mark.asyncio
    async def test_record_vanished_raises(self):
        """Raises QueryFault if record vanishes between INSERT and SELECT."""
        from aquilia.models.base import Model
        from aquilia.models.fields_module import CharField

        mock_db = MockDB()
        # Simulate conflict (no insert)
        mock_db._execute_result = MockCursor(lastrowid=0)
        # But SELECT returns nothing (record deleted)
        mock_db._fetch_one_result = None

        class TestUser(Model):
            _table_name = "test_users"

            email = CharField(max_length=255, unique=True)

            @classmethod
            def _get_db(cls):
                return mock_db

        with pytest.raises(QueryFault) as exc:
            await TestUser.find_or_create(email="vanished@test.com")

        assert "vanished" in str(exc.value).lower()


# ═══════════════════════════════════════════════════════════════════════════
# 6. Concurrency Tests (Simulated)
# ═══════════════════════════════════════════════════════════════════════════


class TestConcurrency:
    """Test concurrent find_or_create behavior."""

    @pytest.mark.asyncio
    async def test_simulated_concurrent_creates(self):
        """Simulated concurrent calls: first creates, others find."""
        from aquilia.models.base import Model
        from aquilia.models.fields_module import CharField

        created_count = {"value": 0}

        class SimulatedDB:
            dialect = "sqlite"
            capabilities = MagicMock(supports_returning=False)

            async def execute(self, sql, params=None):
                # First call succeeds with INSERT
                if created_count["value"] == 0:
                    created_count["value"] += 1
                    return MockCursor(lastrowid=1)
                else:
                    # Subsequent calls hit conflict
                    return MockCursor(lastrowid=0)

            async def fetch_one(self, sql, params=None):
                return {"id": 1, "email": "race@test.com"}

        mock_db = SimulatedDB()

        class TestUser(Model):
            _table_name = "test_users"

            email = CharField(max_length=255, unique=True)

            @classmethod
            def _get_db(cls):
                return mock_db

        # Run multiple concurrent calls
        results = await asyncio.gather(
            *[TestUser.find_or_create(email="race@test.com") for _ in range(5)]
        )

        # Exactly one should be created
        created_results = [created for _, created in results]
        assert created_results.count(True) == 1
        assert created_results.count(False) == 4

        # All should return an instance with the same ID
        instances = [inst for inst, _ in results]
        assert all(inst.id == 1 for inst in instances)
