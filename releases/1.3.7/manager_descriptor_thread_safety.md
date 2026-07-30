# Manager Descriptor Thread Safety & Subclass Binding

Aquilia v1.3.7 refactors `BaseManager` (`aquilia.models.manager.BaseManager`) descriptor access to guarantee **thread isolation** when accessing model managers across derived classes.

---

## Why It Changed

Model managers in Aquilia are attached as descriptors to model classes (e.g. `objects = Manager()`). In Python's descriptor protocol, accessing `Model.objects` calls `BaseManager.__get__(self, instance, owner)`.

Prior to v1.3.7:
- When a subclass inherited a manager from a base model (or when multiple worker threads accessed `SubModel.objects`), `__get__` re-assigned `self._model_cls = owner` directly on the shared `BaseManager` instance.
- In multi-threaded environments, if Thread A accessed `ParentModel.objects` while Thread B accessed `ChildModel.objects`, a race condition occurred where `_model_cls` on the shared manager instance could be mutated while Thread A was building a query. This caused queries in Thread A to target `ChildModel` instead of `ParentModel`.

---

## Architecture & Implementation

### 1. Bound Shallow Copy Protocol

In `BaseManager.__get__()`:
1. Instance access check: If `instance is not None`, raises `ManagerInstanceAccessFault` (blocking `user.objects` access).
2. Owner matching: If `owner` matches `self._model_cls` or `self._model_cls` is `None`, `self._model_cls` is set to `owner` and `self` is returned.
3. Subclass isolation: If accessed from a subclass (`owner != self._model_cls`), `BaseManager.__get__()` returns a **shallow copy** (`copy.copy(self)`) bound to `owner`.

```python
def __get__(self: M, instance: Any, owner: type) -> M:
    if instance is not None:
        from aquilia.faults.domains import ManagerInstanceAccessFault
        raise ManagerInstanceAccessFault(
            f"Manager '{self.__class__.__name__}' is non-accessible from "
            f"'{instance.__class__.__name__}' instance. Access it from the class instead."
        )

    if self._model_cls is None or self._model_cls is owner:
        self._model_cls = cast("type[TModel]", owner)
        return self

    # Subclass or different owner access -- return a bound copy for thread safety
    bound = copy.copy(self)
    bound._model_cls = cast("type[TModel]", owner)
    return bound
```

---

## Code Examples

### Subclass Manager Access in Multi-Threaded Environments

```python
import asyncio
from aquilia.models import Model, Manager, fields

class BaseContent(Model):
    table = "base_contents"
    title = fields.TextField()
    objects = Manager()

class Article(BaseContent):
    table = "articles"
    body = fields.TextField()

class Video(BaseContent):
    table = "videos"
    duration = fields.IntField()

async def concurrent_queries():
    # Concurrently query derived models without cross-thread manager state corruption
    article_task = asyncio.create_task(Article.objects.all())
    video_task = asyncio.create_task(Video.objects.all())
    await asyncio.gather(article_task, video_task)
```

---

## Behavioral Guarantees

- **Thread Safety**: Accessing managers across inheritance hierarchies produces distinct, thread-bound descriptors.
- **Instance Protection**: Accessing `instance.objects` continues to raise `ManagerInstanceAccessFault` deterministically.
