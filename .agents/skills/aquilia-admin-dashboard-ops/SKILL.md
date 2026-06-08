---
name: aquilia-admin-dashboard-ops
description: "Build and operate Aquilia admin dashboard features. Use for AdminIntegration, AdminModules, admin templates/controllers/security/audit/users/permissions/monitoring/storage/tasks/provider pages, and aq admin commands."
---

# Aquilia Admin Dashboard Ops

## Purpose
Configure and extend the built-in Aquilia admin dashboard and admin CLI operations.

## Trigger Conditions
Use for admin dashboard setup, admin pages, users/staff/superuser management, audit logs, permissions, monitoring, storage/tasks/mail admin modules, and `aq admin` commands.

## Inputs
- Admin site title, enabled modules, security settings, database URL, user credentials, and page/module requirements.
- Whether operation is interactive or non-interactive.

## Execution Flow
1. Add `AdminIntegration(...)` to workspace and configure `AdminModules` for enabled areas.
2. Use admin CLI: `aq admin check`, `createsuperuser`, `createstaff`, `listusers`, `changepassword`, `setup`, `status`, and `audit`.
3. Extend templates/controllers using existing admin registry, permissions, hooks, widgets, and audit models.
4. Keep admin pages backed by implemented services and templates under `aquilia/admin/`.
5. Test admin behavior with admin tests and example admin app.

## Constraints
- Admin authentication/authorization must use existing admin security and permissions paths.
- Do not store plaintext passwords; use Aquilia password hashing paths.
- Interactive commands have prompt validation; non-interactive mode must provide required values.

## Implementation Anchors
`aquilia/admin/`, `aquilia/integrations/admin.py`, `aquilia/cli/__main__.py` admin section, `tests/test_admin*.py`, `examples/admin_dashboard_app/`.

## Examples
- `.integrate(AdminIntegration(site_title="Commerce Admin", modules=AdminModules(audit=True, monitoring=True)))`.
- Run `aq admin setup -y --database-url sqlite:///db.sqlite3`.
- Add a custom admin view by following `admin/controller.py` and templates conventions.

## Failure Handling
If admin pages are forbidden, inspect permissions and session/auth state. If setup fails, verify DB connectivity and migrations. If audit output is empty, confirm audit integration and table creation.
