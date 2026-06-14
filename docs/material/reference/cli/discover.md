# aq discover

Auto-discover components in module files and optionally sync them into `manifest.py`. Uses AST-based scanning for controllers, services, models, guards, pipes, and interceptors.

## Usage

```bash
aq discover [OPTIONS]
```

## Options

| Option     | Description                                                    | Default   |
| ---------- | -------------------------------------------------------------- | --------- |
| `--path`   | Workspace path                                                 | `.`       |
| `--sync`   | Auto-sync discovered components into `manifest.py` files       | `False`   |
| `--dry-run`| Preview sync changes without writing (use with `--sync`)       | `False`   |
| `--json`   | Output results as JSON                                         | `False`   |

## Discovery Report

Without flags, `aq discover` prints a summary table of all modules found in `modules/`:

```
Module Discovery Report
─────────────────────────────
Workspace: my-api
Path:      /home/user/my-api
Modules Found: 3

Module    Version  Route
users     0.1.0    /users
products  0.1.0    /products
admin     0.1.0    /admin
```

Validation results show warnings and errors for each module:

- Missing `__init__.py`
- Duplicate route prefixes
- Invalid dependency declarations

## Auto-Sync Mode (`--sync`)

Runs the `AutoDiscoveryEngine` (AST-based) to scan module source files and detect:

| Component Kind  | Detection Target                                     |
| --------------- | ---------------------------------------------------- |
| Controllers     | Classes ending in `Controller`, `Handler`, `View`    |
| Services        | Classes ending in `Service` or with `__di_scope__`   |
| Models          | `Model` subclasses                                   |
| Guards          | Classes ending in `Guard`                            |
| Pipes           | Classes with pipe-like method signatures             |
| Interceptors    | Classes with interceptor patterns                    |

For each component, the engine checks whether it is already declared in the module's `manifest.py`. New components are automatically added.

### Dry Run

```bash
aq discover --sync --dry-run
```

Shows what would be added to each `manifest.py` without actually writing changes.

### Output

```
Auto-Discovery Scan (AST)
Module    Kind         Component                      Status
users     controller   UsersController                ✓ synced
users     service      UserService                    NEW
users     model        User                           NEW
products  controller   ProductsController             ✓ synced
products  guard        AdminGuard                     NEW

Found 3 new component(s).

✓ users/manifest.py -- added UserService
✓ users/manifest.py -- added User
✓ products/manifest.py -- added AdminGuard
```

## Verbose Mode

```bash
aq discover -v
```

Shows detailed information per module including description, author, tags, dependencies, and component breakdown.

## Examples

```bash
# Basic discovery
aq discover

# Discovery with verbose details
aq discover -v

# Sync discovered components to manifest files
aq discover --sync

# Preview sync changes
aq discover --sync --dry-run

# Specific workspace path
aq discover --path=/path/to/workspace
```

## See Also

- [`aq manifest update`](manifest.md) — Manually update a manifest
- [`aq validate`](validate.md) — Validate manifest consistency
- [`aq analytics`](analytics.md) — Deep module analysis and health reports