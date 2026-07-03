---
title: "Introduction"
description: "Getting started with Aquilia Controller and Blueprints modules"
icon: lucide/book-marked
---## What is Aquilia?

Aquilia is a **production-ready async Python web framework** designed for seamless developer experience. It provides deep, complete integration of several advanced components to build robust applications.

As defined in the framework initialization ([aquilia/__init__.py](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/__init__.py#L2-L15)), Aquilia integrates the following modules:
*   **Aquilary**: Manifest-driven app registry with dependency resolution.
*   **Flow**: Typed flow-first routing with composable pipelines.
*   **DI**: Scoped dependency injection with lifecycle management.
*   **Sessions**: Cryptographic session management with policies.
*   **Auth**: OAuth2/OIDC, MFA, RBAC/ABAC authorization.
*   **Faults**: Structured error handling with fault domains.
*   **Middleware**: Composable middleware with effect awareness.
*   **Patterns**: Auto-fix, retry, and circuit breaker patterns.

---

## What These Docs Cover

These documentation sections focus specifically on two core modules of the Aquilia ecosystem:

### 1. Controllers (First-Class Class-Based Routing)
The **Controller System** introduces a class-based architecture that replaces function-based `@flow` handlers ([aquilia/controller/__init__.py](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/__init__.py#L2-L6)).

Key features of Aquilia Controllers include:
*   **Manifest-first**: Declared in `module.aq` ([aquilia/controller/__init__.py:8](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/__init__.py#L8)).
*   **DI-first**: Class constructor and method parameter dependency injection ([aquilia/controller/__init__.py:9](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/__init__.py#L9)).
*   **Pipeline-first**: Class-level and method-level pipelines ([aquilia/controller/__init__.py:10](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/__init__.py#L10)).
*   **Static-first**: Metadata extraction at compile time with zero import-time side effects ([aquilia/controller/__init__.py:11-12](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/__init__.py#L11-L12)).

!!! info
    Class-based Controllers leverage HTTP verb decorators like `@GET`, `@POST`, and `@PUT` for explicit endpoint definitions ([aquilia/controller/__init__.py:40-52](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/__init__.py#L40-L52)).


### 2. Blueprints (Model ↔ World Contracts)
The **Blueprints System** provides first-class contracts between internal models and the outside world ([aquilia/blueprints/__init__.py](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/__init__.py#L2-L8)). 

A Blueprint specifies:
*   **Facets**: What the world sees (e.g. `TextFacet`, `IntFacet`, `BoolFacet`).
*   **Projections**: Named subsets of data (e.g. `summary` or `detail` views).
*   **Casts**: How inbound data enters.
*   **Seals**: How integrity and validation are enforced.
*   **Imprints**: How validated data is written back to the model.

---

## Navigation Guide

To help you get started quickly, we recommend navigating the documentation in the following order:

1.  **Getting Started** (This Section)
    *   [Introduction](index.md): Overview of the framework.
    *   [Core Concepts](concepts.md): Understanding the fundamental architectural blocks.
    *   [Quick Start](quick-start.md): Build your first controller and blueprint.
2.  **Controller Guide**
    *   Learn about routing, HTTP decorators, dependency injection, exception filters, pagination, and OpenAPI schema generation.
3.  **Blueprints Guide**
    *   Learn how to define schemas, declare facets, build projections, use lenses, and handle input validation and database imprinting.
