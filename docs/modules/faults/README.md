# Faults Documentation

This directory is the professional documentation set for `faults`. It is implementation-driven and aligned with the current source files under `aquilia/faults`.

## What This Covers

The structured fault system with domains, severity, recovery strategies, handlers, adapters, and typed subsystem errors.

## Source Files Read

- `aquilia/faults/__init__.py`: AquilaFaults - Production-grade fault handling system.
- `aquilia/faults/core.py`: AquilaFaults - Core types and fault taxonomy.
- `aquilia/faults/default_handlers.py`: AquilaFaults - Default Handlers.
- `aquilia/faults/domains.py`: AquilaFaults - Domain-specific fault types.
- `aquilia/faults/engine.py`: AquilaFaults - Fault Engine.
- `aquilia/faults/handlers.py`: AquilaFaults - Fault handlers.
- `aquilia/faults/integrations/__init__.py`: AquilaFaults - Subsystem Integrations.
- `aquilia/faults/integrations/di.py`: AquilaFaults - DI Integration.
- `aquilia/faults/integrations/flow.py`: AquilaFaults - Flow Engine Integration.
- `aquilia/faults/integrations/models.py`: AquilaFaults - Model/Database Integration.
- `aquilia/faults/integrations/registry.py`: AquilaFaults - Registry Integration.
- `aquilia/faults/integrations/routing.py`: AquilaFaults - Routing Integration.

## Document Map

- `architecture.md`: Runtime architecture and module boundaries
- `configuration.md`: Configuration entry points, datatypes, and precedence
- `api-reference.md`: Classes, methods, functions, constants, and data fields extracted from source
- `integration-guide.md`: How to wire the module into a real Aquilia application
- `cli-reference.md`: Command line surface and operational commands
- `edge-cases-and-limitations.md`: Known edge cases and implementation limits
- `troubleshooting.md`: Common failures and diagnosis steps
- `examples.md`: Code examples and usage patterns

## Public Surface Snapshot

- Python files: 12
- Public classes: 127
- Configuration or dataclass-like types: 6
- Public functions: 23
- Constants detected: 2

## Fast Start

```python
from aquilia.faults import Fault, FaultDomain, Severity

class CatalogFault(Fault):
    def __init__(self, sku: str):
        super().__init__(
            code="CATALOG_NOT_FOUND",
            message=f"Product {sku} was not found",
            domain=FaultDomain.MODEL,
            severity=Severity.WARNING,
            metadata={"sku": sku},
        )
```

## Read Next

Start with `architecture.md` if you are learning how the subsystem fits into runtime boot. Use `api-reference.md` when you need exact methods, datatypes, and class fields. Use `examples.md` for copyable patterns that match the current code.
