import pytest
from aquilia.models import Model, fields, expression
from aquilia.models.fields_module import UniqueConstraint
from aquilia.models.schema_snapshot import create_snapshot, _compile_schema_expression
from aquilia.models.base import ModelMeta

def test_compile_schema_expression():
    class TestModel(Model):
        email = fields.CharField(max_length=255)

        class Meta:
            table = "test_models"

    # F("email") compiles to "email"
    f_expr = expression.F("email")
    assert _compile_schema_expression(f_expr, TestModel) == '"email"'

    # Lower("email") compiles to LOWER("email")
    # Note: because of our fix to Func.__init__ using _coerce_expression,
    # Lower("email") converts "email" to F("email") automatically.
    lower_expr = expression.Lower("email")
    assert _compile_schema_expression(lower_expr, TestModel) == 'LOWER("email")'

    # F("price") * 0.9 compiles to ("price" * 0.9)
    mul_expr = expression.F("price") * 0.9
    assert _compile_schema_expression(mul_expr, TestModel) == '("price" * 0.9)'


def test_unique_constraint_serialization():
    class TestUser(Model):
        email = fields.CharField(max_length=255)

        class Meta:
            table = "test_users"
            constraints = [
                UniqueConstraint(
                    fields=[expression.Lower("email")],
                    name="user_email_ci_unique"
                )
            ]

    # Create snapshot -- should not raise TypeError
    snapshot = create_snapshot([TestUser])

    # Verify snapshot contents
    model_snap = snapshot["models"]["TestUser"]
    assert "constraints" in model_snap
    constraints = model_snap["constraints"]
    assert len(constraints) == 1
    assert constraints[0]["type"] == "UniqueConstraint"
    assert constraints[0]["name"] == "user_email_ci_unique"
    assert constraints[0]["fields"] == ['LOWER("email")']

    # Test generate table SQL (should NOT contain the constraint)
    sql = TestUser.generate_create_table_sql()
    assert 'CONSTRAINT "user_email_ci_unique"' not in sql
    assert 'UNIQUE' not in sql

    # Test generate index SQL (should contain the unique index statement)
    idx_sql_list = TestUser.generate_index_sql()
    assert len(idx_sql_list) == 1
    assert idx_sql_list[0] == 'CREATE UNIQUE INDEX IF NOT EXISTS "user_email_ci_unique" ON "test_users" (LOWER("email"));'


def test_add_constraint_sqlite_translation():
    from aquilia.models.migration_dsl import AddConstraint

    op = AddConstraint(
        table="users",
        constraint_sql='CONSTRAINT "user_email_ci_unique" UNIQUE (LOWER("email"))'
    )
    sql_list = op.to_sql(dialect="sqlite")
    assert len(sql_list) == 1
    assert sql_list[0] == 'CREATE UNIQUE INDEX IF NOT EXISTS "user_email_ci_unique" ON "users" (LOWER("email"));'

    # Test unnamed unique constraint translation
    op_unnamed = AddConstraint(
        table="users",
        constraint_sql='UNIQUE (LOWER("email"))'
    )
    sql_unnamed = op_unnamed.to_sql(dialect="sqlite")
    assert len(sql_unnamed) == 1
    assert 'CREATE UNIQUE INDEX IF NOT EXISTS' in sql_unnamed[0]
    assert 'LOWER("email")' in sql_unnamed[0]

    # Test non-unique constraint fallback (e.g. CHECK constraint)
    op_check = AddConstraint(
        table="users",
        constraint_sql='CONSTRAINT "check_age" CHECK (age >= 18)'
    )
    sql_check = op_check.to_sql(dialect="sqlite")
    assert len(sql_check) == 1
    assert "Cannot add check/exclude constraint" in sql_check[0]

