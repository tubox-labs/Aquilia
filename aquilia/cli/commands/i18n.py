"""
AquilaI18n CLI commands — ``aq i18n`` group.

Commands:
    init      Initialize i18n in the current workspace (create locales/ + starter files).
    check     Validate i18n configuration and catalog coverage.
    inspect   Show current i18n configuration as JSON.
    extract   Extract translation keys from source files (Python + Jinja2).
    coverage  Show translation coverage per locale.
"""

from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set

import click


def _load_i18n_config() -> dict:
    """Load i18n config from workspace.py or config files."""
    workspace_path = Path("workspace.py")
    if workspace_path.exists():
        import importlib.util

        spec = importlib.util.spec_from_file_location("workspace", str(workspace_path))
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)  # type: ignore[union-attr]
            if hasattr(mod, "workspace"):
                ws_dict = mod.workspace.to_dict()
                return ws_dict.get("i18n", ws_dict.get("integrations", {}).get("i18n", {}))

    from aquilia.config import ConfigLoader
    config = ConfigLoader()
    return config.get_i18n_config()


def cmd_i18n_init(
    locales: Optional[str] = None,
    directory: str = "locales",
    format: str = "json",
    verbose: bool = False,
) -> None:
    """
    Initialize i18n in the current workspace.

    Creates:
    - ``locales/`` directory
    - Locale subdirectories for each specified locale
    - Starter ``messages.json`` with example translations
    """
    locale_list = [l.strip() for l in (locales or "en").split(",")]
    base_dir = Path(directory)

    click.echo(click.style("Initializing i18n...", fg="cyan", bold=True))
    click.echo(f"  Directory:  {base_dir}")
    click.echo(f"  Locales:    {', '.join(locale_list)}")
    click.echo(f"  Format:     {format}")
    click.echo()

    # Starter translations
    starter_messages: Dict[str, Dict[str, str]] = {
        "en": {
            "welcome": "Welcome to {app_name}!",
            "goodbye": "Goodbye!",
            "greeting": "Hello, {name}!",
            "items_count": {
                "one": "{count} item",
                "other": "{count} items",
            },
            "errors": {
                "not_found": "Page not found",
                "server_error": "Internal server error",
                "unauthorized": "Please sign in to continue",
                "forbidden": "You don't have permission to access this",
            },
        },
        "fr": {
            "welcome": "Bienvenue sur {app_name} !",
            "goodbye": "Au revoir !",
            "greeting": "Bonjour, {name} !",
            "items_count": {
                "one": "{count} élément",
                "other": "{count} éléments",
            },
            "errors": {
                "not_found": "Page non trouvée",
                "server_error": "Erreur interne du serveur",
                "unauthorized": "Veuillez vous connecter pour continuer",
                "forbidden": "Vous n'avez pas la permission d'accéder à ceci",
            },
        },
        "de": {
            "welcome": "Willkommen bei {app_name}!",
            "goodbye": "Auf Wiedersehen!",
            "greeting": "Hallo, {name}!",
            "items_count": {
                "one": "{count} Artikel",
                "other": "{count} Artikel",
            },
            "errors": {
                "not_found": "Seite nicht gefunden",
                "server_error": "Interner Serverfehler",
                "unauthorized": "Bitte melden Sie sich an",
                "forbidden": "Zugriff verweigert",
            },
        },
        "es": {
            "welcome": "¡Bienvenido a {app_name}!",
            "goodbye": "¡Adiós!",
            "greeting": "¡Hola, {name}!",
            "items_count": {
                "one": "{count} elemento",
                "other": "{count} elementos",
            },
            "errors": {
                "not_found": "Página no encontrada",
                "server_error": "Error interno del servidor",
                "unauthorized": "Inicie sesión para continuar",
                "forbidden": "No tiene permiso para acceder",
            },
        },
        "ja": {
            "welcome": "{app_name}へようこそ！",
            "goodbye": "さようなら！",
            "greeting": "こんにちは、{name}さん！",
            "items_count": {
                "other": "{count}個のアイテム",
            },
            "errors": {
                "not_found": "ページが見つかりません",
                "server_error": "内部サーバーエラー",
                "unauthorized": "ログインしてください",
                "forbidden": "アクセス権がありません",
            },
        },
    }

    created_count = 0
    for locale in locale_list:
        locale_dir = base_dir / locale
        locale_dir.mkdir(parents=True, exist_ok=True)

        messages_file = locale_dir / f"messages.{format}"
        if messages_file.exists():
            click.echo(f"  ⏭  {messages_file} (already exists)")
            continue

        # Use starter translations if available, otherwise minimal
        content = starter_messages.get(locale, {
            "welcome": f"Welcome [{locale}]",
            "goodbye": f"Goodbye [{locale}]",
            "greeting": f"Hello, {{name}}! [{locale}]",
        })

        if format == "json":
            messages_file.write_text(
                json.dumps(content, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
        elif format == "yaml":
            try:
                import yaml
                messages_file.write_text(
                    yaml.dump(content, allow_unicode=True, default_flow_style=False),
                    encoding="utf-8",
                )
            except ImportError:
                click.echo(click.style("  ⚠  PyYAML not installed — falling back to JSON", fg="yellow"))
                messages_file = locale_dir / "messages.json"
                messages_file.write_text(
                    json.dumps(content, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8",
                )

        click.echo(f"  ✅ {messages_file}")
        created_count += 1

    click.echo()
    if created_count > 0:
        click.echo(click.style(f"Created {created_count} locale file(s).", fg="green"))
    else:
        click.echo(click.style("No new files created (all already exist).", fg="yellow"))

    # Hint about workspace config
    click.echo()
    click.echo(click.style("Next steps:", fg="cyan"))
    click.echo("  1. Add i18n to your workspace.py:")
    click.echo()
    click.echo(click.style('     .integrate(Integration.i18n(', fg="white"))
    click.echo(click.style(f'         default_locale="{locale_list[0]}",', fg="white"))
    click.echo(click.style(f'         available_locales={locale_list},', fg="white"))
    click.echo(click.style('     ))', fg="white"))
    click.echo()
    click.echo("  2. Use translations in controllers:")
    click.echo(click.style('     msg = ctx.request.state["i18n"].t("messages.welcome")', fg="white"))
    click.echo()
    click.echo("  3. Use in templates:")
    click.echo(click.style('     {{ _("messages.welcome") }}', fg="white"))


def cmd_i18n_check(verbose: bool = False) -> None:
    """Validate i18n configuration and catalogs."""
    config = _load_i18n_config()

    if not config or not config.get("enabled", False):
        click.echo(click.style("I18n integration is not enabled.", fg="yellow"))
        click.echo("  Add .integrate(Integration.i18n(...)) to your workspace.py")
        click.echo("  Or run: aq i18n init")
        return

    click.echo(click.style("I18n Configuration Check", fg="cyan", bold=True))
    click.echo("─" * 40)

    click.echo(f"  Enabled:            {config.get('enabled')}")
    click.echo(f"  Default Locale:     {config.get('default_locale', 'en')}")
    click.echo(f"  Available Locales:  {config.get('available_locales', ['en'])}")
    click.echo(f"  Fallback Locale:    {config.get('fallback_locale', 'en')}")
    click.echo(f"  Catalog Dirs:       {config.get('catalog_dirs', ['locales'])}")
    click.echo(f"  Missing Key:        {config.get('missing_key_strategy', 'log_and_key')}")
    click.echo(f"  Auto Detect:        {config.get('auto_detect', True)}")
    click.echo(f"  Resolver Order:     {config.get('resolver_order', [])}")

    # Check catalog directories exist
    click.echo()
    click.echo(click.style("Catalog Directories:", fg="cyan"))
    catalog_dirs = config.get("catalog_dirs", ["locales"])
    all_ok = True

    for d in catalog_dirs:
        path = Path(d)
        if path.exists() and path.is_dir():
            locale_dirs = sorted([p.name for p in path.iterdir() if p.is_dir()])
            click.echo(f"  ✅ {d}/ ({len(locale_dirs)} locales: {', '.join(locale_dirs) or 'none'})")

            for locale_dir_name in locale_dirs:
                locale_path = path / locale_dir_name
                files = sorted([f.name for f in locale_path.iterdir() if f.is_file()])
                click.echo(f"     └── {locale_dir_name}/: {', '.join(files) or '(empty)'}")
        else:
            click.echo(f"  ❌ {d}/ (not found)")
            all_ok = False

    if all_ok:
        click.echo()
        click.echo(click.style("✅ Configuration looks good!", fg="green"))
    else:
        click.echo()
        click.echo(click.style("⚠  Some issues detected. Run 'aq i18n init' to create missing files.", fg="yellow"))


def cmd_i18n_inspect() -> None:
    """Show current i18n configuration as JSON."""
    config = _load_i18n_config()
    click.echo(json.dumps(config, indent=2, ensure_ascii=False))


def cmd_i18n_extract(
    source_dirs: Optional[str] = None,
    output: str = "locales/en/messages.json",
    merge: bool = True,
    verbose: bool = False,
) -> None:
    """
    Extract translation keys from Python and template source files.

    Scans for:
    - ``_("key")`` / ``_n("key", count)`` in Python files
    - ``{{ _("key") }}`` in Jinja2 templates
    - ``i18n.t("key")`` / ``i18n.tn("key", count)`` in Python files
    - ``lazy_t("key")`` / ``lazy_tn("key", count)`` in Python files
    """
    dirs = [Path(d.strip()) for d in (source_dirs or "modules,controllers").split(",")]
    click.echo(click.style("Extracting translation keys...", fg="cyan", bold=True))

    keys: Set[str] = set()

    # Patterns to match
    py_patterns = [
        re.compile(r'''(?:_|gettext|i18n\.t|i18n\.tn|i18n\.tp|lazy_t|lazy_tn)\(\s*["']([^"']+)["']'''),
    ]
    template_patterns = [
        re.compile(r'''\{\{[^}]*(?:_|_n|_p|gettext|ngettext)\(\s*["']([^"']+)["']'''),
    ]

    # Scan source directories
    for d in dirs:
        if not d.exists():
            if verbose:
                click.echo(f"  Skipping {d} (not found)")
            continue

        # Python files
        for py_file in d.rglob("*.py"):
            try:
                source = py_file.read_text(encoding="utf-8")
                for pattern in py_patterns:
                    for match in pattern.finditer(source):
                        keys.add(match.group(1))
            except Exception as e:
                if verbose:
                    click.echo(f"  ⚠  Error reading {py_file}: {e}")

        # Template files
        for tmpl_file in list(d.rglob("*.html")) + list(d.rglob("*.jinja2")) + list(d.rglob("*.j2")):
            try:
                source = tmpl_file.read_text(encoding="utf-8")
                for pattern in template_patterns:
                    for match in pattern.finditer(source):
                        keys.add(match.group(1))
            except Exception as e:
                if verbose:
                    click.echo(f"  ⚠  Error reading {tmpl_file}: {e}")

    if not keys:
        click.echo(click.style("No translation keys found.", fg="yellow"))
        return

    click.echo(f"  Found {len(keys)} unique key(s)")

    # Build key structure
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Load existing if merging
    existing: dict = {}
    if merge and output_path.exists():
        try:
            existing = json.loads(output_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    # Build nested dict from dotted keys
    result = existing.copy()
    new_keys = 0
    for key in sorted(keys):
        parts = key.split(".")
        target = result
        for i, part in enumerate(parts[:-1]):
            if part not in target or not isinstance(target[part], dict):
                target[part] = {}
            target = target[part]
        leaf = parts[-1]
        if leaf not in target:
            target[leaf] = ""  # Empty value for new keys
            new_keys += 1

    # Write output
    output_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    click.echo(f"  ✅ Written to {output_path}")
    click.echo(f"     New keys: {new_keys}")
    click.echo(f"     Total keys: {len(keys)}")

    if new_keys > 0:
        click.echo()
        click.echo(click.style("Remember to translate the empty values!", fg="yellow"))


def cmd_i18n_coverage(verbose: bool = False) -> None:
    """Show translation coverage per locale."""
    config = _load_i18n_config()

    if not config:
        click.echo(click.style("I18n is not configured.", fg="yellow"))
        return

    catalog_dirs = config.get("catalog_dirs", ["locales"])
    available_locales = config.get("available_locales", ["en"])
    default_locale = config.get("default_locale", "en")

    click.echo(click.style("Translation Coverage Report", fg="cyan", bold=True))
    click.echo("─" * 50)

    # Collect all keys from default locale
    default_keys: Set[str] = set()
    for d in catalog_dirs:
        default_dir = Path(d) / default_locale
        if default_dir.exists():
            for f in default_dir.rglob("*.json"):
                try:
                    data = json.loads(f.read_text(encoding="utf-8"))
                    ns = f.stem
                    _collect_keys(data, ns, default_keys)
                except Exception:
                    pass

    if not default_keys:
        click.echo(click.style(f"No keys found in default locale '{default_locale}'.", fg="yellow"))
        return

    click.echo(f"  Default locale ({default_locale}): {len(default_keys)} keys")
    click.echo()

    # Check coverage for each locale
    for locale in available_locales:
        locale_keys: Set[str] = set()
        for d in catalog_dirs:
            locale_dir = Path(d) / locale
            if locale_dir.exists():
                for f in locale_dir.rglob("*.json"):
                    try:
                        data = json.loads(f.read_text(encoding="utf-8"))
                        ns = f.stem
                        _collect_keys(data, ns, locale_keys)
                    except Exception:
                        pass

        if not locale_keys:
            pct = 0.0
        else:
            covered = len(default_keys & locale_keys)
            pct = (covered / len(default_keys)) * 100 if default_keys else 100.0

        # Color code
        if pct >= 100:
            color = "green"
            icon = "✅"
        elif pct >= 80:
            color = "yellow"
            icon = "🔶"
        elif pct > 0:
            color = "red"
            icon = "⚠ "
        else:
            color = "red"
            icon = "❌"

        click.echo(f"  {icon} {locale:10s} {pct:6.1f}%  ({len(locale_keys)}/{len(default_keys)} keys)")

        if verbose and pct < 100:
            missing = default_keys - locale_keys
            for key in sorted(missing)[:10]:
                click.echo(f"       Missing: {key}")
            if len(missing) > 10:
                click.echo(f"       ... and {len(missing) - 10} more")


def _collect_keys(data: dict, prefix: str, keys: Set[str], _depth: int = 0) -> None:
    """Recursively collect dotted keys from a nested dict."""
    if _depth > 20:
        return
    for k, v in data.items():
        full_key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            # Check if this is a plural dict
            plural_keys = {"zero", "one", "two", "few", "many", "other"}
            if set(v.keys()) <= plural_keys:
                keys.add(full_key)
            else:
                _collect_keys(v, full_key, keys, _depth + 1)
        else:
            keys.add(full_key)
