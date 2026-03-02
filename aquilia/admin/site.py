"""
AquilAdmin — AdminSite (Central Registry).

The AdminSite is the central coordination point for the admin system.
It manages:
- Model registration (explicit + auto-discovered)
- Dashboard data aggregation
- Audit log
- Template rendering integration
- Permission checks

Design: Singleton pattern with lazy initialization.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple, Type, TYPE_CHECKING

if TYPE_CHECKING:
    from aquilia.models.base import Model
    from aquilia.auth.core import Identity

from .options import ModelAdmin
from .permissions import AdminRole, AdminPermission, get_admin_role, has_admin_permission, has_model_permission
from .permissions import update_role_permissions, set_model_permission_override, get_model_permission_overrides
from .audit import AdminAuditLog, ModelBackedAuditLog, AdminAction
from .faults import (
    AdminAuthorizationFault,
    AdminModelNotFoundFault,
    AdminRecordNotFoundFault,
    AdminValidationFault,
)
from aquilia.controller.pagination import PageNumberPagination

logger = logging.getLogger("aquilia.admin.site")


class AdminSite:
    """
    Central admin site — manages all registered models.

    Singleton-safe with a default() class method.
    Multiple AdminSite instances can coexist for multi-tenant scenarios.

    Attributes:
        name: Site identifier (default "admin")
        title: Dashboard title
        header: Header text
        url_prefix: URL prefix (default "/admin")
        login_url: Login page URL
    """

    _default_instance: Optional[AdminSite] = None

    def __init__(
        self,
        name: str = "admin",
        *,
        title: str = "Aquilia Admin",
        header: str = "Aquilia Administration",
        url_prefix: str = "/admin",
        login_url: str = "/admin/login",
    ):
        self.name = name
        self.title = title
        self.header = header
        self.url_prefix = url_prefix.rstrip("/")
        self.login_url = login_url

        # Registry: model_class -> ModelAdmin instance
        self._registry: Dict[Type[Model], ModelAdmin] = {}

        # Audit log — model-backed (persists to DB), falls back to in-memory
        self.audit_log: ModelBackedAuditLog = ModelBackedAuditLog()

        # Initialization state
        self._initialized = False

    @classmethod
    def default(cls) -> AdminSite:
        """Get or create the default AdminSite singleton."""
        if cls._default_instance is None:
            cls._default_instance = cls()
        return cls._default_instance

    @classmethod
    def reset(cls) -> None:
        """Reset the default site (for testing)."""
        cls._default_instance = None

    def initialize(self) -> None:
        """
        Initialize the admin site.

        Flushes pending registrations and runs autodiscovery.
        Called during app startup.
        """
        if self._initialized:
            return

        from .registry import flush_pending_registrations, autodiscover

        # Flush any @register decorators that fired before init
        flushed = flush_pending_registrations()
        if flushed:
            logger.debug("Flushed %d pending admin registrations", flushed)

        # Auto-discover remaining models
        auto = autodiscover()
        if auto:
            logger.debug("Auto-discovered %d models for admin", len(auto))

        self._initialized = True
        logger.info(
            "AdminSite '%s' initialized with %d models",
            self.name,
            len(self._registry),
        )

    # ── Registration ─────────────────────────────────────────────────

    def register_admin(self, model_cls: Type[Model], admin: ModelAdmin) -> None:
        """Register a model with its ModelAdmin configuration."""
        admin.model = model_cls
        self._registry[model_cls] = admin
        logger.debug("Registered admin for %s", model_cls.__name__)

    def register(self, model_cls: Type[Model], admin_class: Optional[Type[ModelAdmin]] = None) -> None:
        """
        Register a model (convenience method).

        If admin_class is None, uses default ModelAdmin.
        """
        if admin_class is None:
            admin_class = ModelAdmin
        admin = admin_class(model=model_cls)
        self.register_admin(model_cls, admin)

    def unregister(self, model_cls: Type[Model]) -> None:
        """Unregister a model."""
        self._registry.pop(model_cls, None)

    def is_registered(self, model_cls: Type[Model]) -> bool:
        """Check if a model is registered."""
        return model_cls in self._registry

    # ── Registry access ──────────────────────────────────────────────

    def get_model_admin(self, model_cls_or_name: Any) -> ModelAdmin:
        """
        Get ModelAdmin for a model class or name.

        Raises AdminModelNotFoundFault if not found.
        """
        if isinstance(model_cls_or_name, str):
            for cls, admin in self._registry.items():
                if cls.__name__.lower() == model_cls_or_name.lower():
                    return admin
            raise AdminModelNotFoundFault(model_cls_or_name)
        else:
            admin = self._registry.get(model_cls_or_name)
            if admin is None:
                raise AdminModelNotFoundFault(
                    model_cls_or_name.__name__ if hasattr(model_cls_or_name, "__name__") else str(model_cls_or_name)
                )
            return admin

    def get_model_class(self, model_name: str) -> Type[Model]:
        """
        Get model class by name.

        Raises AdminModelNotFoundFault if not found.
        """
        for cls in self._registry:
            if cls.__name__.lower() == model_name.lower():
                return cls
        raise AdminModelNotFoundFault(model_name)

    def get_app_list(self, identity: Optional[Identity] = None) -> List[Dict[str, Any]]:
        """
        Get list of admin apps/models grouped by app_label.

        Filters by identity permissions.
        Returns list of app dicts with their models.
        """
        apps: Dict[str, Dict[str, Any]] = {}

        for model_cls, admin in self._registry.items():
            # Permission check
            if identity and not admin.has_module_permission(identity):
                continue

            app_label = admin.get_app_label()
            if app_label not in apps:
                apps[app_label] = {
                    "app_label": app_label,
                    "app_name": app_label.replace("_", " ").title(),
                    "models": [],
                }

            apps[app_label]["models"].append({
                "name": admin.get_model_name(),
                "name_plural": admin.get_model_name_plural(),
                "model_name": model_cls.__name__,
                "url_name": model_cls.__name__.lower(),
                "icon": admin.icon,
                "perms": {
                    "view": admin.has_view_permission(identity),
                    "add": admin.has_add_permission(identity),
                    "change": admin.has_change_permission(identity),
                    "delete": admin.has_delete_permission(identity),
                },
            })

        return sorted(apps.values(), key=lambda a: a["app_label"])

    def get_registered_models(self) -> Dict[str, ModelAdmin]:
        """Get all registered model name -> ModelAdmin pairs."""
        return {cls.__name__: admin for cls, admin in self._registry.items()}

    # ── Dashboard data ───────────────────────────────────────────────

    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """
        Aggregate dashboard statistics.

        Returns model counts and recent audit entries.
        """
        stats: Dict[str, Any] = {
            "total_models": len(self._registry),
            "model_counts": {},
            "recent_actions": [],
        }

        # Count records per model (best effort)
        for model_cls, admin in self._registry.items():
            try:
                count = await model_cls.objects.count()
                stats["model_counts"][model_cls.__name__] = count
            except Exception:
                stats["model_counts"][model_cls.__name__] = "?"

        # Recent audit entries
        stats["recent_actions"] = [
            e.to_dict() for e in self.audit_log.get_entries(limit=10)
        ]

        return stats

    # ── Build info ───────────────────────────────────────────────────

    def get_build_info(self) -> Dict[str, Any]:
        """
        Gather build information from Crous artifacts in the build directory.

        Scans the workspace build/ directory for .crous files and
        bundle.manifest.json, returning artifact metadata.
        """
        import os

        result: Dict[str, Any] = {
            "info": {},
            "artifacts": [],
            "pipeline_phases": [],
            "build_log": "",
        }

        # Find workspace root — look for build/ directory
        build_dir = self._find_workspace_path("build")
        if build_dir is None or not build_dir.is_dir():
            return result

        # Read bundle manifest if it exists
        manifest_path = build_dir / "bundle.manifest.json"
        if manifest_path.exists():
            try:
                import json
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                result["info"] = {
                    "workspace_name": manifest.get("workspace_name", ""),
                    "workspace_version": manifest.get("workspace_version", ""),
                    "mode": manifest.get("mode", ""),
                    "fingerprint": manifest.get("fingerprint", ""),
                    "total_artifacts": manifest.get("artifact_count", 0),
                    "elapsed_ms": manifest.get("elapsed_ms", 0),
                }
            except Exception:
                pass

        # Scan for .crous files (ignore .aq.json — Crous only)
        for fpath in sorted(build_dir.iterdir()):
            if fpath.suffix == ".crous" and fpath.is_file():
                try:
                    stat = fpath.stat()
                    size_kb = stat.st_size / 1024
                    size_str = f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb/1024:.2f} MB"

                    # Compute SHA-256 digest
                    import hashlib
                    digest = hashlib.sha256(fpath.read_bytes()).hexdigest()

                    # Determine kind from filename
                    name = fpath.stem
                    kind = "bundle" if "bundle" in name else (
                        "routes" if "route" in name else (
                        "di_graph" if "di" in name else (
                        "workspace" if "workspace" in name else "module"
                    )))

                    result["artifacts"].append({
                        "name": fpath.name,
                        "kind": kind,
                        "size": size_str,
                        "digest": digest,
                        "path": str(fpath),
                    })
                except Exception:
                    result["artifacts"].append({
                        "name": fpath.name,
                        "kind": "unknown",
                        "size": "?",
                        "digest": "",
                    })

        result["info"]["total_artifacts"] = len(result["artifacts"])

        # Build pipeline phases (static structure)
        result["pipeline_phases"] = [
            {"name": "Discovery", "status": "success" if result["artifacts"] else "pending",
             "detail": "Scan workspace for modules, controllers, models"},
            {"name": "Validation", "status": "success" if result["artifacts"] else "pending",
             "detail": "Validate manifest and module configuration"},
            {"name": "Static Check", "status": "success" if result["artifacts"] else "pending",
             "detail": "Pre-flight validation of all components"},
            {"name": "Compilation", "status": "success" if result["artifacts"] else "pending",
             "detail": "Compile modules to intermediate artifacts"},
            {"name": "Bundling", "status": "success" if result["artifacts"] else "pending",
             "detail": "Serialize to Crous binary format with dedup"},
            {"name": "Fingerprint", "status": "success" if result["info"].get("fingerprint") else "pending",
             "detail": "Compute content-addressed build fingerprint"},
        ]

        # Read build log if available
        build_log_path = build_dir / "build_output.txt"
        if build_log_path.exists():
            try:
                result["build_log"] = build_log_path.read_text(encoding="utf-8")
            except Exception:
                pass

        # Read artifact contents for the file viewer
        for artifact in result["artifacts"]:
            artifact["content"] = ""
            artifact["content_type"] = "binary"
            fpath_str = artifact.get("path", "")
            if not fpath_str:
                continue
            try:
                from pathlib import Path as _P
                fpath = _P(fpath_str)
                raw = fpath.read_bytes()

                # Try Crous decode first
                try:
                    from aquilia.build.bundler import _CrousBackend
                    backend = _CrousBackend()
                    decoded = backend.decode(raw)
                    import json as _json
                    artifact["content"] = _json.dumps(decoded, indent=2, default=str)
                    artifact["content_type"] = "json"
                    artifact["content_highlighted"] = self._highlight_json(artifact["content"])
                except Exception:
                    # Fallback: try UTF-8 text
                    try:
                        text = raw.decode("utf-8")
                        artifact["content"] = text
                        artifact["content_type"] = "text"
                        # Try to detect if it's JSON
                        text_stripped = text.strip()
                        if text_stripped and text_stripped[0] in ('{', '['):
                            try:
                                import json as _json2
                                _json2.loads(text_stripped)
                                artifact["content_type"] = "json"
                                artifact["content_highlighted"] = self._highlight_json(text)
                            except (ValueError, TypeError):
                                artifact["content_highlighted"] = self._highlight_crous(text)
                        else:
                            artifact["content_highlighted"] = self._highlight_crous(text)
                    except UnicodeDecodeError:
                        # Show hex dump for binary
                        hex_lines = []
                        for offset in range(0, min(len(raw), 2048), 16):
                            chunk = raw[offset:offset + 16]
                            hex_part = " ".join(f"{b:02x}" for b in chunk)
                            ascii_part = "".join(
                                chr(b) if 32 <= b < 127 else "." for b in chunk
                            )
                            hex_lines.append(f"{offset:08x}  {hex_part:<48s}  |{ascii_part}|")
                        if len(raw) > 2048:
                            hex_lines.append(f"... ({len(raw)} bytes total, showing first 2048)")
                        artifact["content"] = "\n".join(hex_lines)
                        artifact["content_type"] = "hex"
            except Exception:
                artifact["content"] = "(unable to read file)"
                artifact["content_type"] = "error"

        # Also scan for other build files (non-.crous)
        result["build_files"] = []
        for fpath in sorted(build_dir.iterdir()):
            if fpath.is_file() and fpath.suffix != ".crous" and fpath.name != "bundle.manifest.json":
                try:
                    content = fpath.read_text(encoding="utf-8")
                    result["build_files"].append({
                        "name": fpath.name,
                        "content": content,
                        "size": f"{fpath.stat().st_size / 1024:.1f} KB",
                    })
                except Exception:
                    pass

        return result

    # ── Migrations data ──────────────────────────────────────────────

    def get_migrations_data(self) -> List[Dict[str, Any]]:
        """
        Scan the migrations directory for migration files and
        return their metadata and syntax-highlighted source.
        """
        import re

        migrations_dir = self._find_workspace_path("migrations")
        if migrations_dir is None or not migrations_dir.is_dir():
            return []

        migrations: List[Dict[str, Any]] = []

        for fpath in sorted(migrations_dir.iterdir()):
            if not fpath.suffix == ".py" or fpath.name.startswith("__"):
                continue

            try:
                source = fpath.read_text(encoding="utf-8")

                # Extract metadata from the migration file
                revision = ""
                models: List[str] = []
                operations_count = 0

                # Parse revision from Meta class
                rev_match = re.search(r'revision\s*=\s*["\']([^"\']+)', source)
                if rev_match:
                    revision = rev_match.group(1)

                # Parse model names from Meta.models list
                models_match = re.search(r'models\s*=\s*\[([^\]]+)\]', source)
                if models_match:
                    models = re.findall(r"'(\w+)'", models_match.group(1))

                # Count operations
                operations_count = len(re.findall(r'(?:CreateModel|CreateIndex|AlterField|AddColumn|DropColumn|RenameField)\(', source))

                # Syntax highlight the source
                highlighted = self._highlight_python(source)

                migrations.append({
                    "filename": fpath.name,
                    "revision": revision,
                    "models": models,
                    "operations_count": operations_count,
                    "source": source,
                    "source_highlighted": highlighted,
                })
            except Exception:
                migrations.append({
                    "filename": fpath.name,
                    "revision": "",
                    "models": [],
                    "operations_count": 0,
                    "source": "",
                })

        return migrations

    # ── Config data ──────────────────────────────────────────────────

    def get_config_data(self) -> Dict[str, Any]:
        """
        Read workspace YAML configuration files and workspace.py.

        Returns file contents for display in the admin config page.
        """
        result: Dict[str, Any] = {
            "files": [],
            "workspace": None,
        }

        config_dir = self._find_workspace_path("config")
        if config_dir and config_dir.is_dir():
            for fname in ["base.yaml", "dev.yaml", "prod.yaml", "test.yaml"]:
                fpath = config_dir / fname
                if fpath.exists():
                    try:
                        content = fpath.read_text(encoding="utf-8")
                        result["files"].append({
                            "name": fname,
                            "path": f"config/{fname}",
                            "content": content,
                            "content_highlighted": self._highlight_yaml(content),
                        })
                    except Exception:
                        pass

        # Read workspace.py for workspace info
        ws_path = self._find_workspace_path("workspace.py", is_file=True)
        if ws_path and ws_path.exists():
            try:
                ws_source = ws_path.read_text(encoding="utf-8")
                import re

                # Extract workspace name
                name_match = re.search(r'(?:Workspace\(\s*["\'](\w+)|name\s*=\s*["\'](\w+))', ws_source)
                ws_name = (name_match.group(1) or name_match.group(2)) if name_match else ""

                # Extract version
                ver_match = re.search(r'version\s*=\s*["\']([^"\']+)', ws_source)
                ws_version = ver_match.group(1) if ver_match else ""

                # Extract modules
                module_matches = re.findall(r'Module\(\s*["\'](\w+)', ws_source)

                # Extract integrations
                intg_matches = re.findall(r'Integration\(\s*["\'](\w+)', ws_source)

                result["workspace"] = {
                    "name": ws_name,
                    "version": ws_version,
                    "modules": module_matches,
                    "integrations": intg_matches,
                }

                # Also add workspace.py as a config file
                result["files"].append({
                    "name": "workspace.py",
                    "path": "workspace.py",
                    "content": ws_source,
                    "content_highlighted": self._highlight_python(ws_source),
                })
            except Exception:
                pass

        return result

    # ── Workspace data ───────────────────────────────────────────────

    def get_workspace_data(self) -> Dict[str, Any]:
        """
        Gather comprehensive workspace data for the admin workspace page.

        Reads workspace.py, discovers all modules and their manifests,
        collects project metadata, registered models, integrations,
        and overall project health/structure information.

        Returns a dict with:
            - workspace: name, version, description, path
            - modules: list of module dicts with manifest data
            - integrations: list of active integrations
            - project_meta: pyproject.toml / setup.py data
            - registered_models: list of all ORM models
            - stats: module counts, model counts, etc.
        """
        import os
        import sys
        from pathlib import Path

        result: Dict[str, Any] = {
            "workspace": None,
            "modules": [],
            "integrations": [],
            "project_meta": {},
            "registered_models": [],
            "stats": {},
        }

        # ── Read workspace.py ────────────────────────────────────────
        ws_path = self._find_workspace_path("workspace.py", is_file=True)
        workspace_root = None
        if ws_path and ws_path.exists():
            workspace_root = ws_path.parent
            try:
                ws_source = ws_path.read_text(encoding="utf-8")
                import re

                name_match = re.search(r'(?:Workspace\(\s*["\'](\w+)|name\s*=\s*["\'](\w+))', ws_source)
                ws_name = (name_match.group(1) or name_match.group(2)) if name_match else "unknown"

                ver_match = re.search(r'version\s*=\s*["\']([^"\']+)', ws_source)
                ws_version = ver_match.group(1) if ver_match else "0.0.0"

                desc_match = re.search(r'description\s*=\s*["\']([^"\']+)', ws_source)
                ws_desc = desc_match.group(1) if desc_match else ""

                # Extract integrations from workspace
                intg_matches = re.findall(r'Integration\.(\w+)', ws_source)
                integrations_list = []
                seen = set()
                for intg in intg_matches:
                    if intg not in seen:
                        seen.add(intg)
                        # Extract inline params for the integration
                        pattern = rf'Integration\.{intg}\((.*?)\)'
                        param_match = re.search(pattern, ws_source, re.DOTALL)
                        params = {}
                        if param_match:
                            param_str = param_match.group(1)
                            for kv in re.findall(r'(\w+)\s*=\s*([^,\)]+)', param_str):
                                params[kv[0]] = kv[1].strip().strip('"\'')
                        integrations_list.append({
                            "name": intg,
                            "display_name": intg.replace("_", " ").title(),
                            "params": params,
                            "icon": self._get_integration_icon(intg),
                        })

                result["workspace"] = {
                    "name": ws_name,
                    "version": ws_version,
                    "description": ws_desc,
                    "path": str(workspace_root),
                    "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                    "platform": sys.platform,
                }
                result["integrations"] = integrations_list

            except Exception as exc:
                logger.debug("Failed to read workspace.py: %s", exc)

        # ── Discover modules ─────────────────────────────────────────
        if workspace_root:
            modules_dir = workspace_root / "modules"
            if modules_dir.is_dir():
                for module_path in sorted(modules_dir.iterdir()):
                    if not module_path.is_dir() or module_path.name.startswith(("_", ".")):
                        continue

                    mod_info: Dict[str, Any] = {
                        "name": module_path.name,
                        "path": str(module_path.relative_to(workspace_root)),
                        "has_manifest": False,
                        "manifest": {},
                        "files": [],
                        "models": [],
                        "controllers": [],
                        "services": [],
                    }

                    # List all files in the module
                    for f in sorted(module_path.iterdir()):
                        if f.is_file() and f.suffix == ".py" and not f.name.startswith("_"):
                            mod_info["files"].append({
                                "name": f.name,
                                "size": f.stat().st_size,
                                "kind": self._classify_module_file(f.name),
                            })
                        elif f.name == "__init__.py":
                            mod_info["files"].append({
                                "name": f.name,
                                "size": f.stat().st_size,
                                "kind": "init",
                            })

                    # Read manifest.py
                    manifest_path = module_path / "manifest.py"
                    if manifest_path.exists():
                        mod_info["has_manifest"] = True
                        try:
                            manifest_source = manifest_path.read_text(encoding="utf-8")
                            import re as _re

                            # Extract manifest fields
                            name_m = _re.search(r'name\s*=\s*["\']([^"\']+)', manifest_source)
                            ver_m = _re.search(r'version\s*=\s*["\']([^"\']+)', manifest_source)
                            desc_m = _re.search(r'description\s*=\s*["\']([^"\']+)', manifest_source)
                            prefix_m = _re.search(r'route_prefix\s*=\s*["\']([^"\']+)', manifest_source)
                            base_m = _re.search(r'base_path\s*=\s*["\']([^"\']+)', manifest_source)

                            # Extract component lists
                            controllers = _re.findall(r'"modules\.[^"]+controllers[^"]*"', manifest_source)
                            services = _re.findall(r'"modules\.[^"]+services[^"]*"', manifest_source)
                            models = _re.findall(r'"modules\.[^"]+models[^"]*"', manifest_source)
                            guards = _re.findall(r'"modules\.[^"]+guards[^"]*"', manifest_source)
                            pipes = _re.findall(r'"modules\.[^"]+pipes[^"]*"', manifest_source)
                            imports = _re.findall(r'imports\s*=\s*\[(.*?)\]', manifest_source, _re.DOTALL)
                            exports = _re.findall(r'exports\s*=\s*\[(.*?)\]', manifest_source, _re.DOTALL)

                            # Tags
                            tags = _re.findall(r'tags\s*=\s*\[(.*?)\]', manifest_source, _re.DOTALL)
                            tag_list = []
                            if tags:
                                tag_list = _re.findall(r'["\']([^"\']+)["\']', tags[0])

                            # Auto-discover
                            auto_disc = _re.search(r'auto_discover\s*=\s*(True|False)', manifest_source)

                            # Fault handling
                            fault_domain = _re.search(r'default_domain\s*=\s*["\']([^"\']+)', manifest_source)
                            fault_strategy = _re.search(r'strategy\s*=\s*["\']([^"\']+)', manifest_source)

                            mod_info["manifest"] = {
                                "name": name_m.group(1) if name_m else module_path.name,
                                "version": ver_m.group(1) if ver_m else "0.0.0",
                                "description": desc_m.group(1) if desc_m else "",
                                "route_prefix": prefix_m.group(1) if prefix_m else "",
                                "base_path": base_m.group(1) if base_m else "",
                                "controllers": [c.strip('"') for c in controllers],
                                "services": [s.strip('"') for s in services],
                                "models": [m.strip('"') for m in models],
                                "guards": [g.strip('"') for g in guards],
                                "pipes": [p.strip('"') for p in pipes],
                                "tags": tag_list,
                                "auto_discover": auto_disc.group(1) == "True" if auto_disc else True,
                                "fault_domain": fault_domain.group(1) if fault_domain else "",
                                "fault_strategy": fault_strategy.group(1) if fault_strategy else "",
                                "source": manifest_source,
                            }
                            mod_info["controllers"] = [c.split(":")[-1].strip('"') for c in controllers]
                            mod_info["services"] = [s.split(":")[-1].strip('"') for s in services]
                            mod_info["models"] = [m.split(":")[-1].strip('"') for m in models]

                        except Exception as exc:
                            logger.debug("Failed to read manifest %s: %s", manifest_path, exc)

                    result["modules"].append(mod_info)

        # ── Project metadata (pyproject.toml) ────────────────────────
        if workspace_root:
            pyproject = workspace_root / "pyproject.toml"
            if not pyproject.exists():
                # Try one directory up (framework root)
                pyproject = workspace_root.parent / "pyproject.toml"

            if pyproject.exists():
                try:
                    content = pyproject.read_text(encoding="utf-8")
                    import re as _re
                    name_m = _re.search(r'name\s*=\s*"([^"]+)"', content)
                    ver_m = _re.search(r'version\s*=\s*"([^"]+)"', content)
                    desc_m = _re.search(r'description\s*=\s*"([^"]+)"', content)
                    py_req = _re.search(r'requires-python\s*=\s*"([^"]+)"', content)
                    license_m = _re.search(r'license\s*=\s*"([^"]+)"', content)

                    result["project_meta"] = {
                        "name": name_m.group(1) if name_m else "",
                        "version": ver_m.group(1) if ver_m else "",
                        "description": desc_m.group(1) if desc_m else "",
                        "python_requires": py_req.group(1) if py_req else "",
                        "license": license_m.group(1) if license_m else "",
                    }
                except Exception:
                    pass

        # ── Registered ORM models ────────────────────────────────────
        for model_cls, admin in self._registry.items():
            result["registered_models"].append({
                "name": model_cls.__name__,
                "table": getattr(model_cls, "table", ""),
                "app_label": admin.get_app_label(),
                "field_count": len(model_cls._fields) if hasattr(model_cls, "_fields") else 0,
                "icon": admin.icon or "📦",
            })

        # ── Stats ────────────────────────────────────────────────────
        result["stats"] = {
            "total_modules": len(result["modules"]),
            "total_models": len(result["registered_models"]),
            "total_integrations": len(result["integrations"]),
            "total_files": sum(len(m.get("files", [])) for m in result["modules"]),
        }

        return result

    @staticmethod
    def _classify_module_file(filename: str) -> str:
        """Classify a Python file by its conventional name."""
        name = filename.replace(".py", "")
        mapping = {
            "controllers": "controller", "controller": "controller",
            "services": "service", "service": "service",
            "models": "model", "model": "model",
            "faults": "fault", "fault": "fault",
            "guards": "guard", "guard": "guard",
            "pipes": "pipe", "pipe": "pipe",
            "interceptors": "interceptor", "interceptor": "interceptor",
            "middleware": "middleware",
            "manifest": "manifest",
            "views": "view", "schemas": "schema", "serializers": "serializer",
        }
        return mapping.get(name, "other")

    @staticmethod
    def _get_integration_icon(name: str) -> str:
        """Get a Lucide icon class for an integration type."""
        icons = {
            "di": "icon-plug",
            "registry": "icon-clipboard-list",
            "routing": "icon-git-branch",
            "fault_handling": "icon-shield",
            "patterns": "icon-puzzle",
            "database": "icon-database",
            "cache": "icon-zap",
            "templates": "icon-file-text",
            "static_files": "icon-folder",
            "admin": "icon-user",
            "cors": "icon-globe",
            "csp": "icon-lock",
            "rate_limit": "icon-clock",
            "mail": "icon-mail",
            "sessions": "icon-key",
            "auth": "icon-shield-check",
            "openapi": "icon-book-open",
        }
        return icons.get(name, "icon-settings")

    # ── Permissions data ─────────────────────────────────────────────

    def get_permissions_data(self, identity: Optional["Identity"] = None) -> Dict[str, Any]:
        """
        Gather permission roles, matrix, and per-model permissions.
        """
        from .permissions import AdminRole, AdminPermission, ROLE_PERMISSIONS

        roles = []
        role_descriptions = {
            AdminRole.SUPERADMIN: "Full access to everything — all admin operations.",
            AdminRole.ADMIN: "Full CRUD on all models, audit log, user management.",
            AdminRole.STAFF: "View and edit access — no delete by default.",
            AdminRole.VIEWER: "Read-only access to admin dashboard and data.",
        }

        for role in AdminRole:
            perms = ROLE_PERMISSIONS.get(role, set())
            roles.append({
                "name": role.value,
                "level": role.level,
                "description": role_descriptions.get(role, ""),
                "permissions": sorted(p.value for p in perms),
            })

        # Sort by level descending (highest first)
        roles.sort(key=lambda r: r["level"], reverse=True)

        all_permissions = sorted(p.value for p in AdminPermission)

        # Model-level permissions for current identity
        model_permissions = []
        for model_cls, admin in self._registry.items():
            model_permissions.append({
                "name": model_cls.__name__,
                "perms": {
                    "view": admin.has_view_permission(identity),
                    "add": admin.has_add_permission(identity),
                    "change": admin.has_change_permission(identity),
                    "delete": admin.has_delete_permission(identity),
                    "export": True,  # Tied to MODEL_EXPORT permission
                },
            })

        return {
            "roles": roles,
            "all_permissions": all_permissions,
            "model_permissions": model_permissions,
        }

    def update_permissions(
        self,
        form_data: Dict[str, Any],
        identity: Optional["Identity"] = None,
    ) -> Dict[str, Any]:
        """
        Update role permissions and/or model permission overrides from
        form POST data.

        Form data expected:
        - Role permissions: keys like "role_<role_name>_<permission_value>" with value "on"
        - Model permissions: keys like "model_<model_name>_<action>" with value "on"
        - update_type: "roles" or "models" to indicate which tab submitted

        Returns dict with status and message.
        """
        from .permissions import (
            AdminRole, AdminPermission, ROLE_PERMISSIONS,
            update_role_permissions as _update_role,
            set_model_permission_override,
        )

        update_type = form_data.get("update_type", "roles")
        changes = 0

        if update_type == "roles":
            # Process role permission matrix
            for role in AdminRole:
                if role == AdminRole.SUPERADMIN:
                    continue  # Can't modify superadmin

                current_perms = ROLE_PERMISSIONS.get(role, set())

                for perm in AdminPermission:
                    key = f"role_{role.value}_{perm.value}"
                    should_have = key in form_data
                    currently_has = perm in current_perms

                    if should_have != currently_has:
                        _update_role(role, perm, granted=should_have)
                        changes += 1

                        # Audit the change
                        self.audit_log.log(
                            user_id=identity.id if identity else "system",
                            username=identity.get_attribute("username", identity.id) if identity else "system",
                            role=str(get_admin_role(identity) or "unknown") if identity else "system",
                            action=AdminAction.PERMISSION_CHANGE,
                            model_name=f"Role:{role.value}",
                            changes={perm.value: {"old": str(currently_has), "new": str(should_have)}},
                        )

        elif update_type == "models":
            # Process model permission overrides
            for model_cls in self._registry:
                model_name = model_cls.__name__
                for action in ["view", "add", "change", "delete", "export"]:
                    key = f"model_{model_name}_{action}"
                    allowed = key in form_data
                    set_model_permission_override(model_name, action, allowed=allowed)
                    changes += 1

            if changes:
                self.audit_log.log(
                    user_id=identity.id if identity else "system",
                    username=identity.get_attribute("username", identity.id) if identity else "system",
                    role=str(get_admin_role(identity) or "unknown") if identity else "system",
                    action=AdminAction.PERMISSION_CHANGE,
                    model_name="ModelPermissions",
                    changes={"type": "model_override_update", "changes_count": changes},
                )

        return {
            "status": "success",
            "message": f"Updated {changes} permission(s) successfully.",
            "changes": changes,
        }

    # ── Helpers ───────────────────────────────────────────────────────

    def _find_workspace_path(self, name: str, is_file: bool = False) -> Optional["Path"]:
        """
        Find a file/directory in the workspace root.

        Tries common workspace locations relative to CWD.
        """
        from pathlib import Path
        import os

        # Check common workspace roots
        candidates = [
            Path(os.getcwd()) / name,
            Path(os.getcwd()) / "myapp" / name,
        ]

        # Also try the workspace root from sys.path hints
        for p in candidates:
            if is_file and p.is_file():
                return p
            if not is_file and p.is_dir():
                return p

        return None

    @staticmethod
    def _highlight_python(source: str) -> str:
        """
        Apply simple syntax highlighting to Python source code.

        Uses CSS classes matching the aqdocx code block theme:
        .kw, .str, .num, .fn, .cls, .cmt, .dec, .op, .var, .prop
        """
        import re
        import html as html_mod

        lines = source.split('\n')
        result_lines = []

        for i, line in enumerate(lines, 1):
            escaped = html_mod.escape(line)

            # Order matters — comments first, then strings, then others
            # Comments
            escaped = re.sub(
                r'(#.*?)$',
                r'<span class="cmt">\1</span>',
                escaped,
            )

            # Strings (triple-quoted and single/double)
            escaped = re.sub(
                r'(&quot;&quot;&quot;.*?&quot;&quot;&quot;|&#x27;&#x27;&#x27;.*?&#x27;&#x27;&#x27;|&quot;[^&]*?&quot;|&#x27;[^&]*?&#x27;)',
                r'<span class="str">\1</span>',
                escaped,
            )

            # Decorators
            escaped = re.sub(
                r'^(\s*)(@\w+)',
                r'\1<span class="dec">\2</span>',
                escaped,
            )

            # Keywords
            keywords = r'\b(def|class|import|from|return|if|elif|else|for|while|with|as|try|except|finally|raise|pass|break|continue|yield|async|await|not|and|or|in|is|None|True|False|self|lambda)\b'
            escaped = re.sub(
                keywords,
                r'<span class="kw">\1</span>',
                escaped,
            )

            # Numbers
            escaped = re.sub(
                r'\b(\d+\.?\d*)\b',
                r'<span class="num">\1</span>',
                escaped,
            )

            # Function calls
            escaped = re.sub(
                r'\b(\w+)(\()',
                r'<span class="fn">\1</span>\2',
                escaped,
            )

            line_num = f'<span class="code-line-num">{i}</span>'
            result_lines.append(f'{line_num}{escaped}')

        return '\n'.join(result_lines)

    @staticmethod
    def _highlight_yaml(source: str) -> str:
        """Apply simple syntax highlighting to YAML source."""
        import re
        import html as html_mod

        lines = source.split('\n')
        result_lines = []

        for i, line in enumerate(lines, 1):
            escaped = html_mod.escape(line)

            # Comments
            escaped = re.sub(
                r'(#.*?)$',
                r'<span class="cmt">\1</span>',
                escaped,
            )

            # Keys (word followed by colon)
            escaped = re.sub(
                r'^(\s*)([\w\-]+)(:)',
                r'\1<span class="kw">\2</span>\3',
                escaped,
            )

            # Strings
            escaped = re.sub(
                r'(&quot;[^&]*?&quot;|&#x27;[^&]*?&#x27;)',
                r'<span class="str">\1</span>',
                escaped,
            )

            # Numbers
            escaped = re.sub(
                r':\s*(\d+\.?\d*)\s*$',
                r': <span class="num">\1</span>',
                escaped,
            )

            # Booleans
            escaped = re.sub(
                r':\s*(true|false|yes|no|null)\s*$',
                r': <span class="kw">\1</span>',
                escaped,
                flags=re.IGNORECASE,
            )

            line_num = f'<span class="code-line-num">{i}</span>'
            result_lines.append(f'{line_num}{escaped}')

        return '\n'.join(result_lines)

    @staticmethod
    def _highlight_json(source: str) -> str:
        """Apply syntax highlighting to JSON source."""
        import re
        import html as html_mod

        lines = source.split('\n')
        result_lines = []

        for i, line in enumerate(lines, 1):
            escaped = html_mod.escape(line)

            # String values (after colon)
            escaped = re.sub(
                r'(&quot;)(.*?)(&quot;)\s*(:)',
                r'<span class="prop">\1\2\3</span>\4',
                escaped,
            )

            # String values (not keys)
            escaped = re.sub(
                r':\s*(&quot;)(.*?)(&quot;)',
                r': <span class="str">\1\2\3</span>',
                escaped,
            )

            # Standalone strings (in arrays)
            escaped = re.sub(
                r'(?<=[\[,\s])(&quot;)(.*?)(&quot;)(?=[,\]\s])',
                r'<span class="str">\1\2\3</span>',
                escaped,
            )

            # Numbers
            escaped = re.sub(
                r'(?<=:\s)(-?\d+\.?\d*(?:[eE][+-]?\d+)?)(?=[,\s\}\]])',
                r'<span class="num">\1</span>',
                escaped,
            )

            # Booleans and null
            escaped = re.sub(
                r'\b(true|false|null)\b',
                r'<span class="kw">\1</span>',
                escaped,
            )

            # Braces and brackets
            escaped = re.sub(
                r'([\{\}\[\]])',
                r'<span class="op">\1</span>',
                escaped,
            )

            line_num = f'<span class="code-line-num">{i}</span>'
            result_lines.append(f'{line_num}{escaped}')

        return '\n'.join(result_lines)

    @staticmethod
    def _highlight_crous(source: str) -> str:
        """Apply syntax highlighting to Crous format data."""
        import re
        import html as html_mod

        lines = source.split('\n')
        result_lines = []

        for i, line in enumerate(lines, 1):
            escaped = html_mod.escape(line)

            # Comments (# or //)
            escaped = re.sub(
                r'(#.*?)$',
                r'<span class="cmt">\1</span>',
                escaped,
            )
            escaped = re.sub(
                r'(//.*?)$',
                r'<span class="cmt">\1</span>',
                escaped,
            )

            # Section headers [SectionName]
            escaped = re.sub(
                r'^(\s*)(\[[\w\.\-]+\])',
                r'\1<span class="cls">\2</span>',
                escaped,
            )

            # Keys (before = or :)
            escaped = re.sub(
                r'^(\s*)([\w\.\-]+)\s*(=|:)',
                r'\1<span class="kw">\2</span> \3',
                escaped,
            )

            # Strings
            escaped = re.sub(
                r'(&quot;[^&]*?&quot;|&#x27;[^&]*?&#x27;)',
                r'<span class="str">\1</span>',
                escaped,
            )

            # Numbers
            escaped = re.sub(
                r'\b(\d+\.?\d*)\b',
                r'<span class="num">\1</span>',
                escaped,
            )

            # Booleans
            escaped = re.sub(
                r'\b(true|false|yes|no|null|none)\b',
                r'<span class="kw">\1</span>',
                escaped,
                flags=re.IGNORECASE,
            )

            # Hex values (common in Crous binary dumps)
            escaped = re.sub(
                r'\b(0x[0-9a-fA-F]+)\b',
                r'<span class="num">\1</span>',
                escaped,
            )

            line_num = f'<span class="code-line-num">{i}</span>'
            result_lines.append(f'{line_num}{escaped}')

        return '\n'.join(result_lines)

    # ── CRUD operations ──────────────────────────────────────────────

    @staticmethod
    def _coerce_form_data(model_cls: type, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Coerce form string values to the correct Python types for ORM fields.

        HTML forms submit everything as strings. This converts:
        - BooleanField: "1", "true", "on" → True; "", "0", "false" → False
        - IntegerField/BigIntegerField/SmallIntegerField: "42" → 42
        - FloatField/DecimalField: "3.14" → 3.14
        - DateTimeField: kept as string (ORM handles parsing)
        - JSON values: attempted parse

        Prevents: "Field 'active': Expected boolean, got str"
        """
        if not hasattr(model_cls, '_fields'):
            return data

        from aquilia.models.fields_module import (
            BooleanField, IntegerField, BigIntegerField, SmallIntegerField,
            FloatField, DecimalField, PositiveIntegerField, PositiveSmallIntegerField,
        )

        coerced = {}
        for field_name, value in data.items():
            if field_name not in model_cls._fields:
                coerced[field_name] = value
                continue

            field = model_cls._fields[field_name]

            if isinstance(field, BooleanField):
                if isinstance(value, str):
                    coerced[field_name] = value.lower() in ("1", "true", "on", "yes")
                elif isinstance(value, (int, float)):
                    coerced[field_name] = bool(value)
                else:
                    coerced[field_name] = bool(value)
            elif isinstance(field, (IntegerField, BigIntegerField, SmallIntegerField,
                                     PositiveIntegerField, PositiveSmallIntegerField)):
                if isinstance(value, str):
                    if value.strip() == "":
                        coerced[field_name] = None if field.null else 0
                    else:
                        try:
                            coerced[field_name] = int(value)
                        except (ValueError, TypeError):
                            coerced[field_name] = value
                else:
                    coerced[field_name] = value
            elif isinstance(field, (FloatField, DecimalField)):
                if isinstance(value, str):
                    if value.strip() == "":
                        coerced[field_name] = None if field.null else 0.0
                    else:
                        try:
                            coerced[field_name] = float(value)
                        except (ValueError, TypeError):
                            coerced[field_name] = value
                else:
                    coerced[field_name] = value
            else:
                coerced[field_name] = value

        return coerced

    async def list_records(
        self,
        model_name: str,
        *,
        page: int = 1,
        per_page: int = 25,
        search: str = "",
        filters: Optional[Dict[str, Any]] = None,
        ordering: Optional[str] = None,
        identity: Optional[Identity] = None,
    ) -> Dict[str, Any]:
        """
        List records for a model with pagination, search, and filtering.

        Uses ``PageNumberPagination`` from ``aquilia.controller.pagination``
        for consistent, framework-standard pagination behaviour.

        Returns dict with records, total count, and pagination info.
        """
        model_cls = self.get_model_class(model_name)
        admin = self.get_model_admin(model_cls)

        # Permission check
        if identity and not admin.has_view_permission(identity):
            raise AdminAuthorizationFault(action="view", resource=model_name)

        # Build queryset
        qs = model_cls.objects.get_queryset()

        # Apply search
        if search and admin.get_search_fields():
            # Build OR search across search fields
            search_q = None
            for field_name in admin.get_search_fields():
                from aquilia.models.query import QNode
                q = QNode(**{f"{field_name}__icontains": search})
                if search_q is None:
                    search_q = q
                else:
                    search_q = search_q | q
            if search_q:
                qs = qs.apply_q(search_q)

        # Apply filters
        if filters:
            qs = qs.filter(**filters)

        # Apply ordering
        if ordering:
            qs = qs.order(ordering)
        else:
            default_ordering = admin.get_ordering()
            if default_ordering:
                qs = qs.order(*default_ordering)

        # ── Paginate via PageNumberPagination ────────────────────────
        paginator = PageNumberPagination(page_size=per_page)

        # Build a lightweight request-like object that PageNumberPagination
        # can extract query params from (it calls _get_current_params which
        # looks for ``request.query_params``).
        _fake_request = type("_R", (), {
            "query_params": {
                paginator.page_param: str(page),
                paginator.page_size_param: str(per_page),
            },
            "scope": {"scheme": "http", "headers": [], "path": f"/admin/{model_name}/"},
        })()

        paginated = await paginator.paginate_queryset(qs, _fake_request)

        total = paginated["count"]
        total_pages = paginated["total_pages"]
        records_raw = paginated["results"]

        # Format records for display
        list_display = admin.get_list_display()
        rows = []
        for record_data in records_raw:
            # paginate_queryset calls to_dict(); we may get dicts or model instances
            if isinstance(record_data, dict):
                row = {"pk": record_data.get("pk") or record_data.get("id")}
                for field_name in list_display:
                    raw_val = record_data.get(field_name)
                    row[field_name] = admin.format_value(field_name, raw_val)
                    row[f"_raw_{field_name}"] = raw_val
            else:
                row = {"pk": record_data.pk}
                for field_name in list_display:
                    value = getattr(record_data, field_name, None)
                    row[field_name] = admin.format_value(field_name, value)
                    row[f"_raw_{field_name}"] = value
            rows.append(row)

        return {
            "rows": rows,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "has_next": paginated["next"] is not None,
            "has_prev": paginated["previous"] is not None,
            "next_url": paginated["next"],
            "previous_url": paginated["previous"],
            "list_display": list_display,
            "list_filter": admin.get_list_filter(),
            "search_fields": admin.get_search_fields(),
            "ordering": ordering,
            "search": search,
            "model_name": model_cls.__name__,
            "verbose_name": admin.get_model_name(),
            "verbose_name_plural": admin.get_model_name_plural(),
        }

    async def get_record(
        self,
        model_name: str,
        pk: Any,
        *,
        identity: Optional[Identity] = None,
    ) -> Dict[str, Any]:
        """
        Get a single record with field metadata for the edit form.
        """
        model_cls = self.get_model_class(model_name)
        admin = self.get_model_admin(model_cls)

        if identity and not admin.has_view_permission(identity):
            raise AdminAuthorizationFault(action="view", resource=model_name)

        record = await model_cls.get(pk=pk)
        if record is None:
            raise AdminRecordNotFoundFault(model_name, str(pk))

        # Build field data
        fields_data = []
        readonly = admin.get_readonly_fields()
        for field_name in admin.get_fields():
            meta = admin.get_field_metadata(field_name)
            meta["value"] = getattr(record, field_name, None)
            meta["readonly"] = field_name in readonly
            fields_data.append(meta)

        # Also include readonly fields that aren't in get_fields
        for field_name in readonly:
            if field_name not in [f["name"] for f in fields_data]:
                meta = admin.get_field_metadata(field_name)
                meta["value"] = getattr(record, field_name, None)
                meta["readonly"] = True
                fields_data.append(meta)

        return {
            "pk": record.pk,
            "record": record,
            "fields": fields_data,
            "fieldsets": admin.get_fieldsets(),
            "model_name": model_cls.__name__,
            "verbose_name": admin.get_model_name(),
            "can_change": admin.has_change_permission(identity),
            "can_delete": admin.has_delete_permission(identity),
        }

    async def create_record(
        self,
        model_name: str,
        data: Dict[str, Any],
        *,
        identity: Optional[Identity] = None,
    ) -> Any:
        """Create a new record."""
        model_cls = self.get_model_class(model_name)
        admin = self.get_model_admin(model_cls)

        if identity and not admin.has_add_permission(identity):
            raise AdminAuthorizationFault(action="add", resource=model_name)

        # Filter to editable fields only
        editable = set(admin.get_fields()) - set(admin.get_readonly_fields())
        clean_data = {k: v for k, v in data.items() if k in editable}

        # Coerce string values from HTML forms to correct Python types
        clean_data = self._coerce_form_data(model_cls, clean_data)

        try:
            record = await model_cls.create(**clean_data)
        except Exception as e:
            raise AdminValidationFault(str(e))

        # Audit log (in-memory + ORM-backed)
        if identity:
            self.audit_log.log(
                user_id=identity.id,
                username=identity.get_attribute("name", identity.id),
                role=str(get_admin_role(identity) or "unknown"),
                action=AdminAction.CREATE,
                model_name=model_name,
                record_pk=str(record.pk),
                changes=clean_data,
            )
            # Persist to AdminLogEntry (database-backed audit trail)
            try:
                from .models import AdminLogEntry, ContentType, _HAS_ORM
                if _HAS_ORM:
                    ct = await ContentType.get_for_model(model_cls)
                    await AdminLogEntry.log_action(
                        user_id=int(identity.id) if identity.id.isdigit() else 1,
                        content_type_id=ct.pk if ct else None,
                        object_id=str(record.pk),
                        object_repr=str(record),
                        action_flag=AdminLogEntry.ADDITION,
                        change_message=str(clean_data),
                    )
            except Exception:
                pass

        return record

    async def update_record(
        self,
        model_name: str,
        pk: Any,
        data: Dict[str, Any],
        *,
        identity: Optional[Identity] = None,
    ) -> Any:
        """Update an existing record."""
        model_cls = self.get_model_class(model_name)
        admin = self.get_model_admin(model_cls)

        if identity and not admin.has_change_permission(identity):
            raise AdminAuthorizationFault(action="change", resource=model_name)

        record = await model_cls.get(pk=pk)
        if record is None:
            raise AdminRecordNotFoundFault(model_name, str(pk))

        # Filter to editable fields and track changes
        editable = set(admin.get_fields()) - set(admin.get_readonly_fields())

        # Coerce string values from HTML forms to correct Python types
        coerced_data = self._coerce_form_data(model_cls, data)

        changes: Dict[str, Dict[str, Any]] = {}
        update_data: Dict[str, Any] = {}

        for field_name, new_value in coerced_data.items():
            if field_name not in editable:
                continue
            old_value = getattr(record, field_name, None)
            if str(old_value) != str(new_value):
                changes[field_name] = {"old": old_value, "new": new_value}
                update_data[field_name] = new_value

        if update_data:
            try:
                await model_cls.objects.filter(**{model_cls._pk_attr: pk}).update(update_data)
                # Refresh record
                record = await model_cls.get(pk=pk)
            except Exception as e:
                raise AdminValidationFault(str(e))

        # Audit log (in-memory + ORM-backed)
        if identity and changes:
            self.audit_log.log(
                user_id=identity.id,
                username=identity.get_attribute("name", identity.id),
                role=str(get_admin_role(identity) or "unknown"),
                action=AdminAction.UPDATE,
                model_name=model_name,
                record_pk=str(pk),
                changes=changes,
            )
            # Persist to AdminLogEntry (database-backed audit trail)
            try:
                from .models import AdminLogEntry, ContentType, _HAS_ORM
                if _HAS_ORM:
                    ct = await ContentType.get_for_model(model_cls)
                    import json as _json
                    change_msg = _json.dumps([
                        {"changed": {"fields": list(changes.keys())}}
                    ], default=str)
                    await AdminLogEntry.log_action(
                        user_id=int(identity.id) if identity.id.isdigit() else 1,
                        content_type_id=ct.pk if ct else None,
                        object_id=str(pk),
                        object_repr=str(record),
                        action_flag=AdminLogEntry.CHANGE,
                        change_message=change_msg,
                    )
            except Exception:
                pass

        return record

    async def delete_record(
        self,
        model_name: str,
        pk: Any,
        *,
        identity: Optional[Identity] = None,
    ) -> bool:
        """Delete a record."""
        model_cls = self.get_model_class(model_name)
        admin = self.get_model_admin(model_cls)

        if identity and not admin.has_delete_permission(identity):
            raise AdminAuthorizationFault(action="delete", resource=model_name)

        record = await model_cls.get(pk=pk)
        if record is None:
            raise AdminRecordNotFoundFault(model_name, str(pk))

        try:
            await model_cls.objects.filter(**{model_cls._pk_attr: pk}).delete()
        except Exception as e:
            raise AdminValidationFault(str(e))

        # Audit log (in-memory + ORM-backed)
        if identity:
            self.audit_log.log(
                user_id=identity.id,
                username=identity.get_attribute("name", identity.id),
                role=str(get_admin_role(identity) or "unknown"),
                action=AdminAction.DELETE,
                model_name=model_name,
                record_pk=str(pk),
            )
            # Persist to AdminLogEntry (database-backed audit trail)
            try:
                from .models import AdminLogEntry, ContentType, _HAS_ORM
                if _HAS_ORM:
                    ct = await ContentType.get_for_model(model_cls)
                    await AdminLogEntry.log_action(
                        user_id=int(identity.id) if identity.id.isdigit() else 1,
                        content_type_id=ct.pk if ct else None,
                        object_id=str(pk),
                        object_repr=f"Deleted {model_name} #{pk}",
                        action_flag=AdminLogEntry.DELETION,
                    )
            except Exception:
                pass

        return True

    async def execute_action(
        self,
        model_name: str,
        action_name: str,
        selected_pks: List[Any],
        *,
        identity: Optional[Identity] = None,
    ) -> str:
        """
        Execute a bulk action on selected records.

        Returns a result message string.
        """
        model_cls = self.get_model_class(model_name)
        admin = self.get_model_admin(model_cls)

        if identity and not has_admin_permission(identity, AdminPermission.ACTION_EXECUTE):
            raise AdminAuthorizationFault(action="execute action", resource=model_name)

        actions = admin.get_actions()
        if action_name not in actions:
            from .faults import AdminActionFault
            raise AdminActionFault(action_name, "Action not found")

        action_desc = actions[action_name]

        # Build queryset for selected records
        qs = model_cls.objects.filter(**{f"{model_cls._pk_attr}__in": selected_pks})

        try:
            result = await action_desc.func(admin, None, qs)
        except Exception as e:
            from .faults import AdminActionFault
            raise AdminActionFault(action_name, str(e))

        # Audit log
        if identity:
            self.audit_log.log(
                user_id=identity.id,
                username=identity.get_attribute("name", identity.id),
                role=str(get_admin_role(identity) or "unknown"),
                action=AdminAction.BULK_ACTION,
                model_name=model_name,
                metadata={"action": action_name, "pks": [str(pk) for pk in selected_pks]},
            )

        return result or f"Action '{action_name}' executed on {len(selected_pks)} record(s)"
