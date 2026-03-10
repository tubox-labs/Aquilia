"""
Simple integrations — small typed configs for DI, routing, faults, etc.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class DiIntegration:
    """Dependency injection configuration."""

    _integration_type: str = field(default="dependency_injection", init=False, repr=False)

    auto_wire: bool = True
    enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "_integration_type": "dependency_injection",
            "enabled": self.enabled,
            "auto_wire": self.auto_wire,
        }


@dataclass
class RoutingIntegration:
    """Routing configuration."""

    _integration_type: str = field(default="routing", init=False, repr=False)

    strict_matching: bool = True
    enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "_integration_type": "routing",
            "enabled": self.enabled,
            "strict_matching": self.strict_matching,
        }


@dataclass
class FaultHandlingIntegration:
    """Fault handling configuration."""

    _integration_type: str = field(default="fault_handling", init=False, repr=False)

    default_strategy: str = "propagate"
    enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "_integration_type": "fault_handling",
            "enabled": self.enabled,
            "default_strategy": self.default_strategy,
        }


@dataclass
class PatternsIntegration:
    """Patterns configuration."""

    _integration_type: str = field(default="patterns", init=False, repr=False)

    enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {"_integration_type": "patterns", "enabled": self.enabled}


@dataclass
class RegistryIntegration:
    """Registry configuration."""

    _integration_type: str = field(default="registry", init=False, repr=False)

    enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {"_integration_type": "registry", "enabled": self.enabled}


@dataclass
class SerializersIntegration:
    """Global serializer settings."""

    _integration_type: str = field(default="serializers", init=False, repr=False)

    auto_discover: bool = True
    strict_validation: bool = True
    raise_on_error: bool = False
    date_format: str = "iso-8601"
    datetime_format: str = "iso-8601"
    coerce_decimal_to_string: bool = True
    compact_json: bool = True
    enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "_integration_type": "serializers",
            "enabled": self.enabled,
            "auto_discover": self.auto_discover,
            "strict_validation": self.strict_validation,
            "raise_on_error": self.raise_on_error,
            "date_format": self.date_format,
            "datetime_format": self.datetime_format,
            "coerce_decimal_to_string": self.coerce_decimal_to_string,
            "compact_json": self.compact_json,
        }
