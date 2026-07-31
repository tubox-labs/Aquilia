"""Expression-based constraints: compilation, state capture, and DDL.

An expression-based or partial UNIQUE constraint has no table-constraint form on
any dialect -- it must be emitted as a unique index. These tests pin that at
three levels: the expression compiler, the migration state built from the model,
and the SQL the backend produces for AddConstraint/RemoveConstraint.
"""

from aquilia.models import Model, expression, fields
from aquilia.models.fields_module import UniqueConstraint
from aquilia.models.migration import (
    AddConstraint,
    ProjectState,
    RemoveConstraint,
    UniqueConstraintState,
    compile_operations,
    get_backend,
)


def test_compile_schema_expression():
    class TestModel(Model):
        email = fields.CharField(max_length=255)

        class Meta:
            table = "test_models"

    # F("email") compiles to "email"
    f_expr = expression.F("email")
    assert expression.compile_schema_expression(f_expr, TestModel) == '"email"'

    # Lower("email") compiles to LOWER("email") -- Func.__init__ coerces the
    # bare string to F("email") via _coerce_expression.
    lower_expr = expression.Lower("email")
    assert expression.compile_schema_expression(lower_expr, TestModel) == 'LOWER("email")'

    # F("price") * 0.9 compiles to ("price" * 0.9)
    mul_expr = expression.F("price") * 0.9
    assert expression.compile_schema_expression(mul_expr, TestModel) == '("price" * 0.9)'


def test_unique_constraint_captured_as_expression_state():
    class TestUser(Model):
        email = fields.CharField(max_length=255)

        class Meta:
            table = "test_users"
            constraints = [UniqueConstraint(fields=[expression.Lower("email")], name="user_email_ci_unique")]

    table = ProjectState.from_models([TestUser]).tables["TestUser"]

    assert len(table.constraints) == 1
    constraint = table.constraints[0]
    assert isinstance(constraint, UniqueConstraintState)
    assert constraint.name == "user_email_ci_unique"
    # The expression is kept as compiled SQL, not flattened into a column name.
    assert constraint.expressions == ('LOWER("email")',)
    assert constraint.columns == ()
    # Expression-based uniqueness has no table-constraint form on any dialect.
    assert constraint.requires_index is True

    # So CREATE TABLE must omit it, and the index SQL must carry it.
    sql = TestUser.generate_create_table_sql()
    assert 'CONSTRAINT "user_email_ci_unique"' not in sql
    assert "UNIQUE" not in sql

    assert TestUser.generate_index_sql() == [
        'CREATE UNIQUE INDEX IF NOT EXISTS "user_email_ci_unique" ON "test_users" (LOWER("email"));'
    ]


def _sql_for(operation, state, dialect):
    # compile_operations applies state_forwards, so it consumes the state it is
    # given -- hand it a clone so one call cannot affect the next.
    return [statement.sql for statement in compile_operations([operation], state.clone(), get_backend(dialect))]


def test_expression_constraint_becomes_unique_index_on_every_dialect():
    class ExprUser(Model):
        email = fields.CharField(max_length=255)

        class Meta:
            table = "expr_users"

    state = ProjectState.from_models([ExprUser])
    constraint = UniqueConstraintState(name="expr_email_ci_unique", expressions=('LOWER("email")',))

    # No dialect can express this as a table constraint, so none may rebuild the
    # table for it -- a rebuild would silently drop the constraint, since
    # create_table() skips index-only constraints by design.
    for dialect in ("sqlite", "postgresql", "mysql"):
        statements = _sql_for(AddConstraint(model="ExprUser", constraint=constraint), state, dialect)
        assert len(statements) == 1
        assert "CREATE UNIQUE INDEX" in statements[0]
        assert 'LOWER("email")' in statements[0]

    # And removing it drops the index rather than rebuilding. The exact syntax
    # is dialect-specific (MySQL requires the table name), so assert the shape.
    with_constraint = state.clone()
    with_constraint.tables["ExprUser"] = state.tables["ExprUser"].evolve(constraints=(constraint,))
    for dialect in ("sqlite", "postgresql", "mysql"):
        statements = _sql_for(RemoveConstraint(model="ExprUser", constraint=constraint), with_constraint, dialect)
        assert len(statements) == 1
        assert statements[0].startswith("DROP INDEX")
        assert "expr_email_ci_unique" in statements[0]


def test_plain_unique_constraint_still_uses_table_constraint():
    """A column-list UNIQUE has a real table-constraint form and must not
    silently degrade into an index."""

    class PlainUser(Model):
        email = fields.CharField(max_length=255)

        class Meta:
            table = "plain_users"

    state = ProjectState.from_models([PlainUser])
    constraint = UniqueConstraintState(name="plain_email_unique", columns=("email",))
    assert constraint.requires_index is False

    # PostgreSQL adds it in place.
    statements = _sql_for(AddConstraint(model="PlainUser", constraint=constraint), state, "postgresql")
    assert any("ADD CONSTRAINT" in sql for sql in statements)

    # SQLite has no ADD CONSTRAINT, so it rebuilds the table with the constraint
    # present -- and the rebuilt table carries the UNIQUE.
    statements = _sql_for(AddConstraint(model="PlainUser", constraint=constraint), state, "sqlite")
    assert any("__aq_new_plain_users" in sql for sql in statements)
    assert any("UNIQUE" in sql for sql in statements)
