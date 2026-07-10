---
name: aquilia-contract-validation
description: "Build Aquilia Contract validation, schema, projection, lens, facet, and request/response molding workflows. Use for Contract classes, facets, sealing/casting, OpenAPI schema generation, request_contract/response_contract, and model-world contracts."
---

# Aquilia Contract Validation

## Purpose
Use Aquilia Contracts for request validation, response shaping, OpenAPI schemas, and model-world contracts.

## Trigger Conditions
Use for data validation, typed request bodies, response projections, facets, lenses, annotations, schema generation, `request_contract`, `response_contract`, and Contract security issues.

## Inputs
- Contract fields/facets, required/optional behavior, projection rules, request data, response object/data, and OpenAPI requirements.

## Execution Flow
1. Define `Contract` classes with facets from `aquilia.contracts`.
2. In controllers, pass Contract classes to route decorators or instantiate explicitly with request data.
3. Seal/cast input before handing data to services.
4. Use projections/lenses for response shaping when returning subsets or derived views.
5. Generate schemas through contract schema integration for OpenAPI.

## Constraints
- Do not treat Contracts as ORM models; they are validation/projection contracts.
- Validate and seal user input before service mutation.
- Do not leak hidden/write-only fields in response projections.

## Implementation Anchors
`aquilia/contracts/`, `aquilia/controller/decorators.py`, `aquilia/controller/engine.py`, `aquilia/patterns/openapi.py`, `tests/test_contract_*.py`, `examples/rest_api_contract/`, `examples/crud_app/modules/projects/contracts.py`.

## Examples
- Use `ProjectCreateContract(data=await ctx.json())` then `await contract.is_sealed_async()`.
- Add `request_contract=CreateUserContract` to `@POST`.
- Return a projected response with read-only and hidden fields respected.

## Failure Handling
Cast/seal/projection failures should map to contract faults. If schemas are wrong, inspect facet definitions and schema generator output. If sensitive fields leak, audit projection and facet annotations.
