# Validation Engine — v1.4.0b1

Aquilia v1.4.0b1 fundamentally re-architects how runtime data validation works. By shifting contract evaluation into the `_dataengine` C++ extension, validation is now orders of magnitude faster.

## The Problem: The "All or Nothing" Approach

In earlier versions, Aquilia evaluated a model's schema to determine if it could be natively accelerated. However, the evaluation was binary. If a contract contained 20 fields, and 19 were simple strings and integers, but the 20th field used a highly customized Python validator or an unsupported regex pattern, the **entire contract** was rejected by the native engine.

This meant the framework fell back to pure Python validation for every field on that model. In production, models are complex, meaning the native fast-path was effectively dead code for many real-world applications.

## The Solution: Per-Field Eligibility

The new `FieldPlan` engine introduces **per-field eligibility**.

During server startup, when models are registered, `Sigil.validate` compiles the schema into a `CompiledPlan(plan, escaped)` instance.
- **`plan`**: Represents the subset of fields on the model that can be evaluated natively in C++.
- **`escaped`**: Represents the set of field names that require complex Python evaluation.

During a request, the native `FieldPlan` engine rapidly blasts through the fields in `plan`. Once complete, the framework looks at the `escaped` list. If it is non-empty, it yields to Python to validate only those specific fields. 

### The `_only` Parameter
This split evaluation is powered by the new `_only=frozenset(...)` parameter in `Sigil.validate`. When escaping to Python, the framework passes `_only=escaped`, instructing the Python evaluator to completely ignore the natively handled fields, resulting in zero duplicated effort.

### Impact Example: `UserProfile`
Consider a `UserProfile` model with 15 fields. One field, `biography`, uses a custom NLP python validator. 
- **Old System:** 0 fields evaluated natively, 15 fields evaluated in Python.
- **New System:** 14 fields evaluated natively, 1 field evaluated in Python.
**Measured Result:** A massive **2.79x improvement** in validation throughput for this specific model during benchmarks.

---

## Native TypeCodes and Container Kinds

The C++ `FieldPlan` engine was expanded extensively to cover the vast majority of standard use cases. It represents fields internally using a tuple of `(TypeCode, ContainerKind)`.

### Supported TypeCodes
The following base data types are fully accelerated in C++:
- `STR`
- `INT`
- `FLOAT`
- `BOOL`
- `UUID` (via native parser)
- `DATE`
- `DATETIME`
- `TIME`
- `DECIMAL`
- `DURATION`
- `BYTES`
- `CHOICE`
- `ENUM` (plain, non-customized)
- `PASSTHROUGH` (Any)

### Supported ContainerKinds
Native collections can wrap any supported TypeCode:
- `NONE` (scalar)
- `LIST`
- `SET`
- `TUPLE`
- `DICT` (with string keys)

Nested sub-plans (e.g., a `List` of `Address` contracts inside a `UserProfile` contract) are fully supported natively, provided the child contract also qualifies.

---

## What Gets ESCAPED and Why?

The compiler is conservative. It escapes fields to Python if the native engine cannot guarantee 100% semantic parity with Python's execution model.

**Common causes for a field to escape:**
1. **Custom Validators / Pipelines:** Any use of `@validator` or data-mangling pipelines requires executing arbitrary Python bytecode, which C++ cannot do efficiently.
2. **`default_factory`:** If a field relies on a dynamic Python function to generate its default value at runtime (e.g., `default_factory=datetime.utcnow`), it escapes.
3. **`FloatFacet` with `multiple_of`:** Floating point modulo arithmetic has slight precision discrepancies between C++ and Python. To guarantee exact parity, this specific constraint escapes.
4. **Custom Enum `_missing_`:** If an `Enum` class overrides the `_missing_` hook to provide dynamic fallback resolution, the native engine escapes it, as evaluating it requires the Python interpreter.
5. **Complex Nested Facets:** Highly customized nested dependencies that cannot be flattened into a standard TypeCode tree.

### Code Example

```python
from aquilia import Model, Field
from enum import Enum

class Status(Enum):
    ACTIVE = "active"
    BANNED = "banned"

class UserProfile(Model):
    # NATIVE: Simple string
    username: str
    
    # NATIVE: Int with standard bounds
    age: int = Field(ge=18, le=100) 
    
    # NATIVE: Plain Enum
    status: Status
    
    # NATIVE: Standard Container
    tags: list[str]
    
    # ESCAPED: Custom validator logic
    bio: str = Field(validator=lambda x: clean_html(x))
```
In this model, `username`, `age`, `status`, and `tags` execute at C++ speeds. Only `bio` incurs the Python evaluation overhead.

---

## Performance Bottom Line

By maximizing the surface area of natively supported facets and mitigating the blast radius of complex fields via `escaped` sets, the validation engine operates at maximum theoretical throughput for standard data structures while remaining fully extensible for complex business logic.
