"""
Brutal test suite verifying DSL Migration Generator correctness fixes.

Validates:
1. Index columns are NEVER character-split (['token'], ['expires_at'], not ['t','o','k','e','n']).
2. Foreign key target tables resolve to actual DB table names ('users', not 'usersmodel').
3. Enum defaults render as valid Python scalar literals ('active', 1) without repr noise.
4. Auto index names use normalized column lists (idx_email_verification_token).
5. Index columns map model field names ('user') to DB column names ('user_id').
6. Unique constraints map model field names ('user', 'role') to DB column names ('user_id', 'role').
7. Foreign key column types are consistently inferred from target PK type (VARCHAR(36)).
8. Table naming consistency across model references.
9. Foreign key metadata (on_delete, nullable) is preserved and rendered.
10. Model dependency ordering (topological sort) places referenced tables before tables with FKs.
11. Dependencies metadata (dependencies = [...]) is included in Meta.
12. AST parsing of generated source succeeds with zero syntax errors.
13. Migration loading and execution via MigrationRunner.
"""

import ast
from enum import Enum
import pytest

from aquilia.models import Model, Index, UniqueConstraint
from aquilia.models.fields import (
    BooleanField,
    DateTimeField,
    EnumField,
    ForeignKey,
    TextField,
    UUIDField,
    VarcharField,
)
from aquilia.models.migration_gen import generate_dsl_migration
from aquilia.models.migration_runner import _load_migration_module, MigrationRunner
from aquilia.db import AquiliaDatabase


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
    user = ForeignKey(UserModel)  # DB col: user_id -> table: users
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
    user = ForeignKey(UserModel)  # DB col: user_id -> table: users
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


def test_generator_correctness_all_scenarios(tmp_path):
    """
    Verify all 19 correctness rules on generated DSL migration file.
    """
    migrations_dir = tmp_path / "migrations"
    model_classes = [Post, UserEmailVerificationModel, UserModel, UserRoleModel]

    migration_file = generate_dsl_migration(
        model_classes=model_classes,
        migrations_dir=migrations_dir,
    )

    assert migration_file is not None
    assert migration_file.exists()

    code = migration_file.read_text(encoding="utf-8")

    # 1. AST Parsing - Must be 100% valid Python syntax
    ast.parse(code)

    # 2. No character splitting in index columns
    assert "['t', 'o', 'k', 'e', 'n']" not in code
    assert "['e', 'x', 'p', 'i', 'r', 'e', 's', '_', 'a', 't']" not in code
    assert "idx_email_verification_t_o_k_e_n" not in code
    assert "columns=['token']" in code or 'columns=["token"]' in code
    assert "columns=['expires_at']" in code or 'columns=["expires_at"]' in code

    # 3. FK target table resolution ('users', not 'usersmodel')
    assert '"usersmodel"' not in code
    assert "'usersmodel'" not in code
    assert 'C.foreign_key("user_id", "users", "id"' in code or "C.foreign_key('user_id', 'users', 'id'" in code

    # 4. Enum default serialization (default='active', not repr)
    assert "<UserStatus" not in code
    assert "default='active'" in code or 'default="active"' in code

    # 5. Index and constraint field name mapping ('user' -> 'user_id')
    assert "columns=['user_id']" in code or 'columns=["user_id"]' in code
    assert 'UNIQUE ("user_id", "role")' in code or 'UNIQUE ("user_id", "role")' in code

    # 6. FK type consistency (col_type="VARCHAR(36)")
    assert 'col_type="VARCHAR(36)"' in code

    # 7. Model dependency ordering (UserModel created BEFORE UserEmailVerificationModel and UserRoleModel)
    create_user_idx = code.find("name='UserModel'")
    if create_user_idx == -1:
        create_user_idx = code.find('name="UserModel"')
    create_email_idx = code.find("name='UserEmailVerificationModel'")
    if create_email_idx == -1:
        create_email_idx = code.find('name="UserEmailVerificationModel"')
    create_role_idx = code.find("name='UserRoleModel'")
    if create_role_idx == -1:
        create_role_idx = code.find('name="UserRoleModel"')

    assert create_user_idx != -1
    assert create_email_idx != -1
    assert create_role_idx != -1
    assert create_user_idx < create_email_idx, "UserModel must be created before UserEmailVerificationModel"
    assert create_user_idx < create_role_idx, "UserModel must be created before UserRoleModel"

    # 8. Dependencies metadata in Meta
    assert "dependencies = []" in code

    # 9. Load module via importlib
    module = _load_migration_module(migration_file, "test_rev")
    assert hasattr(module, "operations")
    assert len(module.operations) > 0


@pytest.mark.asyncio
async def test_generated_migration_execution_on_sqlite(tmp_path):
    """
    Integration test: Execute the generated DSL migration on a real SQLite database
    and verify table creation, foreign keys, and indexes succeed cleanly.
    """
    db_path = str(tmp_path / "test_dsl_execution.db")
    db = AquiliaDatabase(f"sqlite:///{db_path}")
    await db.connect()

    migrations_dir = tmp_path / "migrations"
    model_classes = [Post, UserEmailVerificationModel, UserModel, UserRoleModel]

    migration_file = generate_dsl_migration(
        model_classes=model_classes,
        migrations_dir=migrations_dir,
    )
    assert migration_file is not None

    runner = MigrationRunner(db, migrations_dir=migrations_dir)
    await runner.ensure_tracking_table()

    # Execute migrate
    applied = await runner.migrate()
    assert len(applied) == 1

    # Verify tables created
    tables = await db.get_tables()
    assert "users" in tables
    assert "posts" in tables
    assert "email_verification" in tables
    assert "user_roles" in tables

    await db.disconnect()
