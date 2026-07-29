---
title: "Validation Control & Data Sources"
description: "Ward ordering, conditions, groups, fail-fast, localized messages, and building Contracts from environment variables or CLI arguments"
icon: lucide/sliders-horizontal
---

Beyond declaring rules, Contracts let you control *which* rules run, *in what
order*, and *what language* their messages are reported in — and let you feed a
Contract from sources other than an HTTP body.

---

## Ward ordering

Wards run in definition order by default. Pass `order=` to override; lower runs
first, and wards sharing an order keep definition order.

```python
class OrderContract(Contract):
    @ward(order=-10)
    def cheap_structural_check(self, data):
        ...

    @ward(order=10)
    def expensive_check(self, data):
        ...
```

Use this when one ward's rejection makes another's work redundant or its error
message misleading.

---

## Conditional wards

`when=` takes a predicate receiving the validated data. The ward runs only when
it returns truthy.

```python
class OrderContract(Contract):
    kind = ChoiceFacet(choices=["digital", "physical"])
    shipping_address = TextFacet(required=False)

    @ward(when=lambda data: data.get("kind") == "physical")
    def needs_shipping_address(self, data):
        if not data.get("shipping_address"):
            self.reject("shipping_address", "Required for physical orders")
```

A predicate that raises is treated as "does not apply". The predicate is a
routing decision, not a validation rule — a broken predicate must not
manufacture a field error attributed to the ward it was gating.

---

## Validation groups

Group wards to run different rule sets in different contexts:

```python
class UserContract(Contract):
    email = EmailFacet()

    @ward
    def always_applies(self, data):
        ...

    @ward(groups=("registration",))
    def email_not_disposable(self, data):
        ...

    @ward(mode="async", groups=("checkout",))
    async def payment_method_valid(self, data):
        ...
```

```python
contract.is_sealed()                        # ungrouped wards only
contract.is_sealed(groups="registration")   # ungrouped + registration
contract.is_sealed(groups=["a", "b"])       # ungrouped + a + b
await contract.is_sealed_async(groups="checkout")
```

A ward *without* groups always runs: it expresses an invariant that holds
regardless of which group the caller asked for. Groups describe the validation
pass, so for `many=True` Contracts every row observes them.

---

## Fail-fast

By default every ward runs and errors accumulate, so a client sees all problems
at once. Set `Spec.fail_fast` to stop at the first error instead:

```python
class ExpensiveContract(Contract):
    class Spec:
        fail_fast = True
```

Worth it when wards are costly (each hits the database or an external service)
and there is no value in reporting the rest once one has failed.

---

## Frozen Contracts

`Spec.frozen` makes validated data reject mutation, so a value that passed
validation cannot be edited afterwards:

```python
class AuditRecordContract(Contract):
    class Spec:
        frozen = True

record = AuditRecordContract(data=payload)
record.is_sealed()
record.validated_data["actor"] = "someone-else"   # TypeError
```

Use `copy(update=...)` to derive a modified Contract, which re-validates.

---

## Localized validation messages

Validation messages resolve through `aquilia.contracts.messages.contract_message`.
When an `I18nService` is active for the request, messages come from the
translation catalog under the `contracts.` namespace; otherwise the built-in
English text is used.

```json
{
  "contracts": {
    "required": "Este campo es obligatorio",
    "min_length": "Debe tener al menos {min} caracteres",
    "min_value": "Debe ser al menos {min}"
  }
}
```

Placeholders are ICU-style (`{name}`), matching the rest of Aquilia's i18n, and
receive the same parameters the English pattern uses (`{min}`, `{max}`,
`{field}`, `{type}`, `{expected}`).

An application that never configures i18n sees byte-identical messages to
previous releases. A key absent from the catalog falls back to English rather
than rendering the raw key to an end user, and message resolution never raises
— failing to render the *message* for a rejected payload would turn a 422 into
a 500.

Available keys are listed in `aquilia.contracts.messages.DEFAULT_MESSAGES`.

---

## Building Contracts from other sources

Contracts accept more than mappings. Dataclasses, attrs classes, and
`TypedDict` values are adapted automatically:

```python
@dataclass
class ImportRow:
    name: str
    age: int

PersonContract(data=ImportRow("Kai", 30)).is_sealed()   # True
```

Adaptation is not a bypass — facet rules still apply. A payload that is not a
mapping and not a recognized structured type reports
`Expected an object, got str` rather than a misleading "this field is required"
for every field.

### Environment variables

```python
class SettingsContract(Contract):
    port = IntFacet(default=8000)
    database_url = TextFacet()

settings = SettingsContract.from_env(prefix="APP_")   # APP_PORT, APP_DATABASE_URL
```

Field names map to upper-case variable names. Absent variables are omitted
rather than set empty, so each field's `default` and `required` rules decide
the outcome. Values arrive as strings and are cast by the normal facet
pipeline, so configuration gets the same validation as request data instead of
a parallel parsing path. Validation runs by default so configuration errors
surface at startup, not at first use.

### CLI arguments

```python
class ImportContract(Contract):
    source = TextFacet()
    dry_run = BoolFacet(default=False)

options = ImportContract.from_cli(["--source", "data.csv", "--dry-run"])
```

Supports `--flag value`, `--flag=value`, and bare `--flag` (boolean). Dashes map
to underscores, and a repeated flag collects into a list for a `ListFacet` to
validate. Unknown flags are ignored so a Contract can read the subset of
arguments it cares about from a larger command line.

This is a deliberately small parser for feeding a Contract, not a replacement
for the `aq` CLI's Click layer.
