"""Derive source-backed Aquilia architecture facts from indexed files."""

from __future__ import annotations

from ..models import SourceFile

_FACT_SPECS = [
    (
        "bootstrap.runtime_pipeline",
        "AquiliaRuntime runs configure(), discover(), then bootstrap() before exposing app/server.",
        "aquilia/runtime.py",
        ("def configure", "def discover", "def bootstrap"),
    ),
    (
        "bootstrap.entrypoint_delegates",
        "aquilia.entrypoint delegates application creation to AquiliaRuntime.",
        "aquilia/entrypoint.py",
        ("AquiliaRuntime.from_workspace",),
    ),
    (
        "config.python_native",
        "ConfigLoader loads Python-native workspace.py/aquilia.py and explicitly rejects YAML.",
        "aquilia/config.py",
        ("YAML configuration is no longer supported",),
    ),
    (
        "manifest.module_internals",
        "AppManifest declares module controllers, services, models, middleware, sockets, tasks, imports, and exports.",
        "aquilia/manifest.py",
        ("class AppManifest", "controllers", "services", "socket_controllers"),
    ),
    (
        "routing.workspace_prefix",
        "Workspace Module.route_prefix() is the runtime source of truth for module route prefixes.",
        "aquilia/aquilary/core.py",
        ("workspace prefix", "AppManifest.route_prefix"),
    ),
    (
        "deprecation.module_register_methods",
        "Module.register_* methods are deprecated no-ops; component declarations belong in module manifests.",
        "aquilia/workspace.py",
        ("register_controllers", "deprecated"),
    ),
    (
        "deprecation.manifest_database",
        "Manifest-level database config is deprecated and ignored at runtime.",
        "aquilia/manifest.py",
        ("AppManifest.database", "ignored at runtime"),
    ),
    (
        "request.lifecycle",
        "ASGIAdapter handles HTTP, WebSocket, and lifespan scopes and dispatches matched controller routes.",
        "aquilia/asgi.py",
        ("handle_http", "handle_websocket", "handle_lifespan"),
    ),
    (
        "server.middleware_stack",
        "AquiliaServer always wires FaultMiddleware and request-scope middleware before user and subsystem middleware.",
        "aquilia/server.py",
        ("FaultMiddleware", "request_scope_mw", "get_middleware_config"),
    ),
    (
        "server.subsystems",
        "AquiliaServer initializes versioning, mail, cache, storage, i18n, tasks, error tracking, security middleware, and sockets from workspace config.",
        "aquilia/server.py",
        ("_setup_versioning", "_setup_mail", "_setup_cache", "_setup_storage", "_setup_i18n", "_setup_tasks"),
    ),
    (
        "server.startup",
        "AquiliaServer.startup performs autodiscovery, loads controllers and sockets, wires admin/docs routes, registers models, runs lifecycle hooks, starts subsystems, and records health.",
        "aquilia/server.py",
        ("startup", "perform_autodiscovery", "_load_controllers"),
    ),
    (
        "cli.click_tree",
        "The aq CLI is a Click command tree mounted from aquilia.cli.__main__ and external command groups added with cli.add_command.",
        "aquilia/cli/__main__.py",
        ("@click.group", "cli.add_command", "mcp_group"),
    ),
    (
        "config.env_precedence",
        "ConfigLoader merges workspace Python config, legacy config/env.py, dotenv, AQ_ environment overlays, and explicit overrides.",
        "aquilia/config.py",
        ("_load_python_config", "_load_pyconfig_file", "_load_from_env", "overrides"),
    ),
    (
        "pyconfig.env_secret",
        "AquilaConfig supports Env and Secret bindings for Python-native environment configuration.",
        "aquilia/pyconfig.py",
        ("class Env", "class Secret", "class AquilaConfig"),
    ),
    (
        "controller.decorators",
        "HTTP controllers are declared with Controller subclasses and @GET/@POST/@PUT/@PATCH/@DELETE decorators.",
        "aquilia/controller/decorators.py",
        ("class RouteDecorator", "def GET", "def POST"),
    ),
    (
        "di.providers",
        "Aquilia DI uses scoped containers and providers such as ValueProvider, ClassProvider, and FactoryProvider.",
        "aquilia/di/providers.py",
        ("class ValueProvider", "class ClassProvider", "class FactoryProvider"),
    ),
    (
        "faults.structured",
        "Framework-domain failures are represented by structured Fault objects with code, domain, severity, retryability, public exposure, and metadata.",
        "aquilia/faults/core.py",
        ("class Fault", "FaultDomain", "Severity"),
    ),
    (
        "examples.manifest_first",
        "Runnable examples use workspace.py for orchestration and module manifest.py files for controllers/services/models/sockets/tasks.",
        "examples/README.md",
        ("workspace.py", "modules/<name>/manifest.py", "runtime.py"),
    ),
    (
        "mcp.read_only",
        "Aquilia MCP is designed as a local read-only source-backed server with no arbitrary shell execution tools.",
        "aquilia/mcp/security.py",
        ("resolve_under_root", "redact_secrets"),
    ),
]


def derive_facts(sources: list[SourceFile]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    by_path = {source.path: source for source in sources}
    facts: list[dict[str, object]] = []
    deprecations: list[dict[str, object]] = []
    for fact_id, summary, path, markers in _FACT_SPECS:
        source = by_path.get(path)
        if not source:
            continue
        text = source.text
        symbol_text = " ".join(source.symbols)
        searchable = f"{text}\n{symbol_text}"
        if all(marker in searchable for marker in markers):
            line = 1
            first_marker = markers[0]
            for idx, source_line in enumerate(text.splitlines(), start=1):
                if first_marker in source_line:
                    line = idx
                    break
            else:
                for anchor in source.anchors:
                    if anchor.name == first_marker:
                        line = anchor.line
                        break
            item = {"id": fact_id, "summary": summary, "path": path, "line": line}
            facts.append(item)
            if fact_id.startswith("deprecation."):
                deprecations.append(item)
    return facts, deprecations
