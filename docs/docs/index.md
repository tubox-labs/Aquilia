---
title: "Aquilia Documentation"
description: "Welcome to the Aquilia framework documentation"
icon: lucide/home
---
## Overview

Welcome to the documentation for Aquilia, a Python web framework. This documentation covers two primary architectural modules of the framework:

1. **[Controllers](controller/index.md)**: A class-based, dependency-injection-first request routing and execution layer that replaces traditional function-based handlers.
2. **[Contracts](contracts/index.md)**: A model-to-world contract system that declares data casting, sealing (validation), and imprinting (persistence) flows.

---

## Key Modules

### Controller Module
!!! info
    Evidence: `aquilia/controller/__init__.py:4-12`


The Controller module provides class-based routing, compile-time metadata extraction, automatic parameter validation, content negotiation, pagination, filtering, and rate limiting.

### Contracts Module
!!! info
    Evidence: `aquilia/contracts/__init__.py:4-7`


The Contracts module provides a system to define declarative schemas (specs), input type coercion (casts), cross-field validators (wards), relationship traversal (lenses), dynamic sub-selections (projections), and serialization mappings.
