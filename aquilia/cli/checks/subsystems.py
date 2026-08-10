"""Subsystem checks -- the coverage gap Phase 4 closes.

The audit found 13 subsystems (~45k LOC) with zero CLI presence: a workspace
could configure tasks, storage, templates, mail, i18n, cache, sockets, http,
versioning, sse, otel, auth or contracts and ``aq doctor`` would not look at
any of them.

Each check is *config-driven*: it inspects what the workspace actually
declares and stays silent when a subsystem is unused. A workspace that does
not use tasks should not be nagged about tasks.
"""

from __future__ import annotations

import importlib
import importlib.util
from collections.abc import Iterator

from aquilia.cli.checks.base import Finding, register_check
from aquilia.cli.core.context import AqContext
from aquilia.faults.core import Severity

__all__ = [
    "check_subsystem_available",
    "check_tasks",
    "check_templates",
    "check_vectordb_driver",
]


def _integration(ws, name: str):
    """Return a declared integration object by name, or None.

    The workspace's ``_integrations`` dict is authoritative -- it holds exactly
    what ``Workspace.integrate()`` / the builder methods recorded. Attribute
    lookup is only a fallback for non-``Workspace`` objects, and it skips
    callables: ``Workspace`` exposes builder *methods* named ``storage``,
    ``vectordb``, ``i18n`` and ``tasks``, and returning those would make every
    workspace look like it declared them.
    """
    obj = getattr(ws, "workspace_obj", None)
    if obj is None:
        return None

    declared = getattr(obj, "_integrations", None)
    if isinstance(declared, dict):
        found = declared.get(name)
        if found is not None:
            return found

    for attr in (name, f"{name}_integration", f"_{name}"):
        found = getattr(obj, attr, None)
        if found is not None and not callable(found):
            return found
    return None


@register_check(
    "tasks.registry",
    "Declared background tasks resolve",
    tags=["subsystems", "tasks"],
    subsystem="tasks",
)
def check_tasks(ctx: AqContext) -> Iterator[Finding]:
    """Validate declared background tasks import and carry @task metadata."""
    ws = ctx.workspace
    if ws is None:
        return

    for module_name, manifest in ws.manifests().items():
        for raw in getattr(manifest, "tasks", None) or []:
            ref = str(raw)
            location = f"modules/{module_name}/manifest.py"

            if ":" not in ref:
                yield Finding(
                    "AQ_TASK_REF_MALFORMED",
                    f"{module_name}: task reference '{ref}' is not 'module.path:name'",
                    Severity.ERROR,
                    remedy="Use the 'module.path:task_name' form",
                    location=location,
                )
                continue

            mod_path, task_name = ref.rsplit(":", 1)
            try:
                mod = importlib.import_module(mod_path)
            except Exception as exc:
                yield Finding(
                    "AQ_TASK_IMPORT_FAILED",
                    f"{module_name}: cannot import task module '{mod_path}': {exc}",
                    Severity.ERROR,
                    remedy="Fix the import or correct the task reference",
                    location=location,
                )
                continue

            fn = getattr(mod, task_name, None)
            if fn is None:
                yield Finding(
                    "AQ_TASK_NOT_FOUND",
                    f"{module_name}: task '{task_name}' not found in '{mod_path}'",
                    Severity.ERROR,
                    remedy=f"Define '{task_name}' or remove it from the manifest",
                    location=location,
                )
                continue

            # @task attaches metadata; a bare function listed here never runs.
            if not any(hasattr(fn, a) for a in ("__aq_task__", "_task_meta", "__task__", "task_meta")):
                yield Finding(
                    "AQ_TASK_NOT_DECORATED",
                    f"{module_name}: '{task_name}' is listed as a task but has no @task decorator",
                    Severity.WARN,
                    remedy="Decorate it with @task so the registry can schedule it",
                    location=f"{mod_path.replace('.', '/')}.py",
                )


@register_check(
    "templates.dirs",
    "Template directories exist",
    tags=["subsystems", "templates"],
    subsystem="templates",
)
def check_templates(ctx: AqContext) -> Iterator[Finding]:
    """Check the configured template directory actually exists."""
    ws = ctx.workspace
    if ws is None:
        return

    tmpl = _integration(ws, "templates")
    if tmpl is None:
        return

    for attr in ("directory", "dirs", "search_path", "template_dir"):
        value = getattr(tmpl, attr, None)
        if not value:
            continue
        candidates = [value] if isinstance(value, str) else list(value)
        for cand in candidates:
            if not (ws.root / str(cand)).exists():
                yield Finding(
                    "AQ_TEMPLATE_DIR_MISSING",
                    f"Configured template directory '{cand}' does not exist",
                    Severity.WARN,
                    remedy=f"Create {cand}/ or correct the templates integration",
                    location=str(cand),
                )
        break


# Subsystems needing only an "is it importable when declared" probe.
_SIMPLE_SUBSYSTEMS = (
    ("storage", "aquilia.storage"),
    ("cache", "aquilia.cache"),
    ("mail", "aquilia.mail"),
    ("i18n", "aquilia.i18n"),
    ("otel", "aquilia.otel"),
    ("sse", "aquilia.sse"),
    ("versioning", "aquilia.versioning"),
    ("http", "aquilia.http"),
    ("auth", "aquilia.auth"),
    ("sockets", "aquilia.sockets"),
    ("contracts", "aquilia.contracts"),
    ("mlops", "aquilia.mlops"),
    ("vectordb", "aquilia.vectordb"),
    ("admin", "aquilia.admin"),
)


@register_check(
    "subsystems.available",
    "Configured subsystems are installed",
    tags=["subsystems"],
    subsystem="core",
)
def check_subsystem_available(ctx: AqContext) -> Iterator[Finding]:
    """For every declared subsystem, confirm its package imports.

    Catches a workspace declaring an integration the installed Aquilia build
    does not ship (missing extra, or a subsystem renamed between versions).
    """
    ws = ctx.workspace
    if ws is None:
        return

    for name, package in _SIMPLE_SUBSYSTEMS:
        if _integration(ws, name) is None:
            continue
        try:
            if importlib.util.find_spec(package) is None:
                raise ModuleNotFoundError(package)
        except Exception as exc:
            yield Finding(
                "AQ_SUBSYSTEM_UNAVAILABLE",
                f"'{name}' is configured but package '{package}' is unavailable: {exc}",
                Severity.ERROR,
                remedy=f"Install the extra providing {package}, or drop the {name} integration",
                location="workspace.py",
            )


@register_check(
    "vectordb.driver",
    "Vector database driver is installed",
    tags=["subsystems", "vectordb"],
    subsystem="vectordb",
)
def check_vectordb_driver(ctx: AqContext) -> Iterator[Finding]:
    """Confirm ``elips`` is importable when the workspace enables vectordb.

    ``aquilia.vectordb`` always ships in-tree, so the generic package check in
    :func:`check_subsystem_available` can never fail for it. The dependency
    that is actually optional is the ``elips`` driver, and a boot with stores
    declared but no driver raises ``VectorNotInstalledFault``.
    """
    ws = ctx.workspace
    if ws is None:
        return

    cfg = _integration(ws, "vectordb")
    if cfg is None:
        return

    enabled = cfg.get("enabled", False) if isinstance(cfg, dict) else getattr(cfg, "enabled", False)
    if not enabled:
        return

    if importlib.util.find_spec("elips") is not None:
        return

    yield Finding(
        "AQ_VECTORDB_DRIVER_MISSING",
        "vectordb is enabled but the 'elips' driver is not installed",
        Severity.ERROR,
        remedy="Install the driver with: pip install 'aquilia[vectordb]'",
        location="workspace.py",
    )
