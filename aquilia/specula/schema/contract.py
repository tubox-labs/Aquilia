"""
Contract → JSON Schema bridge.

Uses ``aquilia.contracts.generate_schema`` as the authoritative source, then
enriches properties with Facet-level fragments (``facet.to_schema()``) for any
constraint keywords the base generator did not emit.
"""

from __future__ import annotations

import logging
from typing import Any

from aquilia.contracts import Contract, generate_schema

from ..faults import SchemaResolutionFault

logger = logging.getLogger("aquilia.specula.contract")


def _facet_fragment(facet: Any) -> dict[str, Any]:
    """Best-effort JSON Schema fragment for a single Facet instance."""
    try:
        fragment = facet.to_schema()
        if isinstance(fragment, dict):
            return fragment
    except Exception:  # noqa: BLE001 — facet schema is best-effort enrichment
        pass
    return {}


def contract_to_schema(
    contract_cls: type[Contract],
    *,
    projection: str | None = None,
    mode: str = "output",
) -> dict[str, Any]:
    """
    Convert an Aquilia Contract to an OpenAPI 3.1.0 schema dict.

    Args:
        contract_cls: The Contract subclass to convert.
        projection: Named projection (None = default = all fields).
        mode: ``"output"`` (response schema) or ``"input"`` (request body schema).

    Returns:
        JSON Schema dict.

    Raises:
        SchemaResolutionFault: If the Contract cannot be converted.
    """
    try:
        schema = generate_schema(contract_cls, projection=projection, mode=mode)
    except Exception as exc:
        raise SchemaResolutionFault(
            f"Cannot generate schema for Contract '{contract_cls.__name__}': {exc}",
            detail={"contract": contract_cls.__name__, "projection": projection, "mode": mode},
        ) from exc

    # Enrich with Facet-level constraints the base generator may not emit
    # (format, enum, pattern, minLength, readOnly/writeOnly, ...).
    facets = getattr(contract_cls, "_all_facets", {}) or {}
    properties = schema.get("properties", {})
    for name, facet in facets.items():
        if name not in properties:
            continue
        fragment = _facet_fragment(facet)
        for key, value in fragment.items():
            properties[name].setdefault(key, value)
        if getattr(facet, "read_only", False):
            properties[name].setdefault("readOnly", True)
        if getattr(facet, "write_only", False):
            properties[name].setdefault("writeOnly", True)

    return schema


def contract_components(
    *contract_classes: type[Contract],
    include_projections: bool = True,
) -> dict[str, dict[str, Any]]:
    """
    Produce the ``components.schemas`` dict for a set of Contracts.

    For each Contract generates:
      - ``{Name}``        — output (response) schema
      - ``{Name}Input``   — input (request body) schema
      - ``{Name}_{proj}`` — per-projection schemas (if ``include_projections``)
    """
    schemas: dict[str, dict[str, Any]] = {}
    for cls in contract_classes:
        name = cls.__name__
        schemas[name] = contract_to_schema(cls, mode="output")
        schemas[f"{name}Input"] = contract_to_schema(cls, mode="input")

        if include_projections:
            projections = getattr(cls, "_projections", None)
            available = getattr(projections, "available", ()) if projections else ()
            for proj in available:
                if proj == "__all__":
                    continue
                try:
                    schemas[f"{name}_{proj}"] = contract_to_schema(cls, projection=proj, mode="output")
                except SchemaResolutionFault:
                    logger.warning("Specula: skipping unresolvable projection %s.%s", name, proj)
    return schemas
