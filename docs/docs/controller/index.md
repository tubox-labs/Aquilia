---
title: "Controller Module Overview"
description: "Overview of class-based Controller architecture in Aquilia"
icon: lucide/layers
---
## Overview

!!! info
    Evidence: `aquilia/controller/__init__.py:4-12`


The Aquilia Controller system provides a class-based architecture for request handling, replacing traditional function-based `@flow` handlers.

### Key Features

- **Manifest-first**: Controllers are registered and declared in the module manifest (`module.aq`).
- **DI-first**: Supports dependency injection in both constructors (`__init__`) and handler methods.
- **Pipeline-first**: Middleware and request processing pipelines can be declared at both the class level and method level.
- **Static-first**: Metadata is parsed and extracted at compile time rather than at import time or request time.
- **Zero import-time side effects**: Importing controller files does not execute routing or setup side effects.

---

## Module Structure

The controller system consists of several components:

- **[Defining Controllers](defining-controllers.md)**: Inheriting from `Controller` and using configuration attributes.
- **[Request Context](request-context.md)**: Utilizing the `RequestCtx` object to access parameters, body data, and request state.
- **[HTTP Decorators](http-decorators.md)**: Decorating handler methods using HTTP verb decorators (`@GET`, `@POST`, `@PUT`, `@DELETE`, etc.).
- **[Lifecycle Hooks](lifecycle-hooks.md)**: Injecting logic into controller initialization (`on_startup`, `on_shutdown`) and request processing (`on_request`, `on_response`).
- **[Instantiation Modes](instantiation-modes.md)**: Managing lifecycle lifespans (singleton vs per-request).
- **[Exception Filters](exception-filters.md)**: Catching and normalizing errors via `ExceptionFilter`.
- **[Interceptors](interceptors.md)**: Wrapping request handling with before/after logic.
- **[Throttle](throttle.md)**: Applying sliding-window rate limiting.
- **[Pagination](pagination.md)**: Configuring pagination strategies.
- **[Filtering](filtering.md)**: Performing list search, ordering, and field-based filtering.
- **[Content Negotiation](renderers.md)**: Format-aware response rendering.
- **[Validation](validation.md)**: Validating request body data using `validate_body`.
- **[OpenAPI Docs](openapi.md)**: Generating interactive Swagger UI and ReDoc pages.
- **[Versioning](versioning.md)**: Route-level and class-level API versioning.
