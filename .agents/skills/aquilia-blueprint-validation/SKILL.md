---
name: aquilia-blueprint-validation
description: "Build Aquilia Blueprint validation, schema, projection, lens, facet, and request/response molding workflows. Use for Blueprint classes, facets, sealing/casting, OpenAPI schema generation, request_blueprint/response_blueprint, and model-world contracts."
---

# Aquilia Blueprint Validation

## Purpose
Use Aquilia Blueprints for request validation, response shaping, OpenAPI schemas, and model-world contracts.

## Trigger Conditions
Use for data validation, typed request bodies, response projections, facets, lenses, annotations, schema generation, `request_blueprint`, `response_blueprint`, and Blueprint security issues.

## Inputs
- Blueprint fields/facets, required/optional behavior, projection rules, request data, response object/data, and OpenAPI requirements.

## Execution Flow
1. Define `Blueprint` classes with facets from `aquilia.blueprints`.
2. In controllers, pass Blueprint classes to route decorators or instantiate explicitly with request data.
3. Seal/cast input before handing data to services.
4. Use projections/lenses for response shaping when returning subsets or derived views.
5. Generate schemas through blueprint schema integration for OpenAPI.

## Constraints
- Do not treat Blueprints as ORM models; they are validation/projection contracts.
- Validate and seal user input before service mutation.
- Do not leak hidden/write-only fields in response projections.

## Implementation Anchors
`aquilia/blueprints/`, `aquilia/controller/decorators.py`, `aquilia/controller/engine.py`, `aquilia/patterns/openapi.py`, `tests/test_blueprint_*.py`, `examples/rest_api_blueprint/`, `examples/crud_app/modules/projects/blueprints.py`.

## Examples
- Use `ProjectCreateBlueprint(data=await ctx.json())` then `await blueprint.is_sealed_async()`.
- Add `request_blueprint=CreateUserBlueprint` to `@POST`.
- Return a projected response with read-only and hidden fields respected.

## Failure Handling
Cast/seal/projection failures should map to blueprint faults. If schemas are wrong, inspect facet definitions and schema generator output. If sensitive fields leak, audit projection and facet annotations.
