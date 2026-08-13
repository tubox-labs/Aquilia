# Contract Safety on Python 3.14 — v1.4.0b5

## Overview

Python 3.14 changes when some annotations are evaluated. `ContractMeta` reads `cls.__annotations__` during class construction so Aquilia can derive facets. That access can now execute deferred facet factories and raise validation faults inside the metaclass's introspection recovery block.

## Previous Behavior

The metaclass used broad exception suppression when reading and introspecting annotations. A `CastFault` raised by an unsafe facet constraint could be converted into a warning and the Contract class could continue without the intended field validation.

For security-sensitive constraints, that changes a definition error into silent acceptance.

## New Behavior

`CastFault` is explicitly re-raised in both annotation access and annotation introspection. Other resolution problems retain the existing compatibility behavior: Aquilia warns that introspection failed and continues where possible.

```python
try:
    cls_annotations = cls.__annotations__
except CastFault:
    raise
except Exception:
    pass
```

## ReDoS Example

```python
from aquilia.contracts import Contract, Field

class UnsafeSearch(Contract):
    query: str = Field(pattern=r"(a+)+")
```

The nested quantifier is rejected at class definition. This is consistent across supported Python versions, including 3.14.

## Breaking and Compatibility Notes

There is no public API change. A previously accepted class may now fail only if its facet definition was already invalid and the failure was being swallowed. Treat that as a security/correctness fix:

1. Read the `CastFault` message.
2. Replace the invalid constraint.
3. Do not catch the error simply to keep the unsafe class importable.

Unrelated unresolved forward references still use the established warning/fallback path.

## Performance

No additional annotation passes are introduced. The change only separates `CastFault` from generic exception recovery.

## Related Documentation

- aqdocx [Contract Annotations](/docs/contracts/annotations)
- aqdocx [Contract Faults](/docs/contracts/faults)
- [Migration Guide](migration.md)
