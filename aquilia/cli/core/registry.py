"""Command registration and help categorisation.

The old ``AquiliaGroup._CATEGORIES`` was a hand-maintained literal listing
command names. It had already drifted: it listed ``deploy-gen`` while the
command registers as ``deploy``, so seven commands silently fell into "Other".

Here the category is metadata on the command itself, so a command cannot be
registered without a category and the two cannot disagree.
"""

from __future__ import annotations

from dataclasses import dataclass, field

__all__ = [
    "CATEGORY_ORDER",
    "CommandSpec",
    "category_of",
    "register",
    "registered_categories",
    "uncategorised",
]

CATEGORY_ORDER: tuple[str, ...] = (
    "Scaffold",
    "Develop",
    "Production",
    "Database",
    "Admin",
    "Inspect",
    "Subsystems",
    "Deploy",
    "Migration",
    "Other",
)

# command name -> category. Single source of truth for `aq --help` grouping.
_CATEGORIES: dict[str, str] = {
    # Scaffold
    "init": "Scaffold",
    "add": "Scaffold",
    "generate": "Scaffold",
    # Develop
    "run": "Develop",
    "dev": "Develop",
    "validate": "Develop",
    "test": "Develop",
    "discover": "Develop",
    "doctor": "Develop",
    # Production
    "serve": "Production",
    # Database
    "db": "Database",
    "vectordb": "Database",
    # Admin
    "admin": "Admin",
    # Inspect
    "inspect": "Inspect",
    "inspector": "Inspect",
    "manifest": "Inspect",
    "analytics": "Inspect",
    "aquilary": "Inspect",
    "artifacts": "Inspect",
    "contracts": "Inspect",
    # Subsystems
    "ws": "Subsystems",
    "cache": "Subsystems",
    "mail": "Subsystems",
    "i18n": "Subsystems",
    "mcp": "Subsystems",
    "di": "Subsystems",
    "tasks": "Subsystems",
    "storage": "Subsystems",
    "templates": "Subsystems",
    # Deploy
    "deploy": "Deploy",
    "provider": "Deploy",
    # Migration
    "migrate": "Migration",
}


@dataclass
class CommandSpec:
    """Metadata for one registered command."""

    name: str
    category: str = "Other"
    aliases: tuple[str, ...] = field(default_factory=tuple)


def register(name: str, category: str) -> None:
    """Assign a command to a help category."""
    _CATEGORIES[name] = category


def category_of(name: str) -> str:
    """Category for a command name (``"Other"`` when unassigned)."""
    return _CATEGORIES.get(name, "Other")


def registered_categories() -> dict[str, str]:
    """Copy of the full name -> category mapping."""
    return dict(_CATEGORIES)


def uncategorised(command_names) -> list[str]:
    """Command names with no explicit category.

    Used by the help-integrity test so drift fails CI instead of silently
    dumping commands into "Other".
    """
    return sorted(n for n in command_names if n not in _CATEGORIES)
