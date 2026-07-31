"""
Regression: primary keys that are not auto-incrementing integers.

A ``CharField(primary_key=True)`` or ``UUIDField(primary_key=True)`` must render
as a primary key with no identity clause, and a foreign key pointing at one must
adopt *its* storage type rather than defaulting to INTEGER. Getting the second
part wrong yields a schema that creates cleanly and then fails on the first
insert, so both are asserted against generated SQL rather than against state.
"""

from __future__ import annotations

from aquilia.models.base import Model
from aquilia.models.fields_module import CharField, ForeignKey, UUIDField
from aquilia.models.migration.backends import get_backend
from aquilia.models.migration.executor import compile_operations
from aquilia.models.migration.operations import CreateModel
from aquilia.models.migration.schema import ColumnState, ProjectState, TableState


def _create_sql(table: TableState, dialect: str = "sqlite") -> str:
    return "\n".join(
        statement.sql
        for statement in compile_operations(
            [CreateModel(model=table.model, table=table)], ProjectState(), get_backend(dialect)
        )
    )


def test_char_primary_key_has_no_autoincrement():
    users = TableState.of(
        "User",
        "users",
        columns=[
            ColumnState.of("id", CharField(max_length=36, primary_key=True)),
            ColumnState.of("name", CharField(max_length=100)),
        ],
    )
    sql = _create_sql(users)

    assert '"id" VARCHAR(36) PRIMARY KEY' in sql
    assert "AUTOINCREMENT" not in sql


def test_uuid_primary_key_renders_uuid_storage_type():
    tokens = TableState.of(
        "Token",
        "tokens",
        columns=[ColumnState.of("id", UUIDField(primary_key=True))],
    )

    assert "AUTOINCREMENT" not in _create_sql(tokens)
    assert '"id" UUID PRIMARY KEY' in _create_sql(tokens, "postgresql")


def test_foreign_key_adopts_non_integer_target_type():
    class NonIntPkUser(Model):
        id = CharField(max_length=36, primary_key=True)
        name = CharField(max_length=100)

        class Meta:
            table_name = "non_int_pk_users"

    class NonIntPkVerification(Model):
        user = ForeignKey("NonIntPkUser", on_delete="CASCADE")

        class Meta:
            table_name = "non_int_pk_verifications"

    state = ProjectState.from_models([NonIntPkUser, NonIntPkVerification])
    sql = _create_sql(state.tables["NonIntPkVerification"])

    assert '"user_id" VARCHAR(36)' in sql
    assert 'REFERENCES "non_int_pk_users" ("id")' in sql
    assert "ON DELETE CASCADE" in sql
