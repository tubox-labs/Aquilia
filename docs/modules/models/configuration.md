# Models And ORM Configuration

## Configuration Entry Points

The implementation exposes the following configuration-like classes, policies, integrations, or dataclasses.

| Type | Source | Fields | Purpose |
| --- | --- | --- | --- |
| `SlotNode` | `aquilia/models/ast_nodes.py` | name: str, field_type: FieldType, type_params: tuple[Any, ...] &#124; None, modifiers: dict[str, Any], is_pk: bool, is_unique: bool, is_nullable: bool, max_length: int &#124; None, default_expr: str &#124; None, note: str &#124; None, line_number: int, source_file: str | Represents a `slot` directive -- a model field/column. |
| `LinkNode` | `aquilia/models/ast_nodes.py` | name: str, kind: LinkKind, target_model: str, fk_field: str &#124; None, back_name: str &#124; None, through_model: str &#124; None, modifiers: dict[str, Any], line_number: int, source_file: str | Represents a `link` directive -- a relationship. |
| `IndexNode` | `aquilia/models/ast_nodes.py` | fields: list[str], is_unique: bool, name: str &#124; None, line_number: int, source_file: str | Represents an `index` directive. |
| `HookNode` | `aquilia/models/ast_nodes.py` | event: str, handler_name: str, line_number: int, source_file: str | Represents a `hook` directive -- lifecycle binding. |
| `MetaNode` | `aquilia/models/ast_nodes.py` | key: str, value: str, line_number: int, source_file: str | Represents a `meta` directive. |
| `NoteNode` | `aquilia/models/ast_nodes.py` | text: str, line_number: int, source_file: str | Represents a `note` directive -- freeform documentation. |
| `ModelNode` | `aquilia/models/ast_nodes.py` | name: str, slots: list[SlotNode], links: list[LinkNode], indexes: list[IndexNode], hooks: list[HookNode], meta: dict[str, str], notes: list[str], source_file: str, start_line: int, end_line: int | Represents a complete MODEL stanza. |
| `AMDLFile` | `aquilia/models/ast_nodes.py` | path: str, models: list[ModelNode], errors: list[str] | Represents a parsed `.amdl` file containing one or more models. |
| `ColumnDef` | `aquilia/models/migration_dsl.py` | name: str, col_type: str, primary_key: bool, autoincrement: bool, unique: bool, nullable: bool, default: Any, references: tuple[str, str] &#124; None, on_delete: str, on_update: str | A column definition in the DSL. |
| `CreateModel` | `aquilia/models/migration_dsl.py` | name: str, table: str, fields: list[ColumnDef] | Create a new database table. |
| `DropModel` | `aquilia/models/migration_dsl.py` | name: str, table: str | Drop a table. |
| `RenameModel` | `aquilia/models/migration_dsl.py` | old_name: str, new_name: str, old_table: str, new_table: str | Rename a table (preserves data). |
| `AddField` | `aquilia/models/migration_dsl.py` | model_name: str, table: str, column: ColumnDef | Add a column to an existing table. |
| `RemoveField` | `aquilia/models/migration_dsl.py` | model_name: str, table: str, column_name: str | Remove a column from an existing table. |
| `AlterField` | `aquilia/models/migration_dsl.py` | model_name: str, table: str, column_name: str, new_type: str &#124; None, nullable: bool &#124; None, new_default: Any, drop_default: bool | Alter a column's type, constraints, or default. |
| `RenameField` | `aquilia/models/migration_dsl.py` | model_name: str, table: str, old_name: str, new_name: str | Rename a column (preserves data). |
| `CreateIndex` | `aquilia/models/migration_dsl.py` | name: str, table: str, columns: list[str], unique: bool, condition: str &#124; None | Create a database index. |
| `DropIndex` | `aquilia/models/migration_dsl.py` | name: str, table: str &#124; None | Drop a database index. |
| `AddConstraint` | `aquilia/models/migration_dsl.py` | table: str, constraint_sql: str | Add a constraint to a table. |
| `RemoveConstraint` | `aquilia/models/migration_dsl.py` | table: str, name: str | Remove a constraint from a table. |
| `RunSQL` | `aquilia/models/migration_dsl.py` | sql: str &#124; list[str], reverse: str &#124; list[str] | Execute raw SQL statements (forward and optionally reverse). |
| `RunPython` | `aquilia/models/migration_dsl.py` | forward: Callable &#124; None, reverse: Callable &#124; None | Execute a Python callable as a data migration step. |
| `Migration` | `aquilia/models/migration_dsl.py` | revision: str, slug: str, models: list[str], dependencies: list[str], operations: list[Operation] | Container for a set of migration operations with metadata. |
| `MigrationRecord` | `aquilia/models/migration_runner.py` | revision: str, slug: str, checksum: str, applied_at: str &#124; None | A record in the aquilia_migrations tracking table. |
| `MigrationInfo` | `aquilia/models/migrations.py` | revision: str, slug: str, models: list[str], path: Path &#124; None, applied: bool | Metadata for a single migration file. |
| `Options` | `aquilia/models/options.py` | See class attributes and constructor methods. | Parsed model options from inner Meta class. |
| `SchemaDiff` | `aquilia/models/schema_snapshot.py` | added_models: list[str], removed_models: list[str], renamed_models: list[tuple[str, str]], altered_models: dict[str, ModelDiff] | Result of comparing two snapshots. |
| `ModelDiff` | `aquilia/models/schema_snapshot.py` | added_fields: list[str], removed_fields: list[str], renamed_fields: list[tuple[str, str]], altered_fields: list[str], added_indexes: list[dict[str, Any]], removed_indexes: list[dict[str, Any]] | Changes within a single model. |

## Common Entry Points

- No dedicated workspace integration was detected from module naming. Configure this module through direct constructors, manifests, or the subsystem that owns it.

## Precedence Model

Aquilia generally resolves configuration in this order:

1. Explicit constructor arguments or typed integration dataclass values.
2. `Workspace` builder methods and `Workspace.integrate(...)` output.
3. `ConfigLoader` defaults and environment overlays.
4. Runtime defaults inside the subsystem service or provider constructor.

When this module is registered through an `AppManifest`, keep component declarations inside `modules/<name>/manifest.py` and keep cross-cutting integration settings in `workspace.py`.

## Datatype Guidance

- Prefer typed dataclasses, policy objects, and config objects listed above when they exist.
- Keep secret values in environment-backed config, not literal strings in committed workspace files.
- Keep runtime-only state in services, stores, providers, or request state rather than static configuration.
- Use `to_dict()` on integration dataclasses when you need to inspect exactly what enters `ConfigLoader`.
