"""
Regression tests for the discovery/manifest-sync "stale path" bug.

Previously, restructuring a module file into a package (e.g. turning
modules/auth/models.py into modules/auth/models/register.py) permanently
broke `aq discover`/workspace validation:

  - ManifestDiffer._is_declared() treated any existing manifest ref with a
    matching class name -- regardless of its dotted path -- as "already
    declared", so the newly-discovered correct path never generated an
    "add" SyncAction and the stale entry was never rewritten.
  - FileScanner.scan_module()'s `patterns` filter only matched a file's
    bare stem, so a pattern like "models" never matched the nested
    models/register.py (stem "register"), even though the scan itself
    (rglob) already found the file.
"""

from __future__ import annotations

from pathlib import Path

from aquilia.discovery.engine import ClassifiedComponent, ComponentKind, FileScanner, ManifestDiffer, ManifestWriter


def _component(name: str, import_path: str) -> ClassifiedComponent:
    return ClassifiedComponent(
        name=name,
        kind=ComponentKind.MODEL,
        file_path=Path(import_path.split(":", 1)[0].replace(".", "/") + ".py"),
        line=1,
        import_path=import_path,
    )


class TestManifestDifferDetectsRenamedComponent:
    def test_moved_class_produces_add_action_not_declared_as_duplicate(self):
        differ = ManifestDiffer(root_package="modules")
        discovered = [_component("UsersModel", "modules.auth.models.register:UsersModel")]
        manifest_refs = {"models": ["modules.auth.models:UsersModel"]}

        actions = differ.diff(discovered, manifest_refs, module_prefix="modules.auth")

        add_actions = [a for a in actions if a.action == "add"]
        remove_actions = [a for a in actions if a.action == "remove"]
        assert len(add_actions) == 1
        assert add_actions[0].component.import_path == "modules.auth.models.register:UsersModel"
        # The old stale ref is rewritten in place by ManifestWriter (via its
        # class-name match), not deleted separately -- no "remove" action.
        assert remove_actions == []

    def test_writer_rewrites_stale_ref_in_place(self):
        differ = ManifestDiffer(root_package="modules")
        discovered = [_component("UsersModel", "modules.auth.models.register:UsersModel")]
        manifest_refs = {"models": ["modules.auth.models:UsersModel"]}
        actions = differ.diff(discovered, manifest_refs, module_prefix="modules.auth")

        source = 'models=[\n        "modules.auth.models:UsersModel",\n    ],\n'
        writer = ManifestWriter()
        new_source = writer._add_component(source, "models", actions[0].component.import_path)

        assert "modules.auth.models:UsersModel" not in new_source
        assert '"modules.auth.models.register:UsersModel"' in new_source
        # Rewritten in place, not appended as a second entry.
        assert new_source.count("UsersModel") == 1

    def test_truly_deleted_class_still_produces_remove_action(self):
        differ = ManifestDiffer(root_package="modules")
        discovered: list[ClassifiedComponent] = []
        manifest_refs = {"models": ["modules.auth.models:DeletedModel"]}

        actions = differ.diff(discovered, manifest_refs, module_prefix="modules.auth")

        assert len(actions) == 1
        assert actions[0].action == "remove"
        assert actions[0].component.name == "DeletedModel"


class TestFileScannerMatchesDirectoryPatterns:
    def test_pattern_matches_file_nested_under_matching_directory(self, tmp_path):
        module_dir = tmp_path / "auth"
        models_dir = module_dir / "models"
        models_dir.mkdir(parents=True)
        (models_dir / "__init__.py").write_text("")
        (models_dir / "register.py").write_text("")
        (module_dir / "controllers.py").write_text("")

        scanner = FileScanner(tmp_path)
        found = scanner.scan_module("auth", patterns=["models"])

        found_names = {f.name for f in found}
        assert "register.py" in found_names
        assert "controllers.py" not in found_names
