"""
aquilia.devplatform.reload.analyzer — Dependency graph diff engine.

Maps changed filesystem paths to Python module names, classifies each
module by its Aquilia stability tier, traces reverse dependencies, and
computes the optimal reload strategy (full / partial / hot-patch).

Stability tiers:
  Tier 1 (CORE)      — aquilary/, di/, patterns/     → Full reload (too risky to partial)
  Tier 2 (FRAMEWORK)  — routing/, db/, middleware.py   → Partial reload of dependents
  Tier 3 (APP)        — controller/, models/, auth/    → Partial reload (safe)
  Tier 4 (LEAF)        — debug/, testing/               → Hot-patch when possible

For files inside the workspace's ``modules/`` tree, component-kind
classification is delegated to ``aquilia.discovery.engine.AutoDiscoveryEngine``
(AST-based, mtime+hash incrementally cached to ``.aquilia/discovery_cache.surp``)
instead of re-implementing discovery here. This tells us precisely *what*
changed (a controller added, a service removed, ...) rather than just
*that* a file under a given path prefix changed.
"""

from __future__ import annotations

import ast
import importlib.util
import logging
import os
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from aquilia.devplatform.core._cache import BoundedCache
from aquilia.devplatform.faults import ConfigurationFault

logger = logging.getLogger("aquilia.devplatform.reload.analyzer")


class ReloadStrategy(str, Enum):
    NOOP = "noop"  # Nothing reloadable changed — do nothing
    FULL = "full"  # Restart the Python process
    PARTIAL = "partial"  # importlib.reload() on affected modules + deps
    HOT_PATCH = "hot_patch"  # Bytecode swap only (--hot-patch mode)


class StabilityTier(int, Enum):
    CORE = 1
    FRAMEWORK = 2
    APP = 3
    LEAF = 4


# Module path fragments mapped to stability tiers
_TIER_MAP: list[tuple[str, StabilityTier]] = [
    ("aquilary", StabilityTier.CORE),
    ("/di/", StabilityTier.CORE),
    ("patterns", StabilityTier.CORE),
    ("/db/", StabilityTier.FRAMEWORK),
    ("routing", StabilityTier.FRAMEWORK),
    ("middleware", StabilityTier.FRAMEWORK),
    ("controller", StabilityTier.APP),
    ("models", StabilityTier.APP),
    ("auth", StabilityTier.APP),
    ("sessions", StabilityTier.APP),
    ("debug", StabilityTier.LEAF),
    ("testing", StabilityTier.LEAF),
    ("devplatform", StabilityTier.LEAF),
]


def _classify_tier(module_name: str) -> StabilityTier:
    """Return stability tier for a module name."""
    for fragment, tier in _TIER_MAP:
        if fragment in module_name:
            return tier
    return StabilityTier.APP  # default to app tier


@dataclass
class ReloadPlan:
    """Computed reload plan for a set of changed files."""

    strategy: ReloadStrategy
    changed_modules: list[str] = field(default_factory=list)
    affected_modules: list[str] = field(default_factory=list)
    preserve_resources: list[str] = field(default_factory=list)
    reason: str = ""
    discovery_summary: str = ""


def _path_to_module_name(path: Path) -> str | None:
    """Convert a filesystem path to a Python module name by scanning sys.path."""
    path = path.resolve()
    path_str = str(path)

    # Strip .py suffix
    if path_str.endswith(".py"):
        path_str = path_str[:-3]
    else:
        return None

    for sys_path in sys.path:
        if not sys_path:
            continue
        prefix = sys_path.rstrip("/") + "/"
        if path_str.startswith(prefix):
            rel = path_str[len(prefix) :]
            return rel.replace("/", ".").replace("\\", ".")

    return None


# Per-process memo of a loaded module's static import targets, keyed by
# (file path, mtime) so an unchanged dependent isn't re-parsed every reload.
# Bounded so a long dev session doesn't grow this unboundedly across many
# reload cycles touching many distinct files.
_import_cache: BoundedCache[tuple[str, float], set[str]] = BoundedCache(max_size=2048)


def _static_import_targets(file_path: str, package: str | None) -> set[str]:
    """
    Return the set of fully-qualified dotted module names a file statically
    imports, with relative imports resolved against ``package`` (the
    importing module's ``__package__``).

    Only exact, fully-resolved module names go in — a bare ``import aquilia``
    is recorded as exactly ``"aquilia"``, never as a prefix match for every
    ``aquilia.*`` submodule, since importing a package doesn't guarantee its
    submodules are loaded/referenced.
    """
    try:
        mtime = os.stat(file_path).st_mtime
    except OSError:
        return set()

    cache_key = (file_path, mtime)
    cached = _import_cache.get(cache_key)
    if cached is not None:
        return cached

    targets: set[str] = set()
    try:
        source = Path(file_path).read_text(encoding="utf-8")
        tree = ast.parse(source, filename=file_path)
    except (SyntaxError, UnicodeDecodeError, OSError):
        _import_cache.set(cache_key, targets)
        return targets

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                targets.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                # Relative import — resolve against the importing module's package.
                if not package:
                    continue
                try:
                    base = importlib.util.resolve_name("." * node.level + (node.module or ""), package)
                except (ImportError, ValueError):
                    continue
            else:
                base = node.module
            if not base:
                continue
            targets.add(base)
            # `from pkg import name` may import a submodule `pkg.name` (statically
            # indistinguishable from importing an attribute) — record both as
            # candidate targets. Over-approximating here only widens partial
            # reload's dependent set, never causes an unrelated match.
            for alias in node.names:
                if alias.name != "*":
                    targets.add(f"{base}.{alias.name}")

    _import_cache.set(cache_key, targets)
    return targets


def _get_reverse_deps(module_name: str) -> list[str]:
    """
    Return loaded modules whose source statically imports the given module.

    Uses AST-parsed, fully-resolved import targets rather than object-identity
    scanning of ``__dict__`` — the latter only matches if some attribute's
    *value* happens to equal the module name string, which is not how imports
    are represented and misses essentially all real dependents.
    """
    reverse_deps: list[str] = []
    for loaded_name, mod in list(sys.modules.items()):
        if mod is None or loaded_name == module_name:
            continue
        file_path = getattr(mod, "__file__", None)
        if not file_path:
            continue
        package = getattr(mod, "__package__", None)
        targets = _static_import_targets(file_path, package)
        if module_name in targets:
            reverse_deps.append(loaded_name)
    return reverse_deps


def _resolve_workspace_root() -> Path | None:
    """
    Resolve the workspace root from ``AQUILIA_WORKSPACE``, if set.

    Validates the path is absolute and an existing directory before trusting
    it — an unset/blank env var is not an error (returns ``None``, workspace
    discovery is simply skipped), but a *set-and-wrong* value raises
    ``ConfigurationFault`` rather than silently falling through.
    """
    ws = os.environ.get("AQUILIA_WORKSPACE", "").strip()
    if not ws:
        return None
    candidate = Path(ws)
    if not candidate.is_absolute():
        raise ConfigurationFault(f"AQUILIA_WORKSPACE must be an absolute path, got {ws!r}")
    if not candidate.is_dir():
        raise ConfigurationFault(f"AQUILIA_WORKSPACE does not point to an existing directory: {ws!r}")
    return candidate


class DependencyGraphAnalyzer:
    """
    Analyzes which files changed and produces a ReloadPlan.

    When a workspace root is available, changed files under ``modules/``
    are classified via ``AutoDiscoveryEngine`` so the plan can name exactly
    which controllers/services/models changed instead of only a path tier.
    """

    def __init__(self, workspace_root: Path | None = None) -> None:
        self.workspace_root = workspace_root or _resolve_workspace_root()
        self._engine: Any = None
        if self.workspace_root is not None:
            modules_dir = self.workspace_root / "modules"
            if modules_dir.is_dir():
                try:
                    from aquilia.discovery.engine import AutoDiscoveryEngine

                    self._engine = AutoDiscoveryEngine(modules_dir)
                except Exception as exc:
                    logger.debug("AutoDiscoveryEngine unavailable: %s", exc)

    def compute_strategy(self, changed_paths: set[Path]) -> ReloadPlan:
        """
        Given a set of changed paths, return the optimal ReloadPlan.
        """
        changed_modules: list[str] = []
        max_tier = StabilityTier.LEAF

        # Only .py files can produce a module-level reload. If nothing that
        # changed is Python source, there is nothing to reload — never fall
        # through to a blind FULL restart (the historical false-reload cause).
        py_paths = [p for p in changed_paths if p.suffix == ".py"]
        if not py_paths:
            return ReloadPlan(
                strategy=ReloadStrategy.NOOP,
                reason="No Python source changed — skipping reload",
            )

        for path in py_paths:
            mod_name = _path_to_module_name(path)
            if mod_name and mod_name in sys.modules:
                changed_modules.append(mod_name)
                tier = _classify_tier(mod_name)
                if tier < max_tier:
                    max_tier = tier

        if not changed_modules:
            # New .py files not yet imported — a genuine new module or config
            # change that requires a full restart to pick up.
            return ReloadPlan(
                strategy=ReloadStrategy.FULL,
                reason="New Python source not yet loaded — full reload required",
            )

        if max_tier <= StabilityTier.CORE:
            return ReloadPlan(
                strategy=ReloadStrategy.FULL,
                changed_modules=changed_modules,
                reason="Core stability tier changed — full reload required",
            )

        # Compute affected modules (reverse deps of each changed module)
        affected: set[str] = set(changed_modules)
        for mod_name in changed_modules:
            affected.update(_get_reverse_deps(mod_name))

        # Determine resources to preserve
        preserve = self._identify_resources_to_preserve(affected)

        discovery_summary = self._diff_workspace_changes(changed_paths)

        if max_tier <= StabilityTier.FRAMEWORK:
            strategy = ReloadStrategy.PARTIAL
            reason = "Framework tier changed — partial reload of dependents"
        elif max_tier == StabilityTier.APP:
            strategy = ReloadStrategy.PARTIAL
            reason = discovery_summary or "App tier changed — partial reload"
        else:
            strategy = ReloadStrategy.HOT_PATCH
            reason = "Leaf tier changed — hot-patch eligible"

        return ReloadPlan(
            strategy=strategy,
            changed_modules=changed_modules,
            affected_modules=sorted(affected),
            preserve_resources=preserve,
            reason=reason,
            discovery_summary=discovery_summary,
        )

    def _diff_workspace_changes(self, changed_paths: set[Path]) -> str:
        """
        Best-effort: identify which Aquilia component kinds changed, using
        AutoDiscoveryEngine's incremental AST cache. Returns a human-readable
        summary (empty string if the engine isn't available or nothing under
        modules/ changed).
        """
        if self._engine is None or self.workspace_root is None:
            return ""

        modules_dir = self.workspace_root / "modules"
        changed_module_names: set[str] = set()
        for path in changed_paths:
            try:
                rel = path.resolve().relative_to(modules_dir.resolve())
            except ValueError:
                continue
            if rel.parts:
                changed_module_names.add(rel.parts[0])

        if not changed_module_names:
            return ""

        kind_counts: dict[str, int] = {}
        for module_name in sorted(changed_module_names):
            try:
                result = self._engine.discover(module_name)
            except Exception as exc:
                logger.debug("Discovery diff failed for module %s: %s", module_name, exc)
                continue
            if result.errors:
                logger.debug("Discovery errors in module %s: %s", module_name, result.errors)
            for component in result.components:
                kind_counts[component.kind.value] = kind_counts.get(component.kind.value, 0) + 1

        if not kind_counts:
            return ""

        parts = [f"{count} {kind}" for kind, count in sorted(kind_counts.items())]
        return "Discovery diff: " + ", ".join(parts)

    def _identify_resources_to_preserve(self, affected_modules: set[str]) -> list[str]:
        """Identify long-lived resources that must survive a partial reload."""
        resources = []
        # Always preserve DB pools and session stores
        resources.append("db_connection_pool")
        resources.append("session_store")
        resources.append("cache_backend")
        resources.append("websocket_registry")
        return resources
