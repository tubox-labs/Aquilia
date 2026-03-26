"""
Aquilia Native Dotenv Loader (``aquilia.dotenv``)
=================================================

A zero-dependency, production-ready ``.env`` file loader for Aquilia.

This module provides automatic loading of environment variables from ``.env``
files without requiring external packages like ``python-dotenv``. It is
designed to integrate seamlessly with the Aquilia configuration system.

Features
--------
* **Automatic loading** — Loads ``.env`` files at application startup.
* **Deterministic** — Files are loaded exactly once via singleton pattern.
* **Standard syntax** — Supports comments, quotes, multiline values, exports.
* **Respects existing** — Does not overwrite variables already in the environment.
* **Variable interpolation** — Supports ``${VAR}`` and ``$VAR`` syntax.
* **Multiple files** — Load from multiple files with configurable precedence.
* **Safe** — No eval(), exec(), or shell injection vulnerabilities.

Quick-start
-----------
Automatic (recommended)::

    from aquilia.dotenv import load_dotenv

    # Load .env from current directory (or workspace root)
    load_dotenv()

    # Now os.environ has your .env values
    import os
    print(os.environ.get("DATABASE_URL"))

Manual control::

    from aquilia.dotenv import DotEnv

    # Parse without loading into environment
    env = DotEnv.parse(".env")
    print(env)  # {'DATABASE_URL': '...', ...}

    # Load with override (replace existing values)
    DotEnv.load(".env", override=True)

Syntax
------
Standard ``.env`` syntax is supported::

    # Comments start with #
    SIMPLE=value
    QUOTED="value with spaces"
    SINGLE='value with spaces'
    EXPORT=exported value
    export EXPORTED=also works

    # Variable interpolation
    BASE_URL=http://localhost
    API_URL=${BASE_URL}/api
    ALT_SYNTAX=$BASE_URL/alt

    # Multiline (with quotes)
    MULTILINE="line1
    line2
    line3"

Security
--------
* No shell execution — values are parsed, not evaluated.
* No pickle or eval — purely string parsing.
* Strips BOM for UTF-8 files.
* Validates variable names (alphanumeric + underscore).
"""

from __future__ import annotations

import logging
import os
import re
from collections.abc import Callable, Mapping
from pathlib import Path
from threading import Lock
from typing import (
    TYPE_CHECKING,
    Any,
    Final,
    TypeAlias,
)

if TYPE_CHECKING:
    pass

__all__ = [
    "DotEnv",
    "DotEnvLoader",
    "load_dotenv",
    "dotenv_values",
    "find_dotenv",
    "ensure_dotenv_loaded",
    "is_dotenv_loaded",
    "reset_dotenv_state",
]

log = logging.getLogger(__name__)

# Type aliases for config values
EnvValue: TypeAlias = str | int | float | bool | None
EnvCastFunc: TypeAlias = Callable[[str], Any]
EnvMapping: TypeAlias = Mapping[str, str]


# ============================================================================
# Constants
# ============================================================================

# Valid variable name pattern
_VAR_NAME_PATTERN: Final = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")

# Variable interpolation patterns
_INTERPOLATE_BRACES: Final = re.compile(r"\$\{([a-zA-Z_][a-zA-Z0-9_]*)\}")
_INTERPOLATE_SIMPLE: Final = re.compile(r"\$([a-zA-Z_][a-zA-Z0-9_]*)")


# ============================================================================
# DotEnv Parser
# ============================================================================


class DotEnv:
    """
    Native dotenv file parser and loader.

    This class provides methods for parsing and loading environment variables
    from ``.env`` files without external dependencies.

    Thread-safe for concurrent access.
    """

    __slots__ = ("_path", "_values", "_encoding")

    def __init__(
        self,
        path: str | Path | None = None,
        encoding: str = "utf-8",
    ) -> None:
        """
        Initialize a DotEnv instance.

        Args:
            path: Path to the .env file. If None, uses find_dotenv().
            encoding: File encoding (default: utf-8).
        """
        self._path: Path | None = Path(path) if path else None
        self._encoding = encoding
        self._values: dict[str, str] = {}

    @classmethod
    def parse(
        cls,
        path: str | Path,
        *,
        encoding: str = "utf-8",
        interpolate: bool = True,
    ) -> dict[str, str]:
        """
        Parse a .env file and return a dictionary of values.

        This method does NOT modify os.environ.

        Args:
            path: Path to the .env file.
            encoding: File encoding (default: utf-8).
            interpolate: Whether to expand ${VAR} references (default: True).

        Returns:
            Dictionary of parsed environment variables.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f".env file not found: {path}")

        content = file_path.read_text(encoding=encoding)
        parsed = cls._parse_content(content)

        if interpolate:
            parsed = cls._interpolate(parsed)

        return parsed

    @classmethod
    def parse_string(
        cls,
        content: str,
        *,
        interpolate: bool = True,
    ) -> dict[str, str]:
        """
        Parse dotenv-formatted string content.

        Args:
            content: String content in dotenv format.
            interpolate: Whether to expand ${VAR} references.

        Returns:
            Dictionary of parsed environment variables.
        """
        parsed = cls._parse_content(content)
        if interpolate:
            parsed = cls._interpolate(parsed)
        return parsed

    @classmethod
    def load(
        cls,
        path: str | Path | None = None,
        *,
        override: bool = False,
        encoding: str = "utf-8",
        interpolate: bool = True,
    ) -> dict[str, str]:
        """
        Load environment variables from a .env file into os.environ.

        Args:
            path: Path to .env file. If None, searches for one.
            override: If True, overwrite existing environment variables.
            encoding: File encoding (default: utf-8).
            interpolate: Whether to expand ${VAR} references.

        Returns:
            Dictionary of variables that were loaded (for inspection).
        """
        if path is None:
            path = find_dotenv()
            if path is None:
                return {}

        file_path = Path(path)
        if not file_path.exists():
            return {}

        values = cls.parse(file_path, encoding=encoding, interpolate=interpolate)
        loaded: dict[str, str] = {}

        for key, value in values.items():
            if override or key not in os.environ:
                os.environ[key] = value
                loaded[key] = value

        return loaded

    @classmethod
    def _parse_content(cls, content: str) -> dict[str, str]:
        """
        Parse dotenv content into a dictionary.

        Handles:
        - Comments (# ...)
        - Empty lines
        - export prefix
        - Quoted values (single and double)
        - Multiline values (in quotes)
        - Escape sequences in double quotes
        """
        result: dict[str, str] = {}

        # Remove BOM if present
        if content.startswith("\ufeff"):
            content = content[1:]

        lines = content.splitlines()
        i = 0

        while i < len(lines):
            line = lines[i].strip()
            i += 1

            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue

            # Handle export prefix
            if line.startswith("export "):
                line = line[7:].strip()

            # Skip lines without =
            if "=" not in line:
                continue

            # Split on first =
            key, _, raw_value = line.partition("=")
            key = key.strip()

            # Validate key
            if not _VAR_NAME_PATTERN.match(key):
                log.warning("Invalid variable name: %r", key)
                continue

            raw_value = raw_value.strip()

            # Handle quoted values
            if raw_value.startswith('"'):
                # Double-quoted value - may be multiline
                value, i = cls._parse_double_quoted(raw_value, lines, i)
            elif raw_value.startswith("'"):
                # Single-quoted value - may be multiline
                value, i = cls._parse_single_quoted(raw_value, lines, i)
            else:
                # Unquoted value - strip inline comment
                value = cls._strip_inline_comment(raw_value)

            result[key] = value

        return result

    @classmethod
    def _parse_double_quoted(cls, raw_value: str, lines: list[str], line_idx: int) -> tuple[str, int]:
        """
        Parse a double-quoted value, handling multiline and escapes.

        Returns:
            Tuple of (parsed_value, next_line_index).
        """
        # Remove opening quote
        content = raw_value[1:]

        # Check for closing quote on same line
        if '"' in content:
            end_idx = content.index('"')
            value = content[:end_idx]
            return cls._process_escapes(value), line_idx

        # Multiline: collect until closing quote
        parts = [content]
        while line_idx < len(lines):
            line = lines[line_idx]
            line_idx += 1

            if '"' in line:
                end_idx = line.index('"')
                parts.append(line[:end_idx])
                break
            parts.append(line)

        value = "\n".join(parts)
        return cls._process_escapes(value), line_idx

    @classmethod
    def _parse_single_quoted(cls, raw_value: str, lines: list[str], line_idx: int) -> tuple[str, int]:
        """
        Parse a single-quoted value (no escape processing).

        Returns:
            Tuple of (parsed_value, next_line_index).
        """
        # Remove opening quote
        content = raw_value[1:]

        # Check for closing quote on same line
        if "'" in content:
            end_idx = content.index("'")
            return content[:end_idx], line_idx

        # Multiline: collect until closing quote
        parts = [content]
        while line_idx < len(lines):
            line = lines[line_idx]
            line_idx += 1

            if "'" in line:
                end_idx = line.index("'")
                parts.append(line[:end_idx])
                break
            parts.append(line)

        return "\n".join(parts), line_idx

    @classmethod
    def _strip_inline_comment(cls, value: str) -> str:
        """Strip inline comment from unquoted value."""
        # Find # that's not escaped
        result = []
        escaped = False
        for char in value:
            if escaped:
                result.append(char)
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == "#":
                break
            else:
                result.append(char)

        return "".join(result).strip()

    @classmethod
    def _process_escapes(cls, value: str) -> str:
        """Process escape sequences in double-quoted strings."""
        replacements = {
            "\\n": "\n",
            "\\r": "\r",
            "\\t": "\t",
            '\\"': '"',
            "\\$": "$",
            "\\\\": "\\",
        }
        for escaped, actual in replacements.items():
            value = value.replace(escaped, actual)
        return value

    @classmethod
    def _interpolate(cls, values: dict[str, str]) -> dict[str, str]:
        """
        Expand variable references in values.

        Supports ${VAR} and $VAR syntax.
        Looks up values in the parsed dict first, then os.environ.
        """
        result: dict[str, str] = {}

        def resolve(match: re.Match[str]) -> str:
            var_name = match.group(1)
            # Priority: already-resolved values > parsed values > os.environ
            if var_name in result:
                return result[var_name]
            if var_name in values:
                return values[var_name]
            return os.environ.get(var_name, "")

        # Process in order, allowing later vars to reference earlier ones
        for key, value in values.items():
            # Expand ${VAR} first, then $VAR
            expanded = _INTERPOLATE_BRACES.sub(resolve, value)
            expanded = _INTERPOLATE_SIMPLE.sub(resolve, expanded)
            result[key] = expanded

        return result


# ============================================================================
# DotEnvLoader — Singleton for automatic loading
# ============================================================================


class DotEnvLoader:
    """
    Singleton loader that ensures .env files are loaded exactly once.

    This class provides a thread-safe mechanism for automatic dotenv loading
    that integrates with Aquilia's configuration system.

    Usage::

        # Automatic loading (recommended)
        DotEnvLoader.ensure_loaded()

        # Reset for testing
        DotEnvLoader.reset()

        # Check if already loaded
        if DotEnvLoader.is_loaded():
            print("Already loaded")
    """

    _instance: DotEnvLoader | None = None
    _lock: Lock = Lock()

    # State
    _loaded: bool = False
    _loaded_files: list[Path] = []
    _loaded_values: dict[str, str] = {}

    # Configuration
    _search_paths: list[str] | None = None
    _auto_load: bool = True
    _override: bool = False
    _interpolate: bool = True

    def __new__(cls) -> DotEnvLoader:
        """Singleton pattern — return the same instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def configure(
        cls,
        *,
        search_paths: list[str] | None = None,
        auto_load: bool = True,
        override: bool = False,
        interpolate: bool = True,
    ) -> None:
        """
        Configure the loader before loading.

        Must be called before ensure_loaded() or the first Env.resolve().

        Args:
            search_paths: List of file paths to search for (in order).
            auto_load: Whether to auto-load when Env.resolve() is called.
            override: Whether to override existing environment variables.
            interpolate: Whether to interpolate variables while parsing.
        """
        with cls._lock:
            if cls._loaded:
                log.warning("DotEnvLoader.configure() called after loading — no effect")
                return

            if search_paths is not None:
                cls._search_paths = search_paths
            cls._auto_load = auto_load
            cls._override = override
            cls._interpolate = interpolate

    @classmethod
    def ensure_loaded(
        cls,
        *,
        path: str | Path | None = None,
        search_paths: list[str] | None = None,
    ) -> dict[str, str]:
        """
        Ensure dotenv files are loaded (idempotent).

        This method is thread-safe and will only load files once.

        Args:
            path: Specific .env file to load (skips search).
            search_paths: Override search paths for this call.

        Returns:
            Dictionary of all loaded variables.
        """
        with cls._lock:
            if cls._loaded:
                return cls._loaded_values.copy()

            cls._loaded = True
            if search_paths is not None:
                paths_to_try = list(search_paths)
            elif cls._search_paths is not None:
                paths_to_try = list(cls._search_paths)
            else:
                paths_to_try = _default_dotenv_search_paths()

            # If specific path provided, use only that
            if path is not None:
                paths_to_try = [str(path)]

            # Find workspace root
            workspace_root = _find_workspace_root()

            mode = _resolve_runtime_mode()
            expanded_paths = [p.format(mode=mode, env=mode) if "{" in p else p for p in paths_to_try]

            # Parse all files first, then apply in a single pass so precedence is:
            # process env > dotenv merged values (or dotenv > process env if override=True).
            merged_values: dict[str, str] = {}

            for file_path in expanded_paths:
                full_path = workspace_root / file_path if workspace_root else Path(file_path)

                if full_path.exists():
                    try:
                        loaded = DotEnv.parse(
                            full_path,
                            interpolate=cls._interpolate,
                        )
                        cls._loaded_files.append(full_path)
                        merged_values.update(loaded)
                    except Exception as exc:
                        log.error("Failed to load %s: %s", full_path, exc)

            for key, value in merged_values.items():
                if cls._override or key not in os.environ:
                    os.environ[key] = value

            cls._loaded_values = merged_values.copy()

            return cls._loaded_values.copy()

    @classmethod
    def is_loaded(cls) -> bool:
        """Check if dotenv files have been loaded."""
        return cls._loaded

    @classmethod
    def loaded_files(cls) -> list[Path]:
        """Return list of files that were loaded."""
        return cls._loaded_files.copy()

    @classmethod
    def loaded_values(cls) -> dict[str, str]:
        """Return copy of all loaded values."""
        return cls._loaded_values.copy()

    @classmethod
    def reset(cls) -> None:
        """
        Reset the loader state.

        Use this in tests to allow reloading with different configuration.
        Does NOT remove values from os.environ.
        """
        with cls._lock:
            cls._loaded = False
            cls._loaded_files = []
            cls._loaded_values = {}


# ============================================================================
# Helper functions
# ============================================================================


def _find_workspace_root() -> Path | None:
    """
    Find the workspace root directory.

    Checks:
    1. AQUILIA_WORKSPACE environment variable
    2. Current directory if it contains workspace.py
    3. Walk up from current directory to find workspace.py
    """
    # Check environment variable
    ws_env = os.environ.get("AQUILIA_WORKSPACE")
    if ws_env:
        ws_path = Path(ws_env)
        if ws_path.is_dir():
            return ws_path

    # Check current directory
    cwd = Path.cwd()
    if (cwd / "workspace.py").exists():
        return cwd

    # Walk up the directory tree
    current = cwd
    for _ in range(10):  # Limit depth
        parent = current.parent
        if parent == current:
            break
        if (parent / "workspace.py").exists():
            return parent
        current = parent

    # Fall back to current directory
    return cwd


def _resolve_runtime_mode() -> str:
    """Resolve runtime mode used for mode-specific dotenv path expansion."""
    mode = os.environ.get("AQUILIA_ENV") or os.environ.get("AQ_ENV") or "dev"
    mode = mode.lower().strip()
    if mode == "production":
        return "prod"
    return mode or "dev"


def _default_dotenv_search_paths(mode: str | None = None) -> list[str]:
    """
    Return default dotenv search paths when no explicit paths are configured.

    Order defines precedence (later files override earlier dotenv files).
    """
    resolved_mode = (mode or _resolve_runtime_mode()).lower().strip() or "dev"
    if resolved_mode == "production":
        resolved_mode = "prod"

    candidates = [
        ".env",
        ".env.example",
        ".env.defaults",
        ".env.default",
        ".env.local",
        f".env.{resolved_mode}",
        f".env.{resolved_mode}.local",
        "config/.env",
        f"config/.env.{resolved_mode}",
        f"config/.env.{resolved_mode}.local",
    ]
    return list(dict.fromkeys(candidates))


def find_dotenv(
    filename: str = ".env",
    raise_error: bool = False,
    usecwd: bool = False,
) -> Path | None:
    """
    Search for a .env file.

    Args:
        filename: Name of the file to search for (default: .env).
        raise_error: If True, raise FileNotFoundError if not found.
        usecwd: If True, only search current directory.

    Returns:
        Path to the file, or None if not found.

    Raises:
        FileNotFoundError: If raise_error=True and file not found.
    """
    if usecwd:
        path = Path.cwd() / filename
        if path.exists():
            return path
        if raise_error:
            raise FileNotFoundError(f"{filename} not found in current directory")
        return None

    # Try workspace root first
    workspace_root = _find_workspace_root()
    if workspace_root:
        path = workspace_root / filename
        if path.exists():
            return path

    # Try current directory
    path = Path.cwd() / filename
    if path.exists():
        return path

    # Walk up directory tree
    current = Path.cwd()
    for _ in range(10):
        parent = current.parent
        if parent == current:
            break
        path = parent / filename
        if path.exists():
            return path
        current = parent

    if raise_error:
        raise FileNotFoundError(f"{filename} not found")
    return None


def load_dotenv(
    dotenv_path: str | Path | None = None,
    *,
    override: bool = False,
    interpolate: bool = True,
    encoding: str = "utf-8",
) -> bool:
    """
    Load a .env file into os.environ.

    This is the main entry point for loading dotenv files.

    Args:
        dotenv_path: Path to .env file. If None, searches automatically.
        override: If True, overwrite existing environment variables.
        interpolate: If True, expand ${VAR} references.
        encoding: File encoding (default: utf-8).

    Returns:
        True if any values were loaded, False otherwise.

    Example::

        from aquilia.dotenv import load_dotenv

        # Load .env from workspace root
        load_dotenv()

        # Load specific file
        load_dotenv(".env.production")

        # Override existing values
        load_dotenv(override=True)
    """
    if dotenv_path is None:
        dotenv_path = find_dotenv()
        if dotenv_path is None:
            return False

    try:
        loaded = DotEnv.load(
            dotenv_path,
            override=override,
            encoding=encoding,
            interpolate=interpolate,
        )
        return len(loaded) > 0
    except FileNotFoundError:
        return False


def dotenv_values(
    dotenv_path: str | Path | None = None,
    *,
    interpolate: bool = True,
    encoding: str = "utf-8",
) -> dict[str, str]:
    """
    Parse a .env file and return values WITHOUT loading into os.environ.

    Useful for inspecting .env contents without side effects.

    Args:
        dotenv_path: Path to .env file. If None, searches automatically.
        interpolate: If True, expand ${VAR} references.
        encoding: File encoding (default: utf-8).

    Returns:
        Dictionary of parsed values, or empty dict if file not found.

    Example::

        from aquilia.dotenv import dotenv_values

        # Get values without modifying environment
        values = dotenv_values(".env.production")
        print(values.get("DATABASE_URL"))
    """
    if dotenv_path is None:
        dotenv_path = find_dotenv()
        if dotenv_path is None:
            return {}

    try:
        return DotEnv.parse(dotenv_path, encoding=encoding, interpolate=interpolate)
    except FileNotFoundError:
        return {}


def ensure_dotenv_loaded(
    path: str | Path | None = None,
    *,
    auto_load: bool | None = None,
) -> None:
    """
    Ensure dotenv is loaded (idempotent).

    Called automatically by :class:`~aquilia.pyconfig.AquilaConfig` on first access.
    This function is thread-safe and will only load the .env file once,
    regardless of how many times it is called.

    The auto-loading behavior can be controlled by the ``AQUILIA_DOTENV_AUTO_LOAD``
    environment variable (default: ``true``).

    Args:
        path: Path to .env file (default: ``.env`` in workspace root)
        auto_load: Override auto-load behavior. If ``None``, uses
            ``AQUILIA_DOTENV_AUTO_LOAD`` env var (default: ``true``).

    Example::

        from aquilia.dotenv import ensure_dotenv_loaded

        # Ensure .env is loaded (no-op if already loaded)
        ensure_dotenv_loaded()
    """
    # Check if auto-loading is enabled
    if auto_load is None:
        auto_load_env = os.environ.get("AQUILIA_DOTENV_AUTO_LOAD", "true").lower()
        auto_load = auto_load_env in ("true", "1", "yes", "on")

    if not auto_load:
        return

    # Use the DotEnvLoader singleton
    DotEnvLoader.ensure_loaded(path=path)


def is_dotenv_loaded() -> bool:
    """
    Check if dotenv has been loaded.

    Returns:
        True if :func:`load_dotenv` or :func:`ensure_dotenv_loaded` has been
        called successfully.
    """
    return DotEnvLoader.is_loaded()


def reset_dotenv_state() -> None:
    """
    Reset dotenv loaded state.

    This is primarily intended for testing purposes. It resets the internal
    state so that :func:`ensure_dotenv_loaded` will load the .env file again
    on the next call.

    .. warning::

        This does **not** remove variables from ``os.environ``. It only resets
        the internal flag that tracks whether dotenv has been loaded.
    """
    DotEnvLoader.reset()
