---
title: "Wards & Cross-Field Validation"
description: "Cross-field validation using @ward decorators in Aquilia Blueprints"
icon: lucide/shield
---
Wards are explicit cross-field validators in Aquilia Blueprints that are registered during class-body evaluation. They replace older, fragile method-name prefix scanning with structured metadata and decorators.

---

### What is a Ward?

A **Ward** is an explicit cross-field validator registered on an Aquilia [Blueprint](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/core.py#L826). As defined in [ward.py](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/ward.py), wards replace the legacy prefix-based scanning of `seal_*` or `async_seal_*` methods with an explicit decorator-driven registration system discovered once at class-body evaluation time (see [ward.py lines 2–6](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/ward.py#L2-L6)).

---

### Bare Decorator Usage: `@ward`

Using the decorator without arguments registers a synchronous ward method:

```python
from aquilia.blueprints import ward

class OrderBlueprint(Blueprint):
    @ward
    def total_matches_items(self, data):
        computed = sum(i.price * i.qty for i in data.items)
        if abs(computed - data.total) > 0.01:
            self.reject("total", f"Expected {computed}, got {data.total}")
```

#### Under the Hood
* When used as a bare decorator `@ward`, the [ward](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/ward.py#L57) class intercepts the method call during class evaluation via its `__new__` method (see [ward.py lines 80–90](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/ward.py#L80-L90)).
* It validates that the decorated object is indeed a callable (raising a `TypeError` if not).
* It registers validation metadata on the function under `fn.__ward_meta__` as `{"mode": "sync", "name": fn.__name__}` (see [ward.py line 88](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/ward.py#L88)).

---

### Parameterised Factory: `@ward(mode="async")`

When you need to perform validation that requires calling asynchronous APIs (such as checking a database or calling a remote service), you can parameterise the decorator:

```python
class OrderBlueprint(Blueprint):
    @ward(mode="async")
    async def discount_code_valid(self, data):
        if data.discount_code and not await lookup(data.discount_code):
            self.reject("discount_code", "Unknown code")
```

#### Under the Hood
* Calling `@ward(mode="async")` invokes `__new__` without a decorated function, returning a new instance of the [ward](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/ward.py#L57) class acting as a decorator factory (see [ward.py lines 91–95](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/ward.py#L91-L95)).
* The `mode` parameter is validated against the valid modes list, raising a `ValueError` if the specified mode is invalid.
* When the returned `ward` instance is subsequently called with the decorated function (`fn`), its `__call__` method attaches the `__ward_meta__` dictionary using the stored mode (see [ward.py lines 105–110](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/ward.py#L105-L110)).

---

### The `WardMethod` Dataclass

The metadata for each registered ward is stored in an instance of the [WardMethod](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/ward.py#L42-L47) class, a frozen, memory-optimized dataclass (using slots) defined in [ward.py lines 42–47](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/ward.py#L42-L47).

| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `name` | `str` |  | The name of the validator method. |
| `fn` | `object` |  | The actual validator callable/method object. |
| `mode` | `str` |  | The execution mode: either "sync" or "async". |


---

### Valid Validation Modes

The validation engine supports a restricted set of modes defined in the internal constant `_VALID_MODES` (see [ward.py line 54](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/ward.py#L54)):

* `"sync"`: Standard synchronous validation.
* `"async"`: Asynchronous validation (requires an event loop to resolve).

Any value passed to the decorator's `mode` parameter that is not in `_VALID_MODES` raises a `ValueError` during decoration (see [ward.py lines 81–82](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/ward.py#L81-L82)).

---

### Method Collection: `collect_ward_methods()`

During Blueprint class creation, all registered wards are harvested using the [collect_ward_methods](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/ward.py#L118) helper function (see [ward.py lines 118–199](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/ward.py#L118-L199)).

#### Inheritance and Override Semantics
1. **Inheritance Scan**: The function iterates through the base classes (`bases`) in Method Resolution Order (MRO) to collect inherited ward methods (see [ward.py lines 147–150](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/ward.py#L147-L150)).
2. **Namespace Scan**: It then scans the current class namespace for attributes decorated with `@ward` (identifiable by the `__ward_meta__` attribute) (see [ward.py lines 152–161](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/ward.py#L152-L161)).
3. **Override Mapping**: The inherited and own methods are merged. If a subclass defines a ward with the same name as an inherited ward, the subclass's version replaces (overrides) the parent's version in the merged dictionary (see [ward.py lines 182–185](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/ward.py#L182-L185)).

---

### Deprecation Notice: Legacy Prefix Scanning

Before explicit `@ward` registration, Aquilia automatically discovered cross-field validators by scanning for methods with the `seal_` or `async_seal_` prefix.

!!! warning "Deprecation Warning"
    The `seal_*/async_seal_*` prefix convention is deprecated (see [ward.py lines 163–180](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/ward.py#L163-L180)). Classes defining undecorated methods with these prefixes will emit a `DeprecationWarning` during class-body evaluation:

    ```
    DeprecationWarning: ClassName.method_name: seal_*/async_seal_* prefix convention is deprecated. Use @ward or @ward(mode='async') instead.
    ```


---

### Registration: Class Attribute `_ward_methods`

The list of collected [WardMethod](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/ward.py#L42-L47) descriptors is stored on the evaluated Blueprint class as a class attribute named `_ward_methods` (see [ward.py lines 148–150](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/ward.py#L148-L150)).

---

### Error Reporting via `self.reject()`

Within a ward method, validation failures are reported by calling `self.reject(field, message)`.

* **Usage in `ward.py`**: The decorator and module docstring examples call `self.reject(field, message)` to report specific validation errors (e.g., `self.reject("total", "...")` in [ward.py lines 17, 22](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/ward.py#L17)).
* **Actual Implementation**: "Unknown from inspected source" (the actual `self.reject()` method is not implemented or defined within [ward.py](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/ward.py), although its usage in validator methods is demonstrated in the module docstring on lines 17 and 22. According to [.cache/index_blueprints.json](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/.cache/index_blueprints.json#L125), `reject()` is a method on the base [Blueprint](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/core.py#L826) class defined in `aquilia/blueprints/core.py` at lines 1250–1260).

---

### Execution Order

When a blueprint is validated, wards are executed in a deterministic, stable order:
1. **Inherited Wards First**: Wards defined in parent base classes are run first, preserving MRO and definition order (see [ward.py lines 139–141, 191–193](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/ward.py#L139-L141)).
2. **Subclass Wards Second**: Wards defined directly on the subclass are run next in their order of definition (see [ward.py lines 141–142, 194–197](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/ward.py#L141-L142)).

---

### Code Examples

Below are comprehensive usage patterns for sync, async, and inherited wards:

#### 1. Synchronous Ward Method
```python
from aquilia.blueprints import Blueprint, ward

class RegistrationBlueprint(Blueprint):
    # Registering a synchronous ward using the bare decorator
    @ward
    def validate_password_match(self, data):
        if data.password != data.password_confirmation:
            self.reject("password_confirmation", "Passwords do not match")
```

#### 2. Asynchronous Ward Method
```python
from aquilia.blueprints import Blueprint, ward

class UserBlueprint(Blueprint):
    # Registering an asynchronous ward using the parameterised decorator factory
    @ward(mode="async")
    async def validate_unique_email(self, data):
        if data.email and not await db.is_email_unique(data.email):
            self.reject("email", "Email address is already registered")
```

#### 3. Inherited and Overridden Wards
```python
from aquilia.blueprints import Blueprint, ward

class BaseOrderBlueprint(Blueprint):
    @ward
    def validate_pricing(self, data):
        # Base pricing check
        if data.total < 0:
            self.reject("total", "Total cannot be negative")

    @ward
    def validate_shipping(self, data):
        if not data.shipping_address:
            self.reject("shipping_address", "Shipping address required")

class CustomOrderBlueprint(BaseOrderBlueprint):
    # Overriding validate_shipping to support digital-only orders
    @ward
    def validate_shipping(self, data):
        if not data.is_digital and not data.shipping_address:
            self.reject("shipping_address", "Shipping address required for physical items")

    # A new subclass ward (will execute after inherited validate_pricing and overridden validate_shipping)
    @ward
    def validate_gift_wrap(self, data):
        if data.gift_wrapped and data.is_digital:
            self.reject("gift_wrapped", "Cannot gift-wrap digital products")
```
