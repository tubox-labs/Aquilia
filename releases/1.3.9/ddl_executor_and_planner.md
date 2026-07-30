# DDL Executor & Migration Planner Architecture

Aquilia v1.3.9 introduces two core architectural subsystems in `aquilia.models`: the **DDL Executor** (`DDLExecutor`) and the **Migration Planner** (`MigrationPlanner` & `InitialSchemaPlanner`).

Together, these modules eliminate raw SQL strings as the primary intermediate representation and replace synthetic diffing against empty snapshots with direct, typed initial schema planning.

---

## 1. DDL Executor (`DDLExecutor`)

### Overview & Motivation
Historically, migration operations compiled directly to raw Python strings (`list[str]`). During execution, runners iterated over string lists and executed string checks like `if sql.startswith("--"): continue`.

`DDLExecutor` (`aquilia.models.ddl_executor.DDLExecutor`) introduces typed `ExecutableStatement` objects, decoupling planning and compilation from database execution.

### Key Abstractions

#### `StatementType` (Enum)
Categorizes schema operations:
- `CREATE_TABLE`, `DROP_TABLE`, `ALTER_TABLE`
- `CREATE_INDEX`, `DROP_INDEX`
- `ADD_CONSTRAINT`, `REMOVE_CONSTRAINT`
- `RAW_SQL`, `PYTHON_CALLABLE`, `COMMENT`, `DIAGNOSTIC`

#### `ExecutableStatement` (Dataclass)
```python
@dataclass
class ExecutableStatement:
    sql: str = ""
    statement_type: StatementType = StatementType.RAW_SQL
    description: str = ""
    is_comment: bool = False
    python_op: Any = None
    operation: Operation | None = None
    migration_rev: str | None = None
```

#### `ExecutionResult` (Dataclass)
Captures execution metrics and diagnostics:
```python
@dataclass
class ExecutionResult:
    statements_executed: int = 0
    statements_skipped: int = 0
    duration_ms: float = 0.0
    executed_statements: list[ExecutableStatement] = field(default_factory=list)
    diagnostics: list[str] = field(default_factory=list)
```

### Execution Flow

```python
from aquilia.models import DDLExecutor, CreateModel, C

# 1. Compile DSL operations lazily to ExecutableStatement list
ops = [CreateModel(name="User", table="users", fields=[C.auto("id"), C.varchar("email", 255)])]
statements = DDLExecutor.compile_operations(ops, dialect="postgresql")

# 2. Execute statements atomically with backend adapter error tolerance
result = await DDLExecutor.execute_statements(db, statements, in_transaction=True)
print(f"Executed {result.statements_executed} DDL statements in {result.duration_ms}ms")
```

---

## 2. Migration Planner (`MigrationPlanner` & `InitialSchemaPlanner`)

### Overview & Motivation
Previously, generating an initial schema required creating a synthetic empty snapshot `{"version": 1, "models": {}}` and running generic snapshot diffing against current models.

`InitialSchemaPlanner` (`aquilia.models.migration_planner.InitialSchemaPlanner`) inspects model descriptors directly and generates clean `CreateModel`, `CreateIndex`, and `AddConstraint` operations without diffing or fabricating fake migration metadata.

### API Overview

```python
from aquilia.models import MigrationPlanner, InitialSchemaPlanner

# Generate initial schema plan directly from Model classes
plan = MigrationPlanner.plan_initial_schema()
# plan.steps[0].revision == "0000_initial_schema"
# plan.steps[0].is_initial == True

# Generate incremental migration plan from snapshot diff
plan = MigrationPlanner.plan_incremental(old_snapshot, new_snapshot, revision="20260730_120000", slug="add_user_bio")
```

---

## 3. Before vs After Architecture Comparison

### Before (v1.3.8)
```python
# ModelRegistry executed SQL directly using string lists
old_snapshot = {"version": 1, "models": {}}
snapshot = create_snapshot(ordered)
diff = compute_diff(old_snapshot, snapshot)
operations = diff_to_operations(diff, old_snapshot, snapshot)
migration = Migration(revision="initial_auto", slug="auto_create", operations=operations)
statements = migration.compile_upgrade(dialect)

async with target_db.transaction():
    for sql in statements:
        if sql.startswith("--"):
            continue
        try:
            await target_db.execute(sql)
        except Exception as idx_exc:
            if dialect == "mysql" and idx_exc.args[0] == 1061:
                pass
```

### After (v1.3.9)
```python
# ModelRegistry delegates directly to MigrationRunner
# MigrationRunner uses MigrationPlanner & DDLExecutor
plan = MigrationPlanner.plan_initial_schema(ordered_models)
executed_statements = await runner.execute_plan(plan, record_history=True)
```

---

## 4. Backend Adapter DDL Error Tolerance

All dialect-specific DDL exception logic (such as MySQL error `1061` for duplicate key names or `1091` for missing index drops) has been moved into the database adapter:

```python
# aquilia/db/backends/mysql.py
class MySQLAdapter(DatabaseAdapter):
    def should_ignore_ddl_error(self, exc: Exception, statement: Any = None) -> bool:
        cause = getattr(exc, "__cause__", exc) or exc
        code = getattr(cause, "errno", None)
        if code is None and hasattr(cause, "args") and cause.args:
            code = cause.args[0]
        return code in (1061, 1091)
```

`DDLExecutor` queries `db._adapter.should_ignore_ddl_error(exc, stmt)` automatically during DDL execution.
