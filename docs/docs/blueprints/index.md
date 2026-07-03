---
title: "Blueprints Overview"
description: "Declaring models-to-world contracts in Aquilia"
icon: lucide/layout
---
## Overview

!!! info
    Evidence: `aquilia/blueprints/__init__.py:4-7`


An Aquilia Blueprint declares the data contract between a data model and the outside world. It specifies how incoming payloads are cast into Python types, verified for integrity (sealing), and persisted back (imprinting), as well as how outbound instances are mapped into dictionary representations (molding) for rendering.

---

## Core Concepts

- **[Defining Blueprints](defining-blueprints.md)**: Creating classes inheriting from `Blueprint` with a nested `Spec` configuration class.
- **[Facets](facets.md)**: Declaring field types and validation rules using built-in validators like `TextFacet`, `IntFacet`, `DateTimeFacet`, and `Computed`.
- **[Field Annotations](field-annotations.md)**: Using type annotations with `Field()` and `@computed` for a clean, descriptor-driven coding style.
- **[Projections](projections.md)**: Defining named subsets of fields (e.g., `"summary"`, `"detail"`) to serialize different shapes of the same blueprint.
- **[Lenses](lenses.md)**: Mapping nested database relationships with built-in depth control, cycle prevention, and primary key fallback.
- **[Wards & Cross-Field Validation](ward.md)**: Declaring multi-field validation constraints using the `@ward` decorator.
- **[Lifecycle: Cast, Seal & Imprint](casting-sealing.md)**: Understanding how data moves through casting (type checking), sealing (integrity checks), and imprinting (saving).
- **[Sigil & FieldSpec](sigil.md)**: Declaring low-level field spec templates and structural mapping rules.
- **[Blueprint Unions](blueprint-union.md)**: Supporting discriminated unions and polymorphic API responses.
- **[Integration Helpers](integration.md)**: Resolving and binding Blueprints to HTTP requests and controller responses.
- **[Schema Generation](schema-generation.md)**: Compiling Blueprints into JSON Schema and OpenAPI schemas.
- **[Blueprint Exceptions](exceptions.md)**: Troubleshooting cast, seal, imprint, projection, and lens failures.
