# Admin CLI Reference

This page is derived from the mounted Click command tree. If a source file has CLI helper functions but they are not mounted under `aq`, this page states that explicitly.

## Relationship To The `aq` CLI

The following mounted commands map to this subsystem.

| Command | Syntax | Purpose |
| --- | --- | --- |
| `aq admin check` | `aq admin check [--fix] [--json]` | Pre-flight check for admin dashboard dependencies. |
| `aq admin createsuperuser` | `aq admin createsuperuser [--username VALUE] [--email VALUE] [--password VALUE] [--first-name VALUE] [--last-name VALUE] [--no-input]` | Create an admin superuser in the database. |
| `aq admin createstaff` | `aq admin createstaff [--username VALUE] [--email VALUE] [--password VALUE] [--first-name VALUE] [--last-name VALUE] [--no-input]` | Create an admin staff user in the database. |
| `aq admin listusers` | `aq admin listusers [--database-url VALUE] [--json] [--active-only]` | List all admin users. |
| `aq admin changepassword` | `aq admin changepassword USERNAME [--password VALUE] [--database-url VALUE]` | Change an admin user's password. |
| `aq admin setup` | `aq admin setup [--non-interactive] [--database-url VALUE]` | Auto-configure all admin dependencies in workspace.py. |
| `aq admin status` | `aq admin status [--database-url VALUE]` | Show admin dashboard status and registered models. |
| `aq admin audit` | `aq admin audit [--limit VALUE] [--action VALUE] [--user VALUE]` | View admin audit trail. |

## Detailed Commands

### `aq admin check`

Pre-flight check for admin dashboard dependencies.

```bash
aq admin check [--fix] [--json]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `fix` | `--fix` | False | `False` | Auto-fix missing configuration by uncommenting workspace.py sections |
| Option | `as_json` | `--json` | False | `False` | Output results as JSON |

### `aq admin createsuperuser`

Create an admin superuser in the database.

```bash
aq admin createsuperuser [--username VALUE] [--email VALUE] [--password VALUE] [--first-name VALUE] [--last-name VALUE] [--no-input]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `username` | `--username` | False | `not set` | Admin username |
| Option | `email` | `--email` | False | `not set` | Admin email (required) |
| Option | `password` | `--password` | False | `not set` | Admin password |
| Option | `first_name` | `--first-name` | False | `` | First name (optional) |
| Option | `last_name` | `--last-name` | False | `` | Last name (optional) |
| Option | `no_input` | `--no-input` | False | `False` | Non-interactive mode (requires all options) |

### `aq admin createstaff`

Create an admin staff user in the database.

```bash
aq admin createstaff [--username VALUE] [--email VALUE] [--password VALUE] [--first-name VALUE] [--last-name VALUE] [--no-input]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `username` | `--username` | False | `not set` | Staff username |
| Option | `email` | `--email` | False | `not set` | Staff email (required) |
| Option | `password` | `--password` | False | `not set` | Staff password |
| Option | `first_name` | `--first-name` | False | `` | First name (optional) |
| Option | `last_name` | `--last-name` | False | `` | Last name (optional) |
| Option | `no_input` | `--no-input` | False | `False` | Non-interactive mode (requires all options) |

### `aq admin listusers`

List all admin users.

```bash
aq admin listusers [--database-url VALUE] [--json] [--active-only]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `database_url` | `--database-url` | False | `` | Database URL |
| Option | `as_json` | `--json` | False | `False` | Output as JSON |
| Option | `active_only` | `--active-only` | False | `False` | Show only active users |

### `aq admin changepassword`

Change an admin user's password.

```bash
aq admin changepassword USERNAME [--password VALUE] [--database-url VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Argument | `username` | `username` | True | `not set` |  |
| Option | `password` | `--password` | False | `not set` | New password |
| Option | `database_url` | `--database-url` | False | `` | Database URL |

### `aq admin setup`

Auto-configure all admin dependencies in workspace.py.

```bash
aq admin setup [--non-interactive] [--database-url VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `non_interactive` | `--non-interactive, -y` | False | `False` | Skip confirmation prompts |
| Option | `database_url` | `--database-url` | False | `` | Database URL to use (default: sqlite:///db.sqlite3) |

### `aq admin status`

Show admin dashboard status and registered models.

```bash
aq admin status [--database-url VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `database_url` | `--database-url` | False | `` | Database URL |

### `aq admin audit`

View admin audit trail.

```bash
aq admin audit [--limit VALUE] [--action VALUE] [--user VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `limit` | `--limit` | False | `50` | Number of entries to show |
| Option | `action` | `--action` | False | `` | Filter by action type |
| Option | `user` | `--user` | False | `` | Filter by username |

## General Commands Useful For This Module

| Command | Why it matters |
| --- | --- |
| `aq validate` | Validates workspace manifests and catches invalid component paths. |
| `aq doctor` | Runs environment, workspace, manifest, registry, integration, and deployment diagnostics. |
| `aq inspect config` | Shows resolved config after workspace/env merging. |
| `aq inspect modules` | Lists discovered modules. |
| `aq inspect routes` | Shows compiled routes when the module contributes controllers. |
| `aq run` | Starts the dev server and executes startup wiring. |

## Error Behavior

- Click handles missing required arguments and invalid options before command callbacks run.
- Most operational commands require `workspace.py`; the root CLI guard allows help/version/init/doctor without it.
- Commands that touch external providers, databases, or files can fail with subsystem-specific faults or provider errors.
