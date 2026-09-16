"""Shared workspace/manifest scanning helpers.

Single source of truth for the three operations every manifest-aware CLI
command needs:

  1. Extracting the registered module names from a workspace file.
  2. Loading the ``AppManifest`` instance from a module's manifest.py.
  3. Resolving the component references a manifest declares.

``aq run`` previously regex-scraped quoted colon-strings out of the manifest
*text* and resolved them as file paths relative to the module's own
directory, which falsely errored on framework references
(``aquilia.auth.guards:AuthGuard``) and cross-module references and crashed
on multi-colon strings (``redis://localhost:6379``) (audit F-MAN-01/02/03).
``aq doctor`` and ``aq validate`` each carried their own slightly different
copy of the correct logic.  These helpers consolidate all of it so the
commands cannot drift apart again, and unify module-name scraping to accept
both quote styles (audit N-7).
"""

from __future__ import annotations

import importlib
import importlib.util
import re
import sys
from pathlib import Path
from typing import Any

__all__ = [
    "REF_FIELDS",
    "collect_component_refs",
    "extract_registered_modules",
    "load_manifest_object",
    "ref_to_str",
    "resolve_component_ref",
    "strip_comment_lines",
    "validate_component_refs",
]

# Matches Module("name" ...) and Module('name' ...) -- both quote styles, so
# a single-quoted workspace cannot bypass validation (N-7).
_MODULE_NAME_RE = re.compile(r'Module\(\s*["\']([^"\']+)["\']')

# Manifest fields that declare component references.
REF_FIELDS: tuple[str, ...] = (
    "controllers",
    "services",
    "socket_controllers",
    "models",
    "vector_models",
    "serializers",
    "guards",
    "pipes",
    "interceptors",
    "middleware",
    "socket_middleware",
)


def strip_comment_lines(content: str) -> str:
    """Drop whole-line comments.

    Scaffold templates ship with commented-out ``Module(...)`` examples; a
    scraper that does not strip comments counts them as registered modules
    (audit N-8).
    """
    return "\n".join(line for line in content.splitlines() if not line.strip().startswith("#"))


def extract_registered_modules(content: str) -> list[str]:
    """Extract registered module names from workspace file content.

    Comment lines are stripped first, both quote styles are accepted, and
    the result is deduplicated while preserving declaration order.
    """
    names = _MODULE_NAME_RE.findall(strip_comment_lines(content))
    seen: set[str] = set()
    unique: list[str] = []
    for name in names:
        if name not in seen:
            seen.add(name)
            unique.append(name)
    return unique


def load_manifest_object(module_name: str, manifest_path: Path) -> Any | None:
    """Safely load an AppManifest instance from a manifest.py file.

    Imports the file (so programmatically-built manifests are seen exactly
    as the server sees them), then looks for a module-level ``manifest``
    attribute, any ``AppManifest`` instance, or any ``AppManifest`` subclass
    (instantiated).

    Raises:
        ImportError: if the spec cannot be created or the module cannot be
            executed -- the caller decides whether that is fatal.
    """
    spec = importlib.util.spec_from_file_location(f"_aq_manifest_{module_name}", manifest_path)
    if not spec or not spec.loader:
        raise ImportError(f"Could not create import spec for {manifest_path}")

    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)

    manifest_obj = getattr(mod, "manifest", None)
    if manifest_obj is not None:
        return manifest_obj

    from aquilia.manifest import AppManifest

    for _attr, obj in vars(mod).items():
        if isinstance(obj, AppManifest):
            return obj
        if isinstance(obj, type) and issubclass(obj, AppManifest) and obj is not AppManifest:
            return obj()
    return None


def ref_to_str(ref: Any) -> str:
    """Convert any component reference (str, ComponentRef, ServiceConfig,
    MiddlewareConfig, ...) to its class-path string."""
    if isinstance(ref, str):
        return ref
    class_path = getattr(ref, "class_path", None)
    if isinstance(class_path, str):
        return class_path
    return str(ref)


def collect_component_refs(manifest_obj: Any) -> dict[str, list[str]]:
    """Collect the component references a manifest declares, by field name."""
    refs: dict[str, list[str]] = {}
    for field_name in REF_FIELDS:
        values = getattr(manifest_obj, field_name, None) or []
        paths = [ref_to_str(v) for v in values]
        if paths:
            refs[field_name] = paths
    return refs


def resolve_component_ref(ref: str) -> tuple[Any | None, str | None]:
    """Resolve a component reference via importlib.

    Accepts both the colon form (``module.path:Class``) and the dotted form
    (``module.path.Class``), mirroring the server's runtime reference
    resolution.  Multi-colon strings (``redis://localhost:6379``) resolve
    via ``split(":", 1)`` and simply fail to import rather than crash.

    Returns:
        ``(resolved, None)`` on success, ``(None, reason)`` on failure.
    """
    if ":" in ref:
        module_path, attr = ref.split(":", 1)
    elif "." in ref:
        module_path, attr = ref.rsplit(".", 1)
    else:
        return None, "reference must be a dotted path ('module.Class' or 'module:Class')"

    try:
        module = importlib.import_module(module_path)
    except Exception as exc:  # ImportError plus anything the module exec raises
        return None, f"cannot import '{module_path}' ({exc})"

    resolved = getattr(module, attr, None)
    if resolved is None:
        return None, f"'{attr}' not found in '{module_path}'"
    return resolved, None


def validate_component_refs(manifest_obj: Any, *, module_name: str) -> tuple[list[str], list[str]]:
    """Validate every component reference declared on a manifest.

    Hard errors are raised only for references under the workspace's own
    ``modules.*`` package that fail to resolve -- that is this workspace's
    own code.  References to anything else (framework classes such as
    ``aquilia.auth.guards:AuthGuard``, third-party packages) that fail to
    resolve become warnings: they usually mean an optional dependency is
    simply not installed in this environment.

    Returns:
        ``(errors, warnings)`` message lists.
    """
    errors: list[str] = []
    warnings: list[str] = []

    for field_name, refs in collect_component_refs(manifest_obj).items():
        for ref in refs:
            if not isinstance(ref, str) or (":" not in ref and "." not in ref):
                continue  # non-path declarations (classes/instances) are fine
            _resolved, reason = resolve_component_ref(ref)
            if reason is None:
                continue
            if ref.startswith("modules."):
                errors.append(f"Import error in {module_name} ({field_name}): {ref} -- {reason}")
            else:
                warnings.append(f"{module_name}.{field_name}: {ref} could not be resolved ({reason})")

    return errors, warnings
