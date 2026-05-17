"""explain_bootstrap tool."""

from __future__ import annotations

from ..models import KnowledgeIndex


def explain_bootstrap(index: KnowledgeIndex, arguments: dict) -> dict:
    topic = str(arguments.get("topic") or "runtime")
    facts = [
        fact
        for fact in index.facts
        if topic.lower() in fact["id"].lower()
        or topic.lower() in fact["summary"].lower()
        or topic == "runtime"
    ]
    if not facts:
        facts = index.facts[:8]
    steps = [
        "Aquilia entrypoint resolves AQUILIA_WORKSPACE/AQUILIA_ENV and calls AquiliaRuntime.from_workspace().",
        "AquiliaRuntime.configure() inserts the workspace root into sys.path, sets environment defaults, configures logging, and loads workspace.py through ConfigLoader.",
        "AquiliaRuntime.discover() parses workspace.py, imports modules.<name>.manifest, discovers extra module manifests, rebuilds the apps namespace, and loads workspace Module metadata.",
        "AquiliaRuntime.bootstrap() creates AquiliaServer with manifests, ConfigLoader, RegistryMode, and workspace module route configuration.",
        "AquiliaServer builds Aquilary metadata, RuntimeRegistry, DI containers, middleware, controller compiler/router/engine, sockets, lifecycle coordinator, and subsystem integrations.",
        "ASGIAdapter handles HTTP/WebSocket/lifespan scopes, matches controller routes, creates request-scoped DI, and dispatches through middleware into ControllerEngine.",
    ]
    return {"topic": topic, "steps": steps, "anchors": facts}
