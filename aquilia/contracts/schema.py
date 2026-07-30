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
    Generate an OpenAPI 3.x / JSON Schema dictionary for a given Contract class.

    Purpose:
        Produces standardized JSON Schema definitions for Contract classes, supporting both request body (``"input"``)
        and response payload (``"output"``) validation modes, with optional field projection filtering.

    Lifecycle:
        Invoked during OpenAPI documentation generation, route schema building, or standalone contract inspection.

    Execution Order:
        1. Resolve target Contract class and projection name.
        2. Delegate schema generation to ``contract_cls.to_schema(projection=projection, mode=mode)``.
        3. Return JSON Schema dictionary.

    Parameters:
        contract_cls (type[Contract]):
            The target ``Contract`` subclass class object.
        projection (str | None, optional):
            Name of specific projection to generate schema for. Defaults to ``None`` (default projection).
        mode (str, optional):
            Schema direction mode: ``"output"`` (response format) or ``"input"`` (request body format). Defaults to ``"output"``.

    Returns:
        dict[str, Any]:
            JSON Schema dictionary conforming to OpenAPI 3.x specifications.

    Exceptions:
        ProjectionFault: If specified projection does not exist on the Contract.

    Notes:
        - Input mode marks write-only fields as available and read-only fields as excluded or read-only.
        - Output mode strips write-only fields (e.g. passwords).

    Examples:
        >>> schema = generate_schema(UserContract, projection="summary", mode="output")
        >>> schema["type"]
        'object'
    """
    return contract_cls.to_schema(projection=projection, mode=mode)


def generate_component_schemas(
    *contract_classes: type[Contract],
    include_projections: bool = True,
) -> dict[str, dict[str, Any]]:
    """
    Generate a dictionary of OpenAPI ``components.schemas`` for multiple Contract classes.

    Purpose:
        Aggregates OpenAPI schemas across multiple contracts and projections into a flat component dictionary suitable for OpenAPI specification documents.

    Lifecycle:
        Invoked during OpenAPI document synthesis across application routes.

    Execution Order:
        1. Iterate through provided ``contract_classes``.
        2. Generate primary output schema (``ContractName``) and input schema (``ContractName_Input``).
        3. Iterate through registered projection names if ``include_projections=True``.
        4. Return aggregated mapping of component keys to JSON Schemas.

    Parameters:
        *contract_classes (type[Contract]):
            Variadic Contract classes to include in the schema dictionary.
        include_projections (bool, optional):
            If ``True``, generates individual schema entries for each named projection. Defaults to ``True``.

    Returns:
        dict[str, dict[str, Any]]:
            Mapping of schema component names (e.g. ``"UserContract_summary"``) to schema definitions.

    Exceptions:
        None.

    Examples:
        >>> components = generate_component_schemas(UserContract, ProductContract)
        >>> "UserContract_Input" in components
        True
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
