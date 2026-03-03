"""
Translation Catalogs — Storage and retrieval of translation strings.

Supports multiple catalog backends:
- ``MemoryCatalog``: In-memory dict-based catalog (testing, programmatic use)
- ``FileCatalog``: File-based catalog (JSON/YAML files from ``locales/`` directory)
- ``NamespacedCatalog``: Module-scoped catalog with dotted key access
- ``MergedCatalog``: Layered catalog with fallback (module → global → default)

Key format uses dot notation: ``"namespace.key"`` or ``"module.section.key"``

File layout::

    locales/
    ├── en/
    │   ├── messages.json      →  { "welcome": "Hello", "bye": "Goodbye" }
    │   └── errors.json        →  { "not_found": "Not found" }
    ├── fr/
    │   ├── messages.json      →  { "welcome": "Bonjour", "bye": "Au revoir" }
    │   └── errors.json        →  { "not_found": "Non trouvé" }
    └── de/
        └── messages.json      →  { "welcome": "Hallo" }

Access: ``i18n.t("messages.welcome", locale="fr")``  → ``"Bonjour"``
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set

logger = logging.getLogger("aquilia.i18n.catalog")


# ═══════════════════════════════════════════════════════════════════════════
# Abstract Base
# ═══════════════════════════════════════════════════════════════════════════

class TranslationCatalog(ABC):
    """Abstract base for translation catalogs."""

    @abstractmethod
    def get(
        self,
        key: str,
        locale: str,
        *,
        default: Optional[str] = None,
    ) -> Optional[str]:
        """
        Retrieve a translation string.

        Args:
            key: Dot-notated key (e.g. ``"messages.welcome"``)
            locale: BCP 47 locale tag
            default: Fallback value if key not found

        Returns:
            Translation string or *default*
        """
        ...

    @abstractmethod
    def get_plural(
        self,
        key: str,
        locale: str,
        category: str,
        *,
        default: Optional[str] = None,
    ) -> Optional[str]:
        """
        Retrieve a plural translation variant.

        Translation files can define plural forms as nested dicts::

            {
                "items_count": {
                    "one": "{count} item",
                    "other": "{count} items"
                }
            }

        Args:
            key: Dot-notated key
            locale: BCP 47 locale tag
            category: Plural category (``"one"``, ``"other"``, etc.)
            default: Fallback value

        Returns:
            Plural variant string or *default*
        """
        ...

    @abstractmethod
    def has(self, key: str, locale: str) -> bool:
        """Check if a key exists for a locale."""
        ...

    @abstractmethod
    def locales(self) -> Set[str]:
        """Return set of available locale tags."""
        ...

    @abstractmethod
    def keys(self, locale: str) -> Set[str]:
        """Return all keys for a locale."""
        ...


# ═══════════════════════════════════════════════════════════════════════════
# Memory Catalog
# ═══════════════════════════════════════════════════════════════════════════

class MemoryCatalog(TranslationCatalog):
    """
    In-memory translation catalog backed by nested dicts.

    Ideal for testing, small apps, or programmatic construction.

    Args:
        translations: Dict of ``{locale: {key: value}}``

    Example::

        catalog = MemoryCatalog({
            "en": {
                "messages": {
                    "welcome": "Welcome, {name}!",
                    "items_count": {
                        "one": "{count} item",
                        "other": "{count} items",
                    }
                }
            },
            "fr": {
                "messages": {
                    "welcome": "Bienvenue, {name} !",
                }
            }
        })
    """

    def __init__(self, translations: Optional[Dict[str, Dict]] = None):
        self._data: Dict[str, Dict] = translations or {}

    def add(self, locale: str, translations: Dict) -> None:
        """Add translations for a locale (merges with existing)."""
        if locale in self._data:
            self._deep_merge(self._data[locale], translations)
        else:
            self._data[locale] = translations

    def _resolve_key(self, data: Dict, key: str) -> Any:
        """Resolve a dotted key against a nested dict."""
        parts = key.split(".")
        current = data
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        return current

    def get(
        self,
        key: str,
        locale: str,
        *,
        default: Optional[str] = None,
    ) -> Optional[str]:
        data = self._data.get(locale)
        if data is None:
            return default

        value = self._resolve_key(data, key)
        if value is None:
            return default
        if isinstance(value, dict):
            # Plural dict — return "other" form or first available
            return value.get("other", default)
        return str(value)

    def get_plural(
        self,
        key: str,
        locale: str,
        category: str,
        *,
        default: Optional[str] = None,
    ) -> Optional[str]:
        data = self._data.get(locale)
        if data is None:
            return default

        value = self._resolve_key(data, key)
        if value is None:
            return default

        if isinstance(value, dict):
            # Try exact category, then "other" fallback
            result = value.get(category)
            if result is not None:
                return str(result)
            return str(value.get("other", default or ""))
        # Non-plural key — return as-is
        return str(value)

    def has(self, key: str, locale: str) -> bool:
        data = self._data.get(locale)
        if data is None:
            return False
        return self._resolve_key(data, key) is not None

    def locales(self) -> Set[str]:
        return set(self._data.keys())

    def keys(self, locale: str) -> Set[str]:
        data = self._data.get(locale, {})
        result: set[str] = set()
        self._collect_keys(data, "", result)
        return result

    def _collect_keys(self, data: Dict, prefix: str, result: Set[str]) -> None:
        """Recursively collect dotted keys."""
        for k, v in data.items():
            full_key = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                # Check if it's a plural dict
                if any(cat in v for cat in ("zero", "one", "two", "few", "many", "other")):
                    result.add(full_key)
                else:
                    self._collect_keys(v, full_key, result)
            else:
                result.add(full_key)

    @staticmethod
    def _deep_merge(base: Dict, overlay: Dict) -> None:
        """Deep-merge overlay into base."""
        for k, v in overlay.items():
            if k in base and isinstance(base[k], dict) and isinstance(v, dict):
                MemoryCatalog._deep_merge(base[k], v)
            else:
                base[k] = v


# ═══════════════════════════════════════════════════════════════════════════
# File Catalog
# ═══════════════════════════════════════════════════════════════════════════

class FileCatalog(TranslationCatalog):
    """
    File-based translation catalog loading from ``locales/`` directory.

    Scans directories for locale subdirectories containing JSON
    or YAML translation files.

    Directory layout::

        locales/
        ├── en/
        │   ├── messages.json
        │   └── errors.json
        ├── fr/
        │   └── messages.json
        └── de/
            └── messages.json

    The filename (without extension) becomes the top-level namespace.
    E.g. ``locales/en/messages.json`` with key ``welcome`` is accessed
    as ``"messages.welcome"``.

    Args:
        directories: List of directory paths to scan for locales
        file_extensions: File extensions to load (default: ``.json``)
        watch: Enable file-watching for hot-reload (dev mode)
    """

    def __init__(
        self,
        directories: Sequence[str | Path],
        file_extensions: Sequence[str] = (".json",),
        watch: bool = False,
    ):
        self._directories = [Path(d) for d in directories]
        self._extensions = tuple(file_extensions)
        self._watch = watch
        self._inner = MemoryCatalog()
        self._loaded = False
        self._file_mtimes: Dict[Path, float] = {}

    def load(self) -> None:
        """Load all translation files from configured directories."""
        for directory in self._directories:
            if not directory.exists():
                logger.debug("i18n directory does not exist: %s", directory)
                continue
            self._scan_directory(directory)
        self._loaded = True

    def reload(self) -> None:
        """Reload changed files (hot-reload support)."""
        for directory in self._directories:
            if directory.exists():
                self._scan_directory(directory, check_mtime=True)

    def _scan_directory(self, root: Path, check_mtime: bool = False) -> None:
        """Scan a locale directory tree."""
        if not root.is_dir():
            return

        for locale_dir in sorted(root.iterdir()):
            if not locale_dir.is_dir():
                continue
            # Directory name = locale tag
            locale_tag = locale_dir.name

            for file_path in sorted(locale_dir.rglob("*")):
                if not file_path.is_file():
                    continue
                if not any(file_path.name.endswith(ext) for ext in self._extensions):
                    continue

                # Check mtime for hot-reload
                if check_mtime:
                    current_mtime = file_path.stat().st_mtime
                    if file_path in self._file_mtimes and self._file_mtimes[file_path] >= current_mtime:
                        continue
                    self._file_mtimes[file_path] = current_mtime
                else:
                    self._file_mtimes[file_path] = file_path.stat().st_mtime

                # Compute namespace from file path relative to locale dir
                rel = file_path.relative_to(locale_dir)
                namespace = str(rel.with_suffix("")).replace("/", ".").replace("\\", ".")

                # Load file
                data = self._load_file(file_path)
                if data:
                    self._inner.add(locale_tag, {namespace: data})
                    logger.debug(
                        "Loaded i18n: %s/%s (%d keys)",
                        locale_tag, namespace, len(data),
                    )

    def _load_file(self, path: Path) -> Optional[Dict]:
        """Load a single translation file."""
        try:
            if path.suffix == ".json":
                return json.loads(path.read_text(encoding="utf-8"))
            elif path.suffix in (".yaml", ".yml"):
                try:
                    import yaml
                    return yaml.safe_load(path.read_text(encoding="utf-8"))
                except ImportError:
                    logger.warning(
                        "PyYAML not installed — cannot load %s. "
                        "Install with: pip install pyyaml", path,
                    )
                    return None
            else:
                return None
        except Exception as exc:
            logger.error("Failed to load translation file %s: %s", path, exc)
            return None

    def _ensure_loaded(self) -> None:
        if not self._loaded:
            self.load()

    def get(self, key: str, locale: str, *, default: Optional[str] = None) -> Optional[str]:
        self._ensure_loaded()
        return self._inner.get(key, locale, default=default)

    def get_plural(self, key: str, locale: str, category: str, *, default: Optional[str] = None) -> Optional[str]:
        self._ensure_loaded()
        return self._inner.get_plural(key, locale, category, default=default)

    def has(self, key: str, locale: str) -> bool:
        self._ensure_loaded()
        return self._inner.has(key, locale)

    def locales(self) -> Set[str]:
        self._ensure_loaded()
        return self._inner.locales()

    def keys(self, locale: str) -> Set[str]:
        self._ensure_loaded()
        return self._inner.keys(locale)


# ═══════════════════════════════════════════════════════════════════════════
# Namespaced Catalog
# ═══════════════════════════════════════════════════════════════════════════

class NamespacedCatalog(TranslationCatalog):
    """
    Wraps a catalog with a fixed namespace prefix.

    Useful for module-scoped i18n where each module has its own
    translation keys without conflicts.

    Example::

        base = FileCatalog(["locales"])
        users_i18n = NamespacedCatalog(base, "users")
        users_i18n.get("welcome", "en")
        # → looks up "users.welcome" in the base catalog
    """

    def __init__(self, inner: TranslationCatalog, namespace: str):
        self._inner = inner
        self._namespace = namespace

    def _prefix(self, key: str) -> str:
        return f"{self._namespace}.{key}" if self._namespace else key

    def get(self, key: str, locale: str, *, default: Optional[str] = None) -> Optional[str]:
        return self._inner.get(self._prefix(key), locale, default=default)

    def get_plural(self, key: str, locale: str, category: str, *, default: Optional[str] = None) -> Optional[str]:
        return self._inner.get_plural(self._prefix(key), locale, category, default=default)

    def has(self, key: str, locale: str) -> bool:
        return self._inner.has(self._prefix(key), locale)

    def locales(self) -> Set[str]:
        return self._inner.locales()

    def keys(self, locale: str) -> Set[str]:
        prefix = f"{self._namespace}."
        return {
            k[len(prefix):] for k in self._inner.keys(locale)
            if k.startswith(prefix)
        }


# ═══════════════════════════════════════════════════════════════════════════
# Merged Catalog
# ═══════════════════════════════════════════════════════════════════════════

class MergedCatalog(TranslationCatalog):
    """
    Layered catalog that queries multiple catalogs with fallback.

    Queries catalogs in order; the first to return a value wins.
    Useful for layering module-specific translations over global ones.

    Example::

        global_catalog = FileCatalog(["locales"])
        module_catalog = FileCatalog(["modules/users/locales"])
        merged = MergedCatalog([module_catalog, global_catalog])
    """

    def __init__(self, catalogs: Sequence[TranslationCatalog]):
        self._catalogs = list(catalogs)

    def add(self, catalog: TranslationCatalog) -> None:
        """Add a catalog to the beginning (highest priority)."""
        self._catalogs.insert(0, catalog)

    def get(self, key: str, locale: str, *, default: Optional[str] = None) -> Optional[str]:
        for cat in self._catalogs:
            val = cat.get(key, locale)
            if val is not None:
                return val
        return default

    def get_plural(self, key: str, locale: str, category: str, *, default: Optional[str] = None) -> Optional[str]:
        for cat in self._catalogs:
            val = cat.get_plural(key, locale, category)
            if val is not None:
                return val
        return default

    def has(self, key: str, locale: str) -> bool:
        return any(cat.has(key, locale) for cat in self._catalogs)

    def locales(self) -> Set[str]:
        result: set[str] = set()
        for cat in self._catalogs:
            result.update(cat.locales())
        return result

    def keys(self, locale: str) -> Set[str]:
        result: set[str] = set()
        for cat in self._catalogs:
            result.update(cat.keys(locale))
        return result
