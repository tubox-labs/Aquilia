# aq manifest

Manage module manifests. Scan for controllers, services, and other components, then update `manifest.py` to sync with discovered resources.

## Usage

```bash
aq manifest <SUBCOMMAND> [OPTIONS]
```

## Subcommands

### aq manifest update

Update a module's `manifest.py` with auto-discovered resources.

```bash
aq manifest update <MODULE> [OPTIONS]
```

| Argument  | Description       | Required |
| --------- | ----------------- | -------- |
| `MODULE`  | Module name       | Yes      |

| Option     | Description                                                    | Default |
| ---------- | -------------------------------------------------------------- | ------- |
| `--check`  | Fail if manifest is out of sync (CI mode)                      | `False` |
| `--freeze` | Disable auto-discovery after sync (strict/production mode)     | `False` |

### Discovery Process

1. **AST parsing** — Parses `manifest.py` to extract existing controller and service declarations
2. **Package scanning** — Scans the module package for controllers and services
3. **Diff calculation** — Compares declared vs discovered components
4. **Manifest update** — Writes discovered components into `manifest.py`

### Controller Discovery

Scans these locations within a module:

- `modules/<name>/controllers.py`
- `modules/<name>/test_routes.py`
- `modules/<name>/handlers.py`
- `modules/<name>/views.py`
- `modules/<name>/routes.py`

Plus intelligent file pattern matching for other files containing:

- Classes ending in `Controller`, `Handler`, or `View`
- Classes with `__controller_routes__` or `prefix` attributes
- Classes with HTTP method methods (`get`, `post`, `put`, `delete`)

### Service Discovery

Scans `modules/<name>/services.py` for:

- Classes ending in `Service`
- Classes with `__di_scope__` attribute

### Manifest Format Detection

Supports both declaration styles:

**AppManifest dataclass:**

```python
manifest = AppManifest(
    name="users",
    version="0.1.0",
    controllers=["modules.users.controllers:UsersController"],
    services=["modules.users.services:UserService"],
)
```

**Module builder fluent:**

```python
manifest = Module("users").register_controllers(
    "modules.users.controllers:UsersController"
).register_services(
    "modules.users.services:UserService"
)
```

### Check Mode (`--check`)

Use in CI/CD pipelines to verify manifests are in sync:

```bash
aq manifest update mymod --check
```

Exits with code `1` if the manifest is out of sync, printing missing/extra controllers and services.

### Freeze Mode (`--freeze`)

Sets `auto_discover(False)` on the manifest to lock it at the current state. Used in production to prevent runtime auto-discovery:

```bash
aq manifest update mymod --freeze
```

## Examples

```bash
# Sync a module's manifest
aq manifest update users

# Check if manifest is in sync (CI mode)
aq manifest update users --check

# Freeze manifest for production
aq manifest update users --freeze
```

## See Also

- [`aq discover --sync`](discover.md) — Auto-discover and sync all modules
- [`aq validate`](validate.md) — Validate manifest consistency