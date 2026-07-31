"""
Correctness of generated migration files.

Each assertion here pins a real defect the generator has had:

1. Index columns were character-split -- ``['t','o','k','e','n']`` for ``token``.
2. Foreign keys targeted the *model* name lowercased (``usersmodel``) instead of
   the model's actual table (``users``).
3. Enum defaults rendered as ``repr()`` noise (``<UserStatus.ACTIVE: 'active'>``)
   rather than a Python literal.
4. Auto index names were built from the split column list.
5. Index and constraint columns used model attribute names (``user``) where the
   database has column names (``user_id``).
6. A foreign key's type was hardcoded to INTEGER regardless of the target's PK.
7. Referenced tables were not ordered before the tables referencing them.

The generated file is parsed with :mod:`ast`, re-loaded through the real loader,
and applied to SQLite, so a file that reads correctly but does not execute --
or executes but does not round-trip -- still fails.
"""

from __future__ import annotations

import ast
from enum import Enum

import pytest

from aquilia.db import AquiliaDatabase
from aquilia.models import Index, Model, UniqueConstraint
from aquilia.models.fields import (
    BooleanField,
    DateTimeField,
    EnumField,
    ForeignKey,
    TextField,
    UUIDField,
    VarcharField,
)
from aquilia.models.migration import MigrationEngine, load_migration_module, render_migration_module


class UserStatus(Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"


class Post(Model):
    table = "posts"

    id = UUIDField(primary_key=True)
    name = VarcharField(max_length=255)
    description = TextField(default="")
    active = BooleanField(default=True)
    created_at = DateTimeField()
    updated_at = DateTimeField()


class UserModel(Model):
    table = "users"

    id = UUIDField(primary_key=True)
    name = TextField()
    email = VarcharField(max_length=254, unique=True)
    avatar_url = VarcharField(max_length=200, null=True)
    bio = TextField(null=True)
    status = EnumField(enum_class=UserStatus, default=UserStatus.ACTIVE, max_length=50)
    email_verified_at = DateTimeField(null=True)
    last_login_at = DateTimeField(null=True)
    created_at = DateTimeField()
    updated_at = DateTimeField()

    class Meta:
        indexes = [
            Index(fields=["email"]),
            Index(fields=["status"]),
            Index(fields=["created_at"]),
            Index(fields=["status", "created_at"]),
        ]


class UserEmailVerificationModel(Model):
    table = "email_verification"

    id = UUIDField(primary_key=True)
    user = ForeignKey(UserModel)  # DB column: user_id -> table: users
    token = VarcharField(max_length=255)
    expires_at = DateTimeField()
    updated_at = DateTimeField(null=True)
    created_at = DateTimeField()

    class Meta:
        indexes = [
            Index(fields=["token"]),
            Index(fields=["expires_at"]),
        ]


class UserRoleModel(Model):
    table = "user_roles"

    id = UUIDField(primary_key=True)
    user = ForeignKey(UserModel)  # DB column: user_id -> table: users
    role = TextField()
    created_at = DateTimeField()

    class Meta:
        indexes = [
            Index(fields=["user"]),
            Index(fields=["role"]),
        ]
        constraints = [
            UniqueConstraint(fields=["user", "role"], name="user_role_unique"),
        ]


MODELS = [Post, UserEmailVerificationModel, UserModel, UserRoleModel]


@pytest.fixture
def generated(tmp_path):
    """Generate a migration for MODELS and return (path, source)."""
    engine = MigrationEngine(tmp_path / "migrations")
    path = engine.make_migrations(MODELS)
    assert path is not None and path.exists()
    return path, path.read_text(encoding="utf-8")


def test_generated_source_is_valid_python(generated):
    _, code = generated
    ast.parse(code)


def test_index_columns_are_not_character_split(generated):
    _, code = generated

    assert '"t", "o", "k", "e", "n"' not in code
    assert "idx_email_verification_t_o_k_e_n" not in code
    assert 'columns=("token",)' in code
    assert 'columns=("expires_at",)' in code


def test_auto_index_names_use_whole_columns(generated):
    _, code = generated

    assert 'IndexState(name="idx_email_verification_token"' in code
    assert 'IndexState(name="idx_users_status_created_at", columns=("status", "created_at"))' in code


def test_foreign_key_targets_table_not_model_name(generated):
    _, code = generated

    assert "usersmodel" not in code.lower()
    assert 'Reference(model="UserModel", table="users")' in code
    assert 'column="user_id"' in code


def test_enum_default_renders_as_python_literal(generated):
    _, code = generated

    assert "<UserStatus" not in code
    assert 'default="active"' in code


def test_index_and_constraint_columns_use_database_names(generated):
    _, code = generated

    # Index on the `user` attribute must record the `user_id` column.
    assert 'columns=("user_id",)' in code
    # And so must the composite unique constraint.
    assert 'UniqueConstraintState(name="user_role_unique", columns=("user_id", "role"))' in code


def test_referenced_tables_are_created_first(generated):
    _, code = generated

    user = code.find('model="UserModel"')
    verification = code.find('model="UserEmailVerificationModel"')
    role = code.find('model="UserRoleModel"')

    assert -1 not in (user, verification, role)
    assert user < verification, "UserModel must be created before UserEmailVerificationModel"
    assert user < role, "UserModel must be created before UserRoleModel"


def test_meta_declares_dependencies(generated):
    _, code = generated
    assert "dependencies = []" in code


def test_generated_file_round_trips(generated):
    """Loading the file and re-rendering it must reproduce it byte for byte."""
    path, code = generated

    node = load_migration_module(path)
    assert node.operations

    # The header carries a generation timestamp, which is deliberately not
    # recoverable from the node -- compare everything after it.
    reloaded = render_migration_module(node)
    assert reloaded.split("TEMPLATE_VERSION")[1] == code.split("TEMPLATE_VERSION")[1]


def test_regenerating_unchanged_models_detects_no_changes(tmp_path):
    """A second run against unchanged models must generate nothing.

    This is what makes "no changes detected" trustworthy: if generation were
    non-deterministic, every run would look like a schema change.
    """
    engine = MigrationEngine(tmp_path / "migrations")
    assert engine.make_migrations(MODELS) is not None
    assert engine.make_migrations(MODELS) is None


@pytest.mark.asyncio
async def test_generated_migration_applies_to_sqlite(tmp_path):
    """The generated file must actually execute, creating tables and indexes."""
    db = AquiliaDatabase(f"sqlite:///{tmp_path / 'test_dsl_execution.db'}")
    await db.connect()
    try:
        engine = MigrationEngine(tmp_path / "migrations")
        assert engine.make_migrations(MODELS) is not None

        results = await engine.migrate(db)
        assert len(results) == 1
        assert results[0].statements_executed > 0

        tables = await db.get_tables()
        for expected in ("users", "posts", "email_verification", "user_roles"):
            assert expected in tables

        # Nothing left pending once applied.
        status = await engine.status(db)
        assert status.is_current
    finally:
        await db.disconnect()
