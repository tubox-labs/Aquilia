# aq inspect

Live introspection of compiled artifacts and workspace state. Inspects routes, DI service graph, modules, fault domains, and resolved configuration without starting the server.

## Usage

```bash
aq inspect <SUBCOMMAND> [OPTIONS]
```

## Subcommands

| Subcommand | Description                              |
| ---------- | ---------------------------------------- |
| `routes`   | Show all compiled routes with metadata   |
| `di`       | Show DI service graph with scopes        |
| `modules`  | List all modules with metadata           |
| `faults`   | Show fault domains and handlers          |
| `config`   | Show resolved configuration              |

## `aq inspect routes`

Displays all HTTP routes discovered from module manifests and controllers.

```
  Route Inspection
======================================================================
  users  (prefix: /users)
     GET      /users                                     → UsersController.list_users
     POST     /users                                     → UsersController.create_user
     GET      /users/{id}                                → UsersController.get_user

  products  (prefix: /products)
     GET      /products                                  → ProductsController.list
     GET      /products/{id}                             → ProductsController.detail

──────────────────────────────────────────────────────────────────────
  Total routes: 5
  Modules:      2
```

Extracts route metadata from:

- `__controller_routes__` class attribute
- `__route__` / `_route_meta` method attributes (decorator metadata)

## `aq inspect di`

Shows registered services with their DI scopes.

```
  DI / Service Inspection
======================================================================
  users
     • UserService                       scope=app         path=modules.users.services:UserService
     • UserRepository                    scope=singleton   path=modules.users.services:UserRepository

  products
     • ProductService                    scope=app         path=modules.products.services:ProductService

──────────────────────────────────────────────────────────────────────
  Total services: 3
  Modules:        2
```

## `aq inspect modules`

Lists all modules in a table with version, route prefix, controller count, and service count.

```
  Module Inspection
======================================================================
  Module               Version    Route                Controllers  Services
  ──────────────────── ────────── ──────────────────── ──────────── ──────────
  products             0.1.0      /products            2            1
  users                0.1.0      /users               3            2

──────────────────────────────────────────────────────────────────────
  Total modules: 2
```

In verbose mode, also shows description, author, tags, and dependencies.

## `aq inspect faults`

Shows fault domain configuration for each module.

```
  Fault Domain Inspection
======================================================================
  users
     Domain:   USERS
     Strategy: propagate
     Handlers: (none)

  products
     Domain:   PRODUCTS
     Strategy: propagate
     Handlers:
       • PRODUCTS → modules.products.faults:ProductsFaultHandler

──────────────────────────────────────────────────────────────────────
  Total modules: 2
```

## `aq inspect config`

Displays the resolved configuration:

- Workspace file path and root
- Config directory contents (legacy `config/` or inline `AquilaConfig`)
- Environment variables prefixed with `AQUILIA_`

## Examples

```bash
# Show all routes
aq inspect routes

# Show DI service graph
aq inspect di

# List all modules with metadata
aq inspect modules

# Show fault domains
aq inspect faults

# Show resolved configuration
aq inspect config

# Verbose output for any subcommand
aq inspect modules -v
aq inspect di -v
```

## See Also

- [`aq validate`](validate.md) — Static manifest validation
- [`aq doctor`](index.md) — Comprehensive workspace diagnostics