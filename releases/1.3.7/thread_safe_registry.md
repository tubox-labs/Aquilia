# Thread-Safe ModelRegistry & Cache Invalidation

Aquilia v1.3.7 refactors `ModelRegistry` (`aquilia.models.registry.ModelRegistry`) to introduce **full thread safety** via a re-entrant lock (`threading.RLock`) and automated **reverse-relation cache invalidation**.

---

## Why It Changed

In multi-threaded ASGI server configurations, worker threads or background tasks may dynamically import modules, execute testing fixtures, or register models concurrently. 

Previously, `ModelRegistry` maintained shared dictionaries (`_models` and `_app_models`) without thread synchronization:
- Concurrent calls to `ModelRegistry.register()` during app startup or dynamic module loading could cause dictionary mutation race conditions (`RuntimeError: dictionary changed size during iteration`).
- Foreign key resolution (`_resolve_relations()`) running in one thread while another registered a new model could lead to incomplete or corrupted foreign key mapping.
- Models lazily cached their reverse foreign key relationships (`_reverse_fk_cache` and `_reverse_relation_cache`). When test suites or dynamic reloads registered new models pointing back to existing models, the existing models held onto stale, un-updated reverse relationship caches.

---

## Architecture & Implementation

### 1. Re-Entrant Lock Guard (`threading.RLock`)

`ModelRegistry` now owns a class-level `_lock = threading.RLock()`. Re-entrant locking ensures that nested registry calls (e.g. `register()` calling `_resolve_relations()`, which queries registered models) can acquire the lock on the same thread without deadlocks.

Thread locks guard every public and internal operation:
- `ModelRegistry.register(model_cls)`
- `ModelRegistry.reset()`
- `ModelRegistry.set_database(db)`
- `ModelRegistry.get_database()`
- `ModelRegistry.get_models(app_label)`
- `ModelRegistry.get_model(name, app_label)`
- `ModelRegistry._resolve_relations()`
- `ModelRegistry.create_tables(db, app_label)`
- `ModelRegistry.drop_tables(db, app_label)`

```python
class ModelRegistry:
    _models: dict[str, type[Model]] = {}
    _db: AquiliaDatabase | None = None
    _app_models: dict[str, dict[str, type[Model]]] = {}
    _lock: threading.RLock = threading.RLock()

    @classmethod
    def register(cls, model_cls: type[Model]) -> None:
        with cls._lock:
            # 1. Update global lookups
            # 2. Invalidate reverse relation caches on existing models
            # 3. Resolve pending string foreign keys
            ...
```

### 2. Reverse Relation Cache Invalidation

When a new model is registered or the registry is reset, `ModelRegistry` automatically calls `_clear_reverse_relation_caches()` on all registered `Model` subclasses.

```python
# In aquilia.models.base.Model
@classmethod
def _clear_reverse_relation_caches(cls) -> None:
    """Clear cached reverse FK references and relation maps on this class."""
    cls._reverse_fk_cache = None
    cls._reverse_relation_cache = None
```

---

## Code Examples

### Multi-Threaded Model Registration (Concurrent Safety)

```python
import threading
from aquilia.models import Model, ModelRegistry, fields

def define_and_register(name: str):
    class DynamicUser(Model):
        table = f"users_{name}"
        username = fields.TextField()

    # Thread-safe registration under high concurrency
    ModelRegistry.register(DynamicUser)

threads = [
    threading.Thread(target=define_and_register, args=(f"worker_{i}",))
    for i in range(20)
]
for t in threads:
    t.start()
for t in threads:
    t.join()

assert len(ModelRegistry.get_models()) >= 20
```

---

## Performance Considerations

The performance impact of `threading.RLock` acquisition for model lookups is negligible (sub-microsecond), while completely eliminating data race crashes in multi-threaded application servers or test runners.
