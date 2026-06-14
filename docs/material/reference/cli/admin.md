# aq admin

Admin dashboard management and diagnostics. Pre-flight checks, superuser creation, and staff user management.

## Usage

```bash
aq admin <SUBCOMMAND> [OPTIONS]
```

## Subcommands

### aq admin check

Pre-flight check for admin dashboard dependencies.

```bash
aq admin check [OPTIONS]
```

| Option   | Description                                                            | Default |
| -------- | ---------------------------------------------------------------------- | ------- |
| `--fix`  | Auto-fix missing configuration by uncommenting workspace.py sections   | `False` |
| `--json` | Output results as JSON                                                 | `False` |

Validates:

1. **Admin Integration** — `Integration.admin()` is configured
2. **Sessions** — session support is configured (required for admin login)
3. **Database** — database integration with URL configured
4. **Static Files** — static files middleware configured
5. **Templates** — template engine configured
6. **Superuser** — at least one superuser exists in database
7. **Admin Assets** — `assets/` directory exists

```bash
aq admin check
aq admin check --fix
aq admin check --json
```

!!! warning "Sessions Required"
    The admin dashboard **requires** session support to function. Without it, admin login will not work. Run `aq admin setup` to auto-configure everything.

### aq admin check --fix

Automatically fixes configuration issues by:

- Uncommenting `.sessions(...)` blocks in `workspace.py`
- Enabling session policies with secure defaults

### aq admin check --json

```json
{
  "passed": false,
  "has_failures": true,
  "checks": [
    {
      "name": "Admin Integration",
      "status": "ok",
      "detail": "Integration.admin() is configured"
    },
    {
      "name": "Sessions",
      "status": "fail",
      "detail": "Sessions are NOT configured..."
    }
  ]
}
```

### aq admin createsuperuser

Create an admin superuser in the database.

```bash
aq admin createsuperuser [OPTIONS]
```

| Option         | Description                   | Required |
| -------------- | ----------------------------- | -------- |
| `--username`   | Admin username                | Yes      |
| `--email`      | Admin email                   | Yes      |
| `--password`   | Admin password                | Yes      |
| `--first-name` | First name (optional)         | No       |
| `--last-name`  | Last name (optional)          | No       |

Interactive prompts for:

- Username (min 2 chars)
- Email (validated format)
- Password (with strength requirements: 8+ chars, uppercase, lowercase, digit, special char)
- Optional profile fields: first name, last name, phone, bio, timezone, locale

Password is stored using **Argon2id/PBKDF2** hashing.

```bash
aq admin createsuperuser
aq admin createsuperuser --username=admin --email=admin@site.com --password=secret
aq admin createsuperuser --first-name=John --last-name=Doe
```

!!! note "Prerequisites"
    Run `aq db migrate` before creating a superuser to ensure the `admin_users` table exists. The command auto-creates required tables if missing, but migration is recommended.

### aq admin createstaff

Create an admin staff user with limited dashboard access.

```bash
aq admin createstaff [OPTIONS]
```

| Option         | Description                   | Required |
| -------------- | ----------------------------- | -------- |
| `--username`   | Staff username                | Yes      |
| `--email`      | Staff email                   | Yes      |
| `--password`   | Staff password                | Yes      |
| `--first-name` | First name (optional)         | No       |
| `--last-name`  | Last name (optional)          | No       |

Staff users have limited dashboard access compared to superusers. They cannot manage other admin users or modify permissions unless explicitly granted.

```bash
aq admin createstaff
aq admin createstaff --username=editor --email=editor@site.com --password=secret
```

## Password Requirements

All admin passwords must:

- Be at least 8 characters
- Contain at least one uppercase letter
- Contain at least one lowercase letter
- Contain at least one digit
- Contain at least one special character (`!@#$%^&*` and others)

## Examples

```bash
# Pre-flight check
aq admin check

# Check with auto-fix
aq admin check --fix

# Check in CI (JSON output)
aq admin check --json

# Create superuser interactively
aq admin createsuperuser

# Create superuser non-interactively
aq admin createsuperuser --username=admin --email=admin@site.com --password=StrongP@ss1

# Create staff user
aq admin createstaff --username=editor --email=editor@site.com --password=StaffP@ss1
```

## See Also

- [`aq db`](migrate.md) — Database migrations
- [`aq run`](run.md) — Start the development server