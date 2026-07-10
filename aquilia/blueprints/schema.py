"""
Aquilia Contract Schema -- OpenAPI/JSON Schema generation.

Generates OpenAPI 3.x compatible schemas from Contract classes,
including per-projection schemas and $ref for Lens'd Contracts.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .core import Contract


__all__ = ["generate_schema", "generate_component_schemas"]


def generate_schema(
    contract_cls: type[Contract],
    *,
    projection: str | None = None,
    mode: str = "output",
) -> dict[str, Any]:
    """
    Generate a JSON Schema for a Contract.

    Args:
        contract_cls: The Contract class
        projection: Named projection (None = default)
        mode: "output" (response) or "input" (request body)

    Returns:
        JSON Schema dict
    """
    return contract_cls.to_schema(projection=projection, mode=mode)


def generate_component_schemas(
    *contract_classes: type[Contract],
    include_projections: bool = True,
) -> dict[str, dict[str, Any]]:
    """
    Generate OpenAPI component schemas for multiple Contracts.

    Returns a dict suitable for OpenAPI's ``components.schemas`` section.

    Args:
        contract_classes: Contract classes to generate schemas for
        include_projections: If True, generate separate schemas for each projection
    """
    schemas: dict[str, dict[str, Any]] = {}

    for bp_cls in contract_classes:
        # Default schema
        name = bp_cls.__name__
        schemas[name] = bp_cls.to_schema(mode="output")
        schemas[f"{name}_Input"] = bp_cls.to_schema(mode="input")

        # Per-projection schemas
        if include_projections and hasattr(bp_cls, "_projections"):
            for proj_name in bp_cls._projections.available:
                if proj_name == "__all__":
                    continue
                key = f"{name}_{proj_name}"
                schemas[key] = bp_cls.to_schema(projection=proj_name, mode="output")

    return schemas
