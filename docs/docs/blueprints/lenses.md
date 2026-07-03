---
title: "Lenses"
description: "Modeling nested resource mappings and relationship traversal in Blueprints"
icon: lucide/glasses
---A [Lens](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/lenses.py#L26-L184) is a relational facet that views related data through another [Blueprint](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/core.py#L826-L2075). It lets a blueprint expose related model data with depth control, cycle detection, and projection selection.

### 1. What is a Lens? (Optical Metaphor)

The term **Lens** is used as an optical metaphor because it provides a focused *view* into related data, similar to how an optical lens adjusts focus, zoom, and magnification to show nested objects clearly ([lenses.py:L7-10](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/lenses.py#L7-L10)). A [Lens](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/lenses.py#L26-L184) inherits from [Facet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/facets.py#L228-L457) ([lenses.py:L26](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/lenses.py#L26)) and serves as a depth-controlled relational view.

---

### 2. Constructor Parameters

The [Lens](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/lenses.py#L26-L184) constructor accepts the following parameters ([lenses.py:L52-59](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/lenses.py#L52-L59)):

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `target` | `type[Blueprint] \| _ProjectedRef \| None` | `None` | The target Blueprint class or subscripted projection used to format the related data ([lenses.py:L54](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/lenses.py#L54)). |
| `many` | `bool` | `False` | When `True`, the lens expects an iterable sequence of objects and molds each item individually ([lenses.py:L56](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/lenses.py#L56)). |
| `depth` | `int` | `3` | Maximum nesting depth limit for resolving related lenses before falling back to ID representation ([lenses.py:L57](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/lenses.py#L57)). |
| `projection` | `str \| None` | `None` | Named projection of the target Blueprint to restrict/change the exposed fields ([lenses.py:L58](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/lenses.py#L58)). |
| `source` | `str \| None` | `None` | (Keyword-only from `**kwargs`) The model attribute or dotted path to extract the relation data from ([lenses.py:L59](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/lenses.py#L59)). |
| `read_only` | `bool` | `True` | (Keyword-only from `**kwargs`) Determines if the field is read-only. Lenses default to `True` ([lenses.py:L61](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/lenses.py#L61)). |

```python
# Lenses are read-only by default (lenses.py:L61)
kwargs.setdefault("read_only", True)
super().__init__(**kwargs)
```

---

### 3. Subscript Projections & `_ProjectedRef`

When specifying target Blueprints, you can select specific projections using Python's subscript syntax (e.g., `UserBlueprint["public"]`).

Under the hood, this subscript returns an instance of [_ProjectedRef](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/lenses.py#L187-L201) ([lenses.py:L187-201](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/lenses.py#L187-L201)).
- The [_ProjectedRef](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/lenses.py#L187-L201) class stores `blueprint_cls` and the string `projection` name ([lenses.py:L194-198](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/lenses.py#L194-L198)).
- The [Lens](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/lenses.py#L26-L184) constructor unpacks it automatically ([lenses.py:L65-70](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/lenses.py#L65-L70)):

```python
if isinstance(target, _ProjectedRef):
    self._target_cls = target.blueprint_cls
    self._projection = target.projection
else:
    self._target_cls = target
    self._projection = projection
```

---

### 4. Depth Control

Lenses prevent infinite recursion by enforcing a maximum recursion depth limit, configured via `depth` constructor parameter (stored as `self.max_depth`) ([lenses.py:L73](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/lenses.py#L73)).

- The `mold()` method takes an internal `_depth` parameter tracking the current nesting level ([lenses.py:L93](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/lenses.py#L93)).
- During recursive resolution, `_depth` increments by 1: `_depth=_depth + 1` ([lenses.py:L132-133](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/lenses.py#L132-L133)).
- Once `_depth >= self.max_depth`, resolution halts and falls back to primary key extraction ([lenses.py:L118-122](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/lenses.py#L118-L122)):

```python
if _depth >= self.max_depth:
    if self.many:
        return [self._pk_fallback(item) for item in value]
    return self._pk_fallback(value)
```

---

### 5. Cycle Detection

To prevent cyclic references where blueprints link back to themselves (either directly or transitively), [Lens](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/lenses.py#L26-L184) implements a cycle-detection mechanism.

- The `mold()` method tracks traversed Blueprint classes via a `_seen` set ([lenses.py:L93](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/lenses.py#L93)).
- A unique ID for the target class is calculated: `target_id = id(self._target_cls)` ([lenses.py:L109](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/lenses.py#L109)).
- If `target_id` is already present in `_seen`, the engine raises a [LensCycleFault](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/exceptions.py#L141-L150) ([lenses.py:L110-115](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/lenses.py#L110-L115)):

```python
if target_id in _seen:
    raise LensCycleFault(
        [cls.__name__ for cls in _seen] + [self._target_cls.__name__]
        if hasattr(self._target_cls, "__name__")
        else ["<unknown>"]
    )
```

- If no cycle is found, the current class is added to the set and passed to the next resolution level ([lenses.py:L124](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/lenses.py#L124)):

```python
new_seen = _seen | {target_id}
```

---

### 6. Primary Key Fallback

When depth limits are exceeded or the target Blueprint is omitted, [Lens](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/lenses.py#L26-L184) attempts to extract the primary identifier via the private `_pk_fallback()` method ([lenses.py:L145-154](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/lenses.py#L145-L154)).

- Returns `None` if the input is `None` ([lenses.py:L147-148](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/lenses.py#L147-L148)).
- Looks for `"id"` or `"pk"` keys if the value is a dictionary ([lenses.py:L149-150](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/lenses.py#L149-L150)).
- Checks for `pk` attribute, falling back to `id` attribute if `pk` is absent ([lenses.py:L151-154](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/lenses.py#L151-L154)).

```python
@staticmethod
def _pk_fallback(instance: Any) -> Any:
    if instance is None:
        return None
    if isinstance(instance, dict):
        return instance.get("id", instance.get("pk"))
    pk = getattr(instance, "pk", None)
    if pk is not None:
        return pk
    return getattr(instance, "id", None)
```

---

### 7. Many=True — List Molding

Setting `many=True` configures the lens to process collections of related objects ([lenses.py:L44](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/lenses.py#L44)).

- Evaluates value elements by invoking `_mold_single()` on each item ([lenses.py:L126-133](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/lenses.py#L126-L133)):

```python
if self.many:
    items = value if not hasattr(value, "__aiter__") else value
    ...
    return [self._mold_single(item, _depth=_depth + 1, _seen=new_seen) for item in items]
```

- When the maximum depth is reached, it transforms the entire array into primary keys: `[self._pk_fallback(item) for item in value]` ([lenses.py:L120-121](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/lenses.py#L120-L121)).

---

### 8. Manager/QuerySet Handling

To prevent accidental synchronous evaluation of lazy database relationships (like Django's `RelatedManager` or `QuerySet`), [Lens](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/lenses.py#L26-L184) performs a safety check inside `mold()` ([lenses.py:L128-131](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/lenses.py#L128-L131)):

```python
if hasattr(items, "all"):
    # It's a manager/queryset -- can't iterate sync
    # Return empty; async path should be used
    return []
```

!!! warning
    Attempting to evaluate a queryset/manager synchronously will yield an empty list `[]`. Ensure you await or execute these queries asynchronously before passing the results to the Blueprint serialization context.


---

### 9. to_schema() — JSON Schema $ref Generation

The `to_schema()` method generates standard JSON Schema structures utilizing `$ref` pointers targeting resolved Blueprints.

- Returns `{"type": "object"}` if the target blueprint class is not specified ([lenses.py:L172-173](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/lenses.py#L172-L173)).
- Appends projection names to reference tags when present ([lenses.py:L175-177](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/lenses.py#L175-L177)):
  ```python
  ref_name = self._target_cls.__name__
  if self._projection:
      ref_name = f"{ref_name}_{self._projection}"
  ```
- Yields a nested `array` block for `many=True` lenses ([lenses.py:L179-183](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/lenses.py#L179-L183)):
  ```python
  return {
      "type": "array",
      "items": {"$ref": f"#/components/schemas/{ref_name}"},
  }
  ```
- Yields direct `$ref` pointers for singular relationships ([lenses.py:L184](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/lenses.py#L184)):
  ```python
  return {"$ref": f"#/components/schemas/{ref_name}"}
  ```

---

### 10. extract() — Dotted Source Path Support

The `extract()` method fetches fields from original models, supporting dotted paths (e.g., `author.profile.avatar`) ([lenses.py:L156-168](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/lenses.py#L156-L168)).

- Returns the model itself if `source` is set to `"*"` ([lenses.py:L158-159](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/lenses.py#L158-L159)).
- Splits paths by `.` and traverses attributes/dictionaries step-by-step ([lenses.py:L162-168](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/lenses.py#L162-L168)):

```python
parts = self.source.split(".") if self.source else []
obj = instance
for part in parts:
    if obj is None:
        return None
    obj = obj.get(part) if isinstance(obj, dict) else getattr(obj, part, None)
return obj
```

---

### 11. bind() — Model FK Resolution

When a [Lens](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/lenses.py#L26-L184) is bound to a blueprint using the `bind()` method ([lenses.py:L79-91](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/lenses.py#L79-L91)), it matches standard ORM fields automatically.

If no `source` is explicitly configured, it inspects the Blueprint's specs and underlying model attributes:
- Accesses metadata fields using `getattr(spec.model, "_fields", {})` ([lenses.py:L85](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/lenses.py#L85)).
- If a model field matches the lens attribute name and has a `to` property (denoting a Foreign Key or Many-to-Many relation), the relationship attribute name is matched as the source ([lenses.py:L86-91](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/lenses.py#L86-L91)).

---

### 12. Code Examples

Below are practical code patterns showing how to leverage nested relationship molding and projection selection.

#### Example A: Traversal & Depth Control

In this setup, nesting depth limits ensure we don't output deeply nested payloads unless required.

```python
from aquilia.blueprints.core import Blueprint
from aquilia.blueprints.lenses import Lens

class AuthorBlueprint(Blueprint):
    # Traverses the related Profile model
    profile = Lens(source="profile_details")
    # Traverses related books but halts at depth 1 (returning PKs)
    books = Lens(many=True, depth=1)

class ArticleBlueprint(Blueprint):
    title = str
    # Limits author traversal to a depth of 2
    author = Lens(AuthorBlueprint, depth=2)
```

#### Example B: Subscript Projections

Use named Blueprint projections to select a subset of related model fields during traversal.

```python
class UserBlueprint(Blueprint):
    id = int
    email = str
    
    # Define a projection that only serializes public info
    _projections = {
        "public": ["id"]
    }

class TeamBlueprint(Blueprint):
    name = str
    # Traverses related users using the "public" projection
    members = Lens(UserBlueprint["public"], many=True)
```
