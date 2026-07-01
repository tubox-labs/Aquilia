"""
CLI command for module discovery inspection, validation, auto-sync, fixing, and cleaning.

Architecture v2: Uses AutoDiscoveryEngine for AST-based component scanning,
workspace validation, caching, and dependency graph generation.
"""

import json
import sys
from pathlib import Path

from aquilia.cli.generators.workspace import WorkspaceGenerator
from aquilia.discovery.engine import AutoDiscoveryEngine

from ..utils.colors import (
    _CHECK,
    _CROSS,
    banner,
    bold,
    dim,
    error,
    info,
    kv,
    section,
    success,
    table,
    warning,
)


class DiscoveryInspector:
    """Inspect, validate, and auto-sync discovered modules."""

    def __init__(self, workspace_name: str, workspace_path: str | None = None):
        self.workspace_name = workspace_name
        self.workspace_path = Path(workspace_path or workspace_name)
        self.generator = WorkspaceGenerator(workspace_name, self.workspace_path)

    def inspect(
        self,
        verbose: bool = False,
        sync: bool = False,
        dry_run: bool = False,
        validate: bool = False,
        fix: bool = False,
        clean: bool = False,
        graph_path: str | None = None,
        as_json: bool = False,
    ) -> None:
        """Run discovery inspection and optionally sync, validate, fix, or clean."""
        discovered = self.generator._discover_modules()
        sorted_names = self.generator._resolve_dependencies(discovered)
        validation = self.generator._validate_modules(discovered)

        # Initialize AutoDiscoveryEngine
        modules_dir = self.workspace_path / "modules"
        engine = AutoDiscoveryEngine(modules_dir)
        workspace_py = self.workspace_path / "workspace.py"

        # Run deep workspace validations
        deep_validation = engine.validate_workspace(workspace_py)

        all_errors = validation["errors"] + deep_validation["errors"]
        all_warnings = validation["warnings"] + deep_validation["warnings"]

        # Handle dependency graph export
        if graph_path:
            self._write_dependency_graph(Path(graph_path), discovered)

        # Handle JSON output
        if as_json:
            import click

            res = {
                "workspace": self.workspace_name,
                "modules": list(discovered.keys()),
                "validation": {
                    "errors": all_errors,
                    "warnings": all_warnings,
                },
                "components": {},
            }
            for mod_name in discovered:
                res["components"][mod_name] = [
                    {"name": c.name, "kind": c.kind.value, "import_path": c.import_path}
                    for c in engine.discover(mod_name).components
                ]
            click.echo(json.dumps(res, indent=2))
            if all_errors:
                sys.exit(1)
            return

        # Display summary report
        self._print_summary(discovered, all_errors, all_warnings, sorted_names)

        if verbose:
            self._print_detailed_info(discovered, sorted_names)

        # Run autodiscovery and sync/fix operations
        self._run_autodiscovery_operations(
            engine,
            sync=sync or fix or clean,
            dry_run=dry_run,
            clean=clean,
            fix=fix,
        )

        if all_errors and (validate or sync or fix or clean):
            sys.exit(1)

    def _write_dependency_graph(self, path: Path, discovered: dict) -> None:
        """Write a Graphviz DOT representation of the module dependency graph."""
        lines = ["digraph G {", "  node [shape=box, style=filled, fillcolor=lightblue];"]
        for mod, data in discovered.items():
            deps = data.get("depends_on", [])
            for dep in deps:
                lines.append(f'  "{mod}" -> "{dep}";')
        lines.append("}")
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("\n".join(lines), encoding="utf-8")
            success(f"  {_CHECK} Dependency graph written to {path}")
        except Exception as e:
            error(f"  {_CROSS} Failed to write dependency graph: {e}")

    def _run_autodiscovery_operations(
        self,
        engine: AutoDiscoveryEngine,
        sync: bool = False,
        dry_run: bool = False,
        clean: bool = False,
        fix: bool = False,
    ) -> None:
        """Run AST-based auto-discovery and sync/fix/clean operations."""
        import click

        modules_dir = self.workspace_path / "modules"
        if not modules_dir.is_dir():
            return

        results = engine.discover_all()
        if not results:
            return

        click.echo()
        section("Auto-Discovery Scan & Synchronization")
        click.echo()

        all_new = []
        all_stale = []
        rows = []

        for module_name, result in sorted(results.items()):
            manifest_path = modules_dir / module_name / "manifest.py"
            if not manifest_path.exists():
                continue
            manifest_refs = engine._parse_manifest_refs(manifest_path)
            module_prefix = f"{engine.differ.root_package}.{module_name}"

            # Check new components
            for comp in result.components:
                field_name = engine.differ.KIND_TO_FIELD.get(comp.kind, "unknown")
                existing = manifest_refs.get(field_name, [])
                is_synced = engine.differ._is_declared(comp, existing)

                status = f"{_CHECK} synced" if is_synced else "NEW"
                rows.append((module_name, comp.kind.value, comp.name, status))
                if not is_synced:
                    all_new.append((module_name, comp))

            # Check stale/deleted components
            for field_name, existing in manifest_refs.items():
                kind = None
                for k, f in engine.differ.KIND_TO_FIELD.items():
                    if f == field_name:
                        kind = k
                        break
                if kind is None:
                    continue

                discovered_kind = [c for c in result.components if c.kind == kind]
                discovered_paths = {c.import_path for c in discovered_kind}

                for ref in existing:
                    if ref.startswith(f"{module_prefix}."):
                        if ref not in discovered_paths:
                            class_name = ref.split(":", 1)[1] if ":" in ref else ref
                            is_moved = any(c.name == class_name for c in discovered_kind)
                            if not is_moved:
                                rows.append((module_name, kind.value, class_name, "DELETED"))
                                all_stale.append((module_name, ref))

        if rows:
            table(
                headers=["Module", "Kind", "Component", "Status"],
                rows=rows,
                col_widths=[15, 15, 30, 12],
            )
            click.echo()

        if all_new or all_stale:
            if all_new:
                info(f"  Found {len(all_new)} new component(s).")
            if all_stale:
                warning(f"  Found {len(all_stale)} stale/deleted component(s).")

            if sync:
                if dry_run:
                    info("  Dry run -- no files modified.")

                reports = engine.sync_all(dry_run=dry_run)
                for report in reports:
                    if report.has_changes:
                        action_str = "would add" if dry_run else "added"
                        for action in report.added:
                            success(f"  {_CHECK} {report.manifest_path.name} -- {action_str} {action.component.name}")
                        remove_action_str = "would remove" if dry_run else "removed"
                        for action in report.removed:
                            warning(
                                f"  {_CHECK} {report.manifest_path.name} -- {remove_action_str} {action.component.name}"
                            )

                if not dry_run:
                    # Sync workspace.py configurations as well
                    workspace_py_path = self.workspace_path / "workspace.py"
                    if workspace_py_path.exists():
                        discovered = self.generator._discover_modules()
                        self.generator.update_workspace_config(workspace_py_path, discovered)
                    success(f"\n  {_CHECK} Manifests and workspace synced successfully.")
            else:
                dim("  Run `aq discover --sync` to update manifests and workspace.")
        else:
            success(f"  {_CHECK} All components synced -- manifests up to date.")

    def _print_summary(self, discovered: dict, errors: list, warnings: list, sorted_names: list) -> None:
        """Print summary of discovered modules."""
        banner("Module Discovery Report")
        kv("Workspace", self.workspace_name)
        kv("Path", str(self.workspace_path))
        kv("Modules Found", str(len(discovered)))

        import click

        click.echo()
        table(
            headers=["Module", "Version", "Route"],
            rows=[
                (
                    mod_name,
                    discovered[mod_name].get("version", "0.1.0"),
                    discovered[mod_name].get("route_prefix", f"/{mod_name}"),
                )
                for mod_name in sorted_names
                if mod_name in discovered
            ],
            col_widths=[20, 12, 20],
        )
        click.echo()

        # Validation results
        if warnings:
            warning(f"  Warnings ({len(warnings)}):")
            for w in warnings:
                dim(f"    - {w}")

        if errors:
            error(f"  {_CROSS} Errors ({len(errors)}):")
            for e in errors:
                dim(f"    - {e}")
        elif not warnings:
            success(f"  {_CHECK} All modules valid - no issues detected")

        click.echo()

    def _print_detailed_info(self, discovered: dict, sorted_names: list) -> None:
        """Print detailed information about each module."""
        import click

        click.echo()
        section("Detailed Module Information")
        click.echo()

        for mod_name in sorted_names:
            if mod_name in discovered:
                mod = discovered[mod_name]
                self._print_module_details(mod)

    def _print_module_details(self, mod: dict) -> None:
        """Print detailed information about a single module."""
        import click

        bold(f"  {mod['name']}")
        kv("Version", mod.get("version", "0.1.0"), key_width=16)
        kv("Description", mod.get("description", ""), key_width=16)
        kv("Route Prefix", mod.get("route_prefix", ""), key_width=16)
        kv("Base Path", str(mod.get("base_path", "")), key_width=16)

        if mod.get("author"):
            kv("Author", mod["author"], key_width=16)

        if mod.get("tags"):
            kv("Tags", ", ".join(mod["tags"]), key_width=16)

        if mod.get("depends_on"):
            kv("Dependencies", ", ".join(mod["depends_on"]), key_width=16)

        structure = []
        if mod.get("has_services"):
            structure.append("services")
        if mod.get("has_controllers"):
            structure.append("controllers")
        if mod.get("has_middleware"):
            structure.append("middleware")

        if structure:
            kv("Components", ", ".join(structure), key_width=16)

        click.echo()
