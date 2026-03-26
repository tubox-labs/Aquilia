"""
Configuration type definitions for Aquilia.

This module provides type aliases and protocols used throughout the
configuration system, including pyconfig and dotenv.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any, Protocol, TypeAlias, TypeVar, runtime_checkable

# ============================================================================
# Basic config value types
# ============================================================================

#: Primitive values that can appear in configuration
ConfigPrimitive: TypeAlias = str | int | float | bool | None

#: Any value that can be used in configuration (recursive)
ConfigValue: TypeAlias = ConfigPrimitive | list["ConfigValue"] | dict[str, "ConfigValue"]

#: A configuration dictionary
ConfigDict: TypeAlias = dict[str, ConfigValue]

#: Type variable for generic config value operations
T = TypeVar("T")

# ============================================================================
# Environment variable types
# ============================================================================

#: Environment variable name
EnvVarName: TypeAlias = str

#: Raw environment variable value (always a string)
EnvVarValue: TypeAlias = str

#: Mapping of environment variables
EnvMapping: TypeAlias = Mapping[str, str]

#: Callable that casts string environment values to typed values
EnvCaster: TypeAlias = Callable[[str], Any]

#: Valid cast types for Env class (type or callable)
EnvCastType: TypeAlias = type | EnvCaster | None


# ============================================================================
# Config protocols
# ============================================================================


@runtime_checkable
class ConfigSource(Protocol):
    """Protocol for configuration sources that can be converted to dict."""

    def to_dict(self) -> ConfigDict:
        """Convert this config source to a dictionary."""
        ...


@runtime_checkable
class EnvResolvable(Protocol):
    """Protocol for values that resolve from environment variables."""

    def resolve(self) -> ConfigValue:
        """Resolve the value from the environment."""
        ...


@runtime_checkable
class SecretRevealable(Protocol):
    """Protocol for secret values that can be revealed."""

    def reveal(self) -> str | None:
        """Reveal the secret value."""
        ...


@runtime_checkable
class ConfigSection(Protocol):
    """Protocol for config section classes."""

    @classmethod
    def to_dict(cls) -> ConfigDict:
        """Convert this section to a dictionary."""
        ...


# ============================================================================
# DotEnv types
# ============================================================================

#: Parsed dotenv values (always string to string)
DotEnvValues: TypeAlias = dict[str, str]

#: Path to a dotenv file
DotEnvPath: TypeAlias = str


__all__ = [
    # Basic types
    "ConfigPrimitive",
    "ConfigValue",
    "ConfigDict",
    # Env types
    "EnvVarName",
    "EnvVarValue",
    "EnvMapping",
    "EnvCaster",
    "EnvCastType",
    # Protocols
    "ConfigSource",
    "EnvResolvable",
    "SecretRevealable",
    "ConfigSection",
    # DotEnv types
    "DotEnvValues",
    "DotEnvPath",
]
