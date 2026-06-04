"""Prompt templates for Aquilia build workflows."""

from __future__ import annotations

from ..models import KnowledgeIndex

PROMPT_NAMES = [
    "aquilia.build_workspace",
    "aquilia.add_module",
    "aquilia.build_rest_controller",
    "aquilia.add_auth_sessions",
    "aquilia.add_db_models_migrations",
    "aquilia.add_tasks_scheduler",
    "aquilia.add_websocket_realtime",
    "aquilia.add_templates_mail_i18n",
    "aquilia.add_cache_storage",
    "aquilia.enable_versioning",
    "aquilia.debug_startup_routes_di",
    "aquilia.production_hardening",
    "aquilia.generate_full_feature_app",
]

_WORKFLOW_HINTS = {
    "auth": "Use Integration.auth/AuthConfig and sessions; protect controllers with existing auth decorators/guards.",
    "db": "Use Workspace.database or Integration.database with typed DB config; use ORM model/migration commands.",
    "tasks": "Use @task plus Workspace.tasks or Integration.tasks; keep payloads serializable.",
    "websocket": "Use SocketController and socket_controllers in AppManifest.",
    "templates": "Use template/mail/i18n integrations and keep templates sandboxed.",
    "cache": "Use cache/storage integrations and filesystem path validation.",
    "versioning": "Use implemented versioning decorators/strategies.",
    "debug": "Trace AquiliaRuntime phases, Aquilary registry, DI, controller compiler/router, ASGIAdapter.",
    "production": "Use security middleware, Secret/env config, provider credential stores, and structured faults.",
}


def render_workflow_prompt(index: KnowledgeIndex, workflow: str, arguments: dict | None = None) -> str:
    arguments = arguments or {}
    goal = arguments.get("goal") or "<describe the feature>"
    hint = next((value for key, value in _WORKFLOW_HINTS.items() if key in workflow), "")
    anchors = "\n".join(f"- {fact['path']}:{fact['line']} - {fact['summary']}" for fact in index.facts[:8])
    return f"""You are working inside the Aquilia repository. Use the source code as the single source of truth.

Workflow: {workflow}
Goal: {goal}

Assumptions:
- Work through workspace.py for orchestration and modules/<name>/manifest.py for module internals.
- Prefer Python-native config with Workspace, Module, AquilaConfig, Env, Secret, and Integration.*.
- Keep the system read-only until the intended file edits are explicit.

Files To Create Or Edit:
- workspace.py only for workspace/module/integration orchestration.
- modules/<name>/manifest.py for controllers, services, models, middleware, sockets, tasks, imports, and exports.
- modules/<name>/controllers.py and service/fault/model/task/socket files as needed.
- tests/ for focused pytest coverage.

Expected Code Shape:
- Controller subclasses use @GET/@POST/etc. and return Response.json(...) or framework-supported responses.
- AppManifest has name, version, controllers/services, base_path, imports/exports, and no deprecated route_prefix/database.
- Module route prefixes live in Module(...).route_prefix(...).
- Framework-domain failures use structured Aquilia Fault subclasses.
{("- " + hint) if hint else ""}

Anti-Pattern Guards:
- Do not use Module.register_* methods.
- Do not configure AppManifest.database.
- Do not set AppManifest.route_prefix for new code.
- Do not rely on generated runtime/app.py instead of AquiliaRuntime.
- Do not add arbitrary shell/file mutation tools to MCP flows.

Source Anchors:
{anchors}

Validation Checklist:
- aq validate
- aq inspect routes when routes changed
- python -m pytest tests/ or focused pytest path
- Confirm examples/docs match actual source behavior, not stale claims.
"""
