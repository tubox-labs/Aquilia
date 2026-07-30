# Topological Model Dependency Ordering

## Overview

In Aquilia v1.3.8, `diff_to_operations()` implements post-order topological dependency sorting (`_topologically_sort_models()`) for `CreateModel` operations in generated migrations.

---

## The Problem

Before v1.3.8, added models in a migration diff were processed in simple alphabetical order. For example, given the models:

- `Post` (table `posts`)
- `UserEmailVerificationModel` (table `email_verification`, referencing `users.id`)
- `UserModel` (table `users`, primary key `id`)
- `UserRoleModel` (table `user_roles`, referencing `users.id`)

Alphabetical iteration produced `CreateModel` operations in the following sequence:

1. `CreateModel(name='Post', table='posts', ...)`
2. `CreateModel(name='UserEmailVerificationModel', table='email_verification', fields=[C.foreign_key("user_id", "users", "id"), ...])`
3. `CreateModel(name='UserModel', table='users', ...)`
4. `CreateModel(name='UserRoleModel', table='user_roles', fields=[C.foreign_key("user_id", "users", "id"), ...])`

When the migration runner attempted to execute `CREATE TABLE email_verification` on PostgreSQL or SQLite with foreign key enforcement active, the execution failed with:

```
[MIGRATION_FAILED] Cannot add foreign key constraint: table 'users' does not exist
```

---

## Architectural Implementation

### Dependency Graph Construction & Topological Sorting

`_topologically_sort_models(added_models, models_data)` constructs a directed dependency graph where:
- Each node represents an added model name.
- A directed edge $A \rightarrow B$ indicates that Model $A$ contains a `ForeignKey` referencing Model $B$'s database table ($B \neq A$).

```python
def _topologically_sort_models(
    added_models: list[str],
    models_data: dict[str, Any],
) -> list[str]:
    if len(added_models) <= 1:
        return added_models

    table_to_model = {}
    for m_name in added_models:
        m_info = models_data.get(m_name, {})
        t_name = m_info.get("table", m_name.lower())
        table_to_model[t_name] = m_name

    deps: dict[str, set[str]] = {m: set() for m in added_models}
    for m_name in added_models:
        m_info = models_data.get(m_name, {})
        fields = m_info.get("fields", {})
        for f_info in fields.values():
            ref = f_info.get("references")
            if ref and isinstance(ref, dict):
                ref_table = ref.get("table")
                if ref_table and ref_table in table_to_model:
                    target_m = table_to_model[ref_table]
                    if target_m != m_name:
                        deps[m_name].add(target_m)

    sorted_models: list[str] = []
    visited: set[str] = set()
    visiting: set[str] = set()

    def visit(node: str) -> None:
        if node in visiting:
            # Cycle detected (e.g. self-referential or circular FK), break cycle gracefully
            return
        if node not in visited:
            visiting.add(node)
            for dep in sorted(deps[node]):
                visit(dep)
            visiting.remove(node)
            visited.add(node)
            sorted_models.append(node)

    for m_name in sorted(added_models):
        if m_name not in visited:
            visit(m_name)

    return sorted_models
```

---

## Execution Guarantees

1. **Dependency First**: Tables referenced by foreign keys (`users`) are guaranteed to appear in `CreateModel` operations before tables that reference them (`email_verification`, `user_roles`).
2. **Cycle Safety**: Self-referential models (Model $A \rightarrow$ Model $A$) ignore self-loops, and circular dependencies (Model $A \rightarrow$ Model $B \rightarrow$ Model $A$) are broken gracefully without recursion errors.
3. **Determinism**: Ties are broken using sorted model names, ensuring byte-for-byte deterministic migration file generation across platforms.
