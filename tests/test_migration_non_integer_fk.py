from __future__ import annotations

from aquilia.models.migration_dsl import ColumnDef, CreateModel
from aquilia.models.migration_dsl import columns as C
from aquilia.models.migration_gen import _render_column_def


def test_uuid_primary_key_renders_primary_key_true():
    """Verify that a non-autoincrement primary key (like a UUID VARCHAR) renders primary_key=True."""
    col = ColumnDef(name="id", col_type="VARCHAR(36)", primary_key=True, autoincrement=False)
    rendered = _render_column_def(col)
    assert rendered == 'C.varchar("id", 36, primary_key=True)'


def test_uuid_foreign_key_renders_custom_col_type():
    """Verify that a foreign key referencing a VARCHAR primary key renders col_type='VARCHAR(36)'."""
    col = ColumnDef(
        name="user_id",
        col_type="VARCHAR(36)",
        primary_key=False,
        references=("users", "id"),
        on_delete="CASCADE",
        on_update="CASCADE",
    )
    rendered = _render_column_def(col)
    assert rendered == 'C.foreign_key("user_id", "users", "id", col_type="VARCHAR(36)")'


def test_foreign_key_to_sql_with_custom_col_type():
    """Verify that ColumnDef compiled to SQL matches the custom col_type for foreign keys."""
    col = ColumnDef(
        name="user_id",
        col_type="VARCHAR(36)",
        references=("users", "id"),
        on_delete="CASCADE",
        on_update="CASCADE",
    )
    sql = col.to_sql("sqlite")
    assert '"user_id" VARCHAR(36) NOT NULL REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE' in sql


def test_create_model_sql_with_uuid_pk_and_fk():
    """Verify that CreateModel operation generates correct DDL for UUID primary keys and matching foreign keys."""
    op_parent = CreateModel(
        name="UsersModel",
        table="users",
        fields=[
            C.varchar("id", 36, primary_key=True),
            C.varchar("name", 100),
        ],
    )
    op_child = CreateModel(
        name="UserEmailVerificationModel",
        table="email_verification",
        fields=[
            C.auto("id"),
            C.foreign_key("user_id", "users", "id", col_type="VARCHAR(36)"),
        ],
    )

    parent_sql = op_parent.to_sql("sqlite")[0]
    child_sql = op_child.to_sql("sqlite")[0]

    assert '"id" VARCHAR(36) PRIMARY KEY' in parent_sql
    assert '"user_id" VARCHAR(36) NOT NULL REFERENCES "users"("id")' in child_sql
