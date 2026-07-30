# Aquilia v1.3.7 Release Notes — "Thread Sentinel"

Aquilia v1.3.7 introduces **Thread-Safe Model Registration & Descriptor Access**, **Type-Annotated Nested Contract Facets**, **Multi-Dialect Database Field Conversions**, and **Comprehensive 10-Point Standard Docstrings** across core Contract primitives.

Before this release, concurrent multi-threaded execution could experience subtle race conditions when registering models or accessing manager descriptors on model subclasses. Furthermore, imprinting contracts back into ORM models containing `EnumField` or `CompositeField` raised a `TypeError` due to missing dialect parameters, and nested contracts required verbose `NestedContractFacet` explicit declarations rather than standard Python type hints.

This release addresses all concurrency vulnerabilities with re-entrant locking (`threading.RLock`) in `ModelRegistry`, implements thread-isolated descriptor binding copies in `BaseManager`, enables type hint introspection for `NestedContractFacet`, extends dialect support across all ORM field conversions, and adds industry-grade 10-point documentation to the entire Contracts subsystem.

---

## Table of Contents

1. [Thread-Safe Model Registry](thread_safe_registry.md)
   - `ModelRegistry` thread safety via `threading.RLock`
   - Re-entrant locking strategy across registration, lookup, reset, and DDL
   - Reverse relation cache invalidation (`_clear_reverse_relation_caches()`)
2. [Manager Descriptor Thread Safety](manager_descriptor_thread_safety.md)
   - Subclass manager lookup isolation via bound shallow copies (`copy.copy`)
   - Strict descriptor access rules (`ManagerInstanceAccessFault`)
3. [Nested Contract Type Hint Annotations](nested_contract_annotations.md)
   - Python type hint introspection for `NestedContractFacet`
   - Support for `NestedContractFacet[SubContract]`, `SubContract`, and `list[...]`
4. [Multi-Dialect Field Conversions](field_dialect_support.md)
   - `dialect` parameter support in `EnumField.to_db()` and `CompositeField.to_db()`
   - Seamless contract imprinting (`contract.imprint()`) across SQLite, Postgres, MySQL, and Oracle
5. [Contract Standardized Docstrings](contract_docstrings.md)
   - 10-point industry docstring coverage across `facets.py`, `exceptions.py`, `integration.py`, `lenses.py`, `pipeline.py`, `projections.py`, `schema.py`, and `ward.py`
6. [Bug Fixes](bugfixes.md)
   - Critical fixes in model imprinting, registry concurrency, and manager descriptor binding
7. [Migration Guide](migration.md)
   - Upgrade checklist, compatibility notes, and zero-breaking-change guarantees

---

## Highlights

### Thread-Safe ModelRegistry & Reverse-Relation Invalidation

All global model registry operations are now fully thread-safe, guarded by a re-entrant `threading.RLock`. Additionally, registering new models or resetting the registry automatically invalidates lazily-cached reverse foreign key lookups across all registered models.

```python
import threading
from aquilia.models import ModelRegistry

def worker_thread(model_cls):
    # Safe concurrent registration across worker threads
    ModelRegistry.register(model_cls)
```

### Thread-Isolated Subclass Managers

`BaseManager.__get__()` now creates a thread-isolated bound shallow copy when accessed on model subclasses, ensuring concurrent queries on inherited managers never corrupt shared manager state.

```python
class BaseItem(Model):
    objects = Manager()

class ConcreteItem(BaseItem):
    pass

# Accessing SubModel.objects dynamically binds to SubModel safely in multi-threaded environments
items = await ConcreteItem.objects.all()
```

### Type-Annotated Nested Contracts

Declare nested contract structures cleanly using standard Python type annotations. `ContractMeta` automatically wraps direct contract classes or `NestedContractFacet[...]` annotations.

```python
class NameContract(Contract):
    first_name: typing.Annotated[str, Facet.text(min_length=1) >> strip]
    last_name: typing.Annotated[str, Facet.text(min_length=1) >> strip]

class UserRegistrationContract(Contract[UserModel]):
    # Modern Python type annotation syntax:
    name: NameContract
    aliases: list[NameContract]
```

### Multi-Dialect Field Support in Contract Imprinting

`EnumField.to_db()` and `CompositeField.to_db()` now accept the `dialect` keyword argument (defaulting to `"sqlite"`), preventing runtime `TypeError` exceptions during `contract.imprint()`.

```python
field = EnumField(enum_class=UserStatus, store_name=False)
field.to_db(UserStatus.ACTIVE, dialect="postgresql")  # -> 'active'
```

---

## Summary of Changes

| Subsystem | Change | Impact |
|---|---|---|
| `aquilia.models.registry` | `threading.RLock` guarding all registry methods; reverse relation cache invalidation | Prevents race conditions during concurrent model registration & reload |
| `aquilia.models.manager` | `BaseManager.__get__` creates bound shallow copies for subclasses | Guarantees thread isolation when accessing managers on derived models |
| `aquilia.models.fields` | `EnumField` & `CompositeField` accept `dialect` in `to_db()` | Fixes contract `imprint()` crashes on models with Enum/Composite fields |
| `aquilia.contracts` | `ContractMeta` introspects type hints for `NestedContractFacet` | Allows clean Python type hint syntax for nested contract definitions |
| `aquilia.contracts` | 10-point standard docstrings across all facet & core contract modules | Full IDE intellisense, architectural clarity, and documentation integrity |

Check the [Migration Guide](migration.md) for full details on upgrading to v1.3.7.
