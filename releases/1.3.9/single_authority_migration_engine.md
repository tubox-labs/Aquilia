# Single-Authority Migration Engine Architecture

In Aquilia v1.3.9, the database schema execution and planning pipeline achieves full architectural unification under a single authority: the **Migration Engine** (`MigrationRunner`, `MigrationPlanner`, and `DDLExecutor`).

---

## Background & Problem Statement

Prior to v1.3.9, Aquilia suffered from architectural split-brain responsibility between `ModelRegistry` and `MigrationRunner`:

1. **`ModelRegistry` as an Execution Authority**:
   - `ModelRegistry.create_tables()` generated synthetic migrations by diffing current models against an empty snapshot.
   - It managed its own statement iteration loop (`for sql in statements:`), checked comment prefixes manually (`sql.startswith("--")`), managed its own atomic transaction blocks (`async with target_db.transaction():`), and contained hardcoded MySQL error handling (e.g. error `1061`).
   - Initial table creation executed directly on `target_db` and **bypassed `aquilia_migrations` tracking entirely**, leading to databases existing with empty migration history tables.

2. **`MigrationRunner` as a Parallel Execution Authority**:
   - `MigrationRunner` executed pending migration files (`.py`) by reading `aquilia_migrations`, compiling operations, managing separate transaction blocks, and inserting tracking rows.

This split meant that schema transformations had **two independent execution authorities**, creating maintenance overhead, logic drift between startup auto-creation and CLI migrations, and inconsistent migration tracking history.

---

## The Unified Architecture

In v1.3.9, the architecture eliminates `ModelRegistry` as an execution authority entirely:

```
Runtime / CLI / Startup Guard
           │
           ▼
     ModelRegistry
(Model Metadata & Topological Sort ONLY)
           │
           ▼
    MigrationPlanner
  (InitialSchemaPlanner & Incremental Planner)
           │
           ▼
     MigrationPlan
(Typed MigrationSteps & Operations)
           │
           ▼
    MigrationRunner
(Sole Execution Engine & History Authority)
           │
           ▼
      DDLExecutor
(Typed ExecutableStatement Compilation & Execution)
           │
           ▼
    DatabaseAdapter
(Backend DDL Error Tolerance: MySQL 1061/1091, etc.)
           │
           ▼
  AquiliaDatabase Engine
```

---

## Technical Refactoring Details & Component Responsibilities

### 1. `ModelRegistry` (Metadata Authority Only)
`ModelRegistry` in `aquilia/models/registry.py` no longer executes SQL, manages transactions, compiles DSL operations, or handles driver error codes.

Its DDL methods delegate directly to `MigrationRunner`:
```python
# aquilia/models/registry.py
@classmethod
async def create_tables(cls, db: AquiliaDatabase | None = None) -> list[str]:
    with cls._lock:
        target_db = db or cls._db
        ordered = cls._topological_sort()

    if not target_db:
        raise DatabaseConnectionFault(...)

    runner = MigrationRunner(target_db, dialect=getattr(target_db, "dialect", "sqlite"))
    exec_stmts = await runner.create_initial_schema(ordered)
    return [s.sql for s in exec_stmts if s.sql and not s.is_comment]
```

### 2. `InitialSchemaPlanner` & `MigrationPlanner` (Planning Authority)
Located in `aquilia/models/migration_planner.py`:
- **`InitialSchemaPlanner.plan_from_models()`**: Directly inspects dependency-ordered model descriptors and generates `CreateModel`, `CreateIndex`, and `AddConstraint` operations without fabricating fake migration files or relying on empty-snapshot diffing hacks.
- **`MigrationPlanner.plan_initial_schema()`**: Returns a clean `MigrationPlan` with `is_initial=True` and revision `0000_initial_schema`.

### 3. `DDLExecutor` & `ExecutableStatement` (DDL Compiler & Executor)
Located in `aquilia/models/ddl_executor.py`:
- Replaces raw SQL strings (`list[str]`) as the primary intermediate representation with strongly-typed `ExecutableStatement` instances.
- Statements carry explicit categorization via `StatementType` (`CREATE_TABLE`, `ALTER_TABLE`, `CREATE_INDEX`, `PYTHON_CALLABLE`, `COMMENT`, etc.).
- Non-executable comments (`is_comment=True`) are identified during compilation and filtered without string parsing hacks during execution.
- Delegates backend error tolerance to `db.adapter.should_ignore_ddl_error()`.

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

### 4. `DatabaseAdapter` DDL Error Encapsulation
Located in `aquilia/db/backends/base.py` and backend-specific adapters (e.g. `aquilia/db/backends/mysql.py`):
- Dialect DDL quirks (such as MySQL error 1061 for duplicate key names and 1091 for non-existent drops) are encapsulated inside `DatabaseAdapter.should_ignore_ddl_error()`.
- The migration engine remains backend-agnostic.

---

## Architectural Benefits

1. **Single Execution Authority**: `MigrationRunner` (via `DDLExecutor`) is the sole component in Aquilia allowed to execute DDL statements against the database.
2. **Authoritative Revision Zero History**: Initial schema creation creates and updates `aquilia_migrations` with revision `0000_initial_schema`, maintaining clean history from revision zero.
3. **Typed Intermediate Representation**: Operations compile into structured `ExecutableStatement` objects rather than raw un-typed SQL strings.
4. **Zero Code Duplication**: Transaction management, error translation, logging, progress reporting, and metrics are centralized in `DDLExecutor` and `MigrationRunner`.
