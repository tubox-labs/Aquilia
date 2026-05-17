# Blueprints Documentation

This directory is the professional documentation set for `blueprints`. It is implementation-driven and aligned with the current source files under `aquilia/blueprints`.

## What This Covers

The contract system for casting inbound data, sealing validated values, molding outbound data, projections, lenses, and model imprinting.

## Source Files Read

- `aquilia/blueprints/__init__.py`: Aquilia Blueprints -- first-class model↔world contracts.
- `aquilia/blueprints/annotations.py`: Aquilia Blueprint Annotations -- type-annotation-driven schema declaration.
- `aquilia/blueprints/core.py`: Aquilia Blueprint Core -- the Blueprint metaclass and base class.
- `aquilia/blueprints/exceptions.py`: Aquilia Blueprint Exceptions -- Fault-domain-integrated error hierarchy.
- `aquilia/blueprints/facets.py`: Aquilia Blueprint Facets -- the field-level primitives of a Blueprint.
- `aquilia/blueprints/integration.py`: Aquilia Blueprint Integration -- hooks into Controller, DI, Request/Response.
- `aquilia/blueprints/lenses.py`: Aquilia Blueprint Lenses -- depth-controlled relational views.
- `aquilia/blueprints/projections.py`: Aquilia Blueprint Projections -- named, reusable field subsets.
- `aquilia/blueprints/schema.py`: Aquilia Blueprint Schema -- OpenAPI/JSON Schema generation.

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

- Python files: 9
- Public classes: 41
- Configuration or dataclass-like types: 0
- Public functions: 10
- Constants detected: 7

## Fast Start

```python
from aquilia.blueprints import Blueprint

class CreateUser(Blueprint):
    email: str
    name: str
    active: bool = True

    class Spec:
        extra_fields = "reject"

    def seal_email(self, data):
        email = data.get("email", "").strip().lower()
        if "@" not in email:
            self.reject("email", "Email address is required")
        data["email"] = email

bp = CreateUser(data={"email": "ADA@example.com", "name": "Ada"})
assert bp.is_sealed() is True
payload = bp.validated_data
```

## Read Next

Start with `architecture.md` if you are learning how the subsystem fits into runtime boot. Use `api-reference.md` when you need exact methods, datatypes, and class fields. Use `examples.md` for copyable patterns that match the current code.
