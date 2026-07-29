---
title: "Wards & Cross-Field Validation"
description: "Cross-field validation using @ward decorators in Aquilia Contracts"
icon: lucide/shield
---
Wards are explicit cross-field validators in Aquilia Contracts that are registered during class-body evaluation. They replace older, fragile method-name prefix scanning with structured metadata and decorators.

---

### What is a Ward?

A **Ward** is an explicit cross-field validator registered on an Aquilia [Contract](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/core.py#L826). As defined in [ward.py](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/ward.py), wards replace the legacy prefix-based scanning of `seal_*` or `async_seal_*` methods with an explicit decorator-driven registration system discovered once at class-body evaluation time (see [ward.py lines 2–6](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/ward.py#L2-L6)).

---

### Bare Decorator Usage: `@ward`

Using the decorator without arguments registers a synchronous ward method:

```python
from aquilia.contracts import ward

class OrderContract(Contract):
    @ward
    def total_matches_items(self, data):
        computed = sum(i.price * i.qty for i in data.items)
        if abs(computed - data.total) > 0.01:
            self.reject("total", f"Expected {computed}, got {data.total}")
```

#### Under the Hood
* When used as a bare decorator `@ward`, the [ward](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/ward.py#L57) class intercepts the method call during class evaluation via its `__new__` method (see [ward.py lines 80–90](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/ward.py#L80-L90)).
* It validates that the decorated object is indeed a callable (raising a `TypeError` if not).
* It registers validation metadata on the function under `fn.__ward_meta__` as `{"mode": "sync", "name": fn.__name__}` (see [ward.py line 88](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/ward.py#L88)).

---

### Parameterised Factory: `@ward(mode="async")`

When you need to perform validation that requires calling asynchronous APIs (such as checking a database or calling a remote service), you can parameterise the decorator:

```python
class OrderContract(Contract):
    @ward(mode="async")
    async def discount_code_valid(self, data):
        if data.discount_code and not await lookup(data.discount_code):
            self.reject("discount_code", "Unknown code")
```

#### Under the Hood
* Calling `@ward(mode="async")` invokes `__new__` without a decorated function, returning a new instance of the [ward](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/ward.py#L57) class acting as a decorator factory (see [ward.py lines 91–95](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/ward.py#L91-L95)).
* The `mode` parameter is validated against the valid modes list, raising a `ValueError` if the specified mode is invalid.
* When the returned `ward` instance is subsequently called with the decorated function (`fn`), its `__call__` method attaches the `__ward_meta__` dictionary using the stored mode (see [ward.py lines 105–110](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/ward.py#L105-L110)).

---

### The `WardMethod` Dataclass

The metadata for each registered ward is stored in an instance of the [WardMethod](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/ward.py#L42-L47) class, a frozen, memory-optimized dataclass (using slots) defined in [ward.py lines 42–47](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/ward.py#L42-L47).

| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `name` | `str` |  | The name of the validator method. |
| `fn` | `object` |  | The actual validator callable/method object. |
| `mode` | `str` |  | The execution mode: either "sync" or "async". |


---

### Valid Validation Modes

The validation engine supports a restricted set of modes defined in the internal constant `_VALID_MODES` (see [ward.py line 54](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/ward.py#L54)):

* `"sync"`: Standard synchronous validation.
* `"async"`: Asynchronous validation (requires an event loop to resolve).

Any value passed to the decorator's `mode` parameter that is not in `_VALID_MODES` raises a `ValueError` during decoration (see [ward.py lines 81–82](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/ward.py#L81-L82)).

---

### Method Collection: `collect_ward_methods()`

During Contract class creation, all registered wards are harvested using the [collect_ward_methods](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/ward.py#L118) helper function (see [ward.py lines 118–199](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/ward.py#L118-L199)).

#### Inheritance and Override Semantics
1. **Inheritance Scan**: The function iterates through the base classes (`bases`) in Method Resolution Order (MRO) to collect inherited ward methods (see [ward.py lines 147–150](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/ward.py#L147-L150)).
2. **Namespace Scan**: It then scans the current class namespace for attributes decorated with `@ward` (identifiable by the `__ward_meta__` attribute) (see [ward.py lines 152–161](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/ward.py#L152-L161)).
3. **Override Mapping**: The inherited and own methods are merged. If a subclass defines a ward with the same name as an inherited ward, the subclass's version replaces (overrides) the parent's version in the merged dictionary (see [ward.py lines 182–185](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/ward.py#L182-L185)).

---

### Deprecation Notice: Legacy Prefix Scanning

Before explicit `@ward` registration, Aquilia discovered cross-field validators by scanning for methods whose names began with `seal_` or `async_seal_`.

!!! warning "Deprecated in 1.3.0 — removed in 2.0.0"
    A Contract declaring an undecorated `seal_*`/`async_seal_*` method emits a `DeprecationWarning` at class-body evaluation naming the exact replacement:

    ```
    DeprecationWarning: OrderContract.seal_total is registered as a validator by the
    deprecated seal_*/async_seal_* prefix convention (deprecated in Aquilia 1.3.0,
    removed in 2.0.0). Decorate it with @ward instead — the method body does not need
    to change, and you may then rename it freely. After 2.0.0, OrderContract.seal_total
    will be treated as an ordinary method and will silently stop validating.
    ```

    Until 2.0.0 these methods continue to run exactly as before. There is no behavioral change in 1.x — only the warning.

#### Why the convention is being removed

Each of these has cost real debugging time:

- **A rename silently disables validation.** Renaming `seal_total` to `check_total` during a routine cleanup removes the rule with no error and no warning. The Contract keeps reporting success on payloads it should reject.
- **A name collision silently creates one.** A helper legitimately named `seal_envelope` is executed as a validator on every request, its return value discarded and any exception it raises turned into a user-facing field error.
- **Async mode was inferred, not declared.** Mode came from `inspect.iscoroutinefunction`, so a validator awaiting the database while written as a sync `def` registered as sync — the coroutine was created, never awaited, and the check never ran.
- **No room to grow.** Ordering, conditions, and validation groups have nowhere to live in a naming convention. `@ward` carries them as metadata.

#### Migration

Mechanical — decorate the method. The body does not change.

```python
# Before (deprecated)
class OrderContract(Contract):
    def seal_total(self, data):
        if data["total"] < 0:
            self.reject("total", "Must not be negative")

    async def async_seal_stock(self, data):
        if not await in_stock(data["sku"]):
            self.reject("sku", "Out of stock")

# After
class OrderContract(Contract):
    @ward
    def total_not_negative(self, data):          # rename is now safe
        if data["total"] < 0:
            self.reject("total", "Must not be negative")

    @ward(mode="async")
    async def stock_available(self, data):
        if not await in_stock(data["sku"]):
            self.reject("sku", "Out of stock")
```

Two things change beyond the decorator: `mode="async"` becomes explicit rather than inferred, and the methods can be renamed to describe the rule rather than to satisfy the scanner.

#### Finding every affected method

Promote the warning to an error and import your Contract modules:

```bash
python -W error::DeprecationWarning -c "import myapp.contracts"
```

Or fail the test suite on it:

```toml
[tool.pytest.ini_options]
filterwarnings = ["error::DeprecationWarning"]
```

Both report each legacy method with its class name, its exact replacement decorator, and the file and line that declared it. Because registration happens at class-body evaluation, importing the module is enough — no request needs to run.

---

### Registration: Class Attribute `_ward_methods`

The list of collected [WardMethod](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/ward.py#L42-L47) descriptors is stored on the evaluated Contract class as a class attribute named `_ward_methods` (see [ward.py lines 148–150](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/ward.py#L148-L150)).

---

### Error Reporting via `self.reject()`

Within a ward method, validation failures are reported by calling `self.reject(field, message)`.

* **Usage in `ward.py`**: The decorator and module docstring examples call `self.reject(field, message)` to report specific validation errors (e.g., `self.reject("total", "...")` in [ward.py lines 17, 22](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/ward.py#L17)).
* **Actual Implementation**: "Unknown from inspected source" (the actual `self.reject()` method is not implemented or defined within [ward.py](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/ward.py), although its usage in validator methods is demonstrated in the module docstring on lines 17 and 22. According to [.cache/index_contracts.json](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/.cache/index_contracts.json#L125), `reject()` is a method on the base [Contract](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/core.py#L826) class defined in `aquilia/contracts/core.py` at lines 1250–1260).

---

### Execution Order

When a contract is validated, wards are executed in a deterministic, stable order:
1. **Inherited Wards First**: Wards defined in parent base classes are run first, preserving MRO and definition order (see [ward.py lines 139–141, 191–193](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/ward.py#L139-L141)).
2. **Subclass Wards Second**: Wards defined directly on the subclass are run next in their order of definition (see [ward.py lines 141–142, 194–197](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/ward.py#L141-L142)).

---

### Code Examples

Below are comprehensive usage patterns for sync, async, and inherited wards:

#### 1. Synchronous Ward Method
```python
from aquilia.contracts import Contract, ward

class RegistrationContract(Contract):
    # Registering a synchronous ward using the bare decorator
    @ward
    def validate_password_match(self, data):
        if data.password != data.password_confirmation:
            self.reject("password_confirmation", "Passwords do not match")
```

#### 2. Asynchronous Ward Method
```python
from aquilia.contracts import Contract, ward

class UserContract(Contract):
    # Registering an asynchronous ward using the parameterised decorator factory
    @ward(mode="async")
    async def validate_unique_email(self, data):
        if data.email and not await db.is_email_unique(data.email):
            self.reject("email", "Email address is already registered")
```

#### 3. Inherited and Overridden Wards
```python
from aquilia.contracts import Contract, ward

class BaseOrderContract(Contract):
    @ward
    def validate_pricing(self, data):
        # Base pricing check
        if data.total < 0:
            self.reject("total", "Total cannot be negative")

    @ward
    def validate_shipping(self, data):
        if not data.shipping_address:
            self.reject("shipping_address", "Shipping address required")

class CustomOrderContract(BaseOrderContract):
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
