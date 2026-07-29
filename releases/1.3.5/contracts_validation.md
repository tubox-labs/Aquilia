# Contracts — Validation Control & Typing — Aquilia v1.3.5

The second half of the Contracts audit closed the gaps between what a Contract could express and what real validation needs: rule ordering, conditional rules, validation groups, fail-fast, frozen Contracts, and the strongly-typed primitives that previously fell through to a permissive `TextFacet`.

Everything here is additive. A Contract that declares none of it behaves exactly as it did in v1.3.4.

---

## Ward ordering, conditions, and groups

### Motivation

`@ward` had exactly one knob: `mode`. Real validation needs three more, and without them each was hand-rolled inside ward bodies where it could not be inspected, reordered, or reused.

| Need | Previous workaround |
|---|---|
| Run a cheap check before an expensive one | Rely on definition order and hope nobody reorders the methods |
| A rule that applies only to some payloads | `if` at the top of the ward body |
| Different rules for different operations | A separate Contract subclass per operation |

### `order` — deterministic sequencing

```python
class OrderContract(Contract):
    @ward(order=-10)
    def total_not_negative(self, data):
        if data["total"] < 0:
            self.reject("total", "Must not be negative")

    @ward(order=0)          # default
    async def payment_authorized(self, data):
        ...                  # expensive: hits the payment provider
```

Lower runs first. Wards sharing an `order` keep definition order — the sort is stable, so a Contract that sets no `order` behaves exactly as before.

Use it when one ward's rejection makes another's work redundant or misleading: there is no point authorizing payment on a negative total.

### `when` — conditional rules

```python
class OrderContract(Contract):
    @ward(when=lambda data: data["kind"] == "physical")
    def needs_shipping_address(self, data):
        if not data.get("shipping_address"):
            self.reject("shipping_address", "Required for physical orders")
```

The predicate receives the validated data. Moving the condition into metadata means the rule's applicability is inspectable rather than buried in the body.

**Edge case — a predicate that raises is treated as "does not apply."** The predicate is a routing decision, not a validation rule. A broken predicate must not manufacture a field error attributed to the ward it was gating, because that error would name the wrong field and the wrong cause.

### `groups` — per-operation rule sets

```python
class UserContract(Contract):
    @ward(groups=("registration",))
    def password_strength(self, data):
        ...

    @ward(groups=("admin",))
    def role_assignable(self, data):
        ...

    @ward
    def email_wellformed(self, data):    # no groups — always runs
        ...
```

Select groups per validation pass:

```python
contract.is_sealed(groups="registration")
contract.is_sealed(groups=["registration", "admin"])
await contract.is_sealed_async(groups="checkout")
```

**An ungrouped ward always runs.** It expresses an invariant that holds regardless of which group the caller asked for — an email must be well-formed whether or not this is a registration. Grouping an invariant would silently disable it for every pass that did not name its group.

Groups propagate to nested Contracts, so a group selected at the top level applies through the whole tree.

### `Spec.fail_fast`

```python
class OrderContract(Contract):
    class Spec:
        fail_fast = True

    @ward
    def first(self, data): ...
    @ward
    def second(self, data): ...    # never runs if `first` rejected
```

Stops at the first ward error instead of accumulating all of them. Default is `False`, unchanged — accumulating every error is the right default for a form, where a user should see all problems at once. `fail_fast` suits pipelines where a later rule's output would be noise once an earlier one has failed.

Applies to the ward phase only; structural field validation always accumulates.

---

## Frozen Contracts, equality, and copy

### `Spec.frozen`

```python
class ConfigContract(Contract):
    port = IntFacet()

    class Spec:
        frozen = True

config = ConfigContract(data={"port": 8000})
config.is_sealed()
config.validated_data["port"] = 9000     # TypeError
```

**Motivation:** `is_sealed()` returning `True` is a guarantee that the data satisfied every rule. That guarantee expires the moment a caller assigns to a field. Freezing makes the guarantee durable for the lifetime of the object.

### `Contract.__eq__`

```python
a = UserContract(data={"name": "Ada"})
b = UserContract(data={"name": "Ada"})
a.is_sealed(); b.is_sealed()
a == b     # True
```

Two Contracts are equal when they are the same class and carry the same validated data. Unvalidated Contracts compare on their raw input, so a comparison before sealing is still meaningful rather than degrading to identity.

**Contracts remain unhashable:**

```python
hash(a)
# TypeError: UserContract is unhashable (its validated data is mutable)
```

This is deliberate. Defining `__eq__` without `__hash__` would make Python set `__hash__ = None` silently; an explicit `__hash__` that raises names the reason instead. Validated data is mutable by default, so a hash computed at insertion time would go stale and the object would become unfindable in its own dict.

### `copy(update=...)`

```python
updated = contract.copy(update={"name": "Grace"})
```

Derives a new Contract with fields replaced. Keys absent from `update` carry over.

**Re-validates by default.** An override can violate a constraint the original satisfied, and skipping validation would produce a Contract whose `validated_data` never passed the rules it claims to enforce:

```python
contract.copy(update={"age": -5})
# SealFault — the override is validated, not trusted
```

Defer validation when building a payload in stages:

```python
draft = contract.copy(update={"name": "Grace"}, validate=False)
final = draft.copy(update={"email": "g@example.com"})    # validates here
```

For Contracts with async wards, use `copy_async()`:

```python
updated = await contract.copy_async(update={"sku": "ABC"})
```

`copy()` on a Contract with async wards raises `ContractAsyncMismatchFault` rather than silently skipping them.

---

## New facets

Four types previously fell through to a permissive `TextFacet` or had no facet at all.

### `BytesFacet`

Binary data over a JSON transport.

```python
class UploadContract(Contract):
    payload = BytesFacet()                    # base64 (default)
    checksum = BytesFacet(encoding="hex")

UploadContract(data={"payload": "aGVsbG8=", "checksum": "68656c6c6f"})
# validated_data: {"payload": b"hello", "checksum": b"hello"}
```

**Bug fixed:** `bytes` annotations previously mapped to `TextFacet`, whose cast whitelist *rejects real `bytes`*. A `payload: bytes` field rejected every genuine value while accepting plain strings — non-functional end to end. `bytes` annotations now route to `BytesFacet`.

Size constraints apply to the **decoded** length, which is what matters for storage and memory:

```python
thumbnail = BytesFacet(max_length=64 * 1024)
```

Always bound `max_length` on a client-facing binary field. Base64 expands roughly 33%, so a modest request body still decodes to a large allocation — an unbounded field is a memory-exhaustion vector.

JSON Schema emits `{"type": "string", "format": "byte"}`.

### `PathFacet`

Filesystem paths, validated as `pathlib.PurePosixPath`.

```python
class UploadContract(Contract):
    destination = PathFacet()

UploadContract(data={"destination": "reports/q3.pdf"})
# validated_data: {"destination": PurePosixPath('reports/q3.pdf')}
```

**Security defaults reject the two ways a client-supplied path escapes its root:**

| Input | Result | Why |
|---|---|---|
| `/etc/passwd` | `Path must be relative` | `Path("/root") / "/etc/passwd"` resolves to `/etc/passwd`, discarding the root |
| `../../etc/passwd` | `Path may not contain '..' segments` | Traversal out of the intended directory |
| `a\x00b` | `Path may not contain null bytes` | Truncates at the OS layer, so a name passing an extension check can open a different file |

Null bytes are rejected unconditionally. The other two relax only for paths that never originate from a request:

```python
destination = PathFacet(must_be_relative=False, allow_traversal=True)
```

Windows separators are normalized before the `..` check, so a backslash cannot smuggle a segment past it on a POSIX server.

Values are `PurePosixPath` so a payload validates identically regardless of server platform. Convert with `Path(value)` at the point of filesystem access.

### `SecretFacet` and `Secret`

Sensitive strings that never appear in output or tracebacks.

```python
class LoginContract(Contract):
    password = SecretFacet(min_length=8)

contract = LoginContract(data={"password": "hunter2hunter2"})
contract.is_sealed()

repr(contract.validated_data["password"])       # "Secret('**********')"
str(contract.validated_data["password"])        # "**********"
contract.validated_data["password"].reveal()    # "hunter2hunter2"
```

`write_only` by default, so the field is accepted inbound and omitted from every serialized representation.

**Equality is constant-time** (`hmac.compare_digest`), so comparing a submitted value against a stored one does not leak the shared-prefix length through timing:

```python
if contract.validated_data["password"] == stored_secret:   # constant-time
    ...
```

**Security scope:** masking defends against *accidental* disclosure — log lines, exception reports, debug pages. It is not a substitute for hashing or encryption at rest. Call `.reveal()` only at the point of use.

JSON Schema emits `{"type": "string", "format": "password", "writeOnly": true}`.

### `MACAddressFacet`

```python
class DeviceContract(Contract):
    mac = MACAddressFacet()
```

Accepts colon, dash, and Cisco notations, normalizing to lowercase colon-separated form:

| Input | Validated value |
|---|---|
| `AA:BB:CC:DD:EE:FF` | `aa:bb:cc:dd:ee:ff` |
| `aa-bb-cc-dd-ee-ff` | `aa:bb:cc:dd:ee:ff` |
| `aabb.ccdd.eeff` | `aa:bb:cc:dd:ee:ff` |

Normalizing at validation means downstream comparisons and database lookups do not each reimplement it.

### Annotation routing

These types now resolve to the right facet from a plain annotation:

```python
import ipaddress, pathlib
from aquilia.contracts.facets import Secret

class DeviceContract(Contract):
    address: ipaddress.IPv4Address    # IPFacet
    config_path: pathlib.Path         # PathFacet
    api_key: Secret                   # SecretFacet
```

---

## `IntFacet` no longer truncates silently

### Previous behavior

```python
class QuantityContract(Contract):
    qty = IntFacet()

QuantityContract(data={"qty": 3.9}).validated_data["qty"]   # 3   ← silently truncated
QuantityContract(data={"qty": "3.9"}).errors                # rejected
```

The same logical input behaved differently depending on its wire type. A JSON body with `3.9` was accepted and quietly became `3`; the string `"3.9"` was correctly rejected.

### New behavior

```python
QuantityContract(data={"qty": 3.9}).errors
# {"qty": ["Expected integer, got non-integer number 3.9"]}

QuantityContract(data={"qty": 3.0}).is_sealed()   # True — integral float still accepted
```

`NaN` and `Infinity` are rejected explicitly.

**This is a behavioral change.** Payloads previously accepted with silent truncation now fail validation. Silent truncation of a quantity, a price in cents, or a page offset is a data-integrity bug that surfaces far from its cause.

---

## Alternate data sources

### `Contract.from_env()`

```python
class SettingsContract(Contract):
    port = IntFacet(default=8000)
    database_url = TextFacet()

settings = SettingsContract.from_env(prefix="APP_")
# reads APP_PORT and APP_DATABASE_URL
```

Field names map to upper-case variable names. Absent variables are **omitted rather than set empty**, so each field's `default` and `required` rules decide the outcome exactly as they would for a JSON body.

Every value arrives as a string; normal facet casting turns `"8000"` into an `int`. Configuration therefore gets the same validation as request data instead of a parallel parsing path.

**Validates by default** — configuration errors should surface at startup, not at first use. Pass `seal=False` to defer.

### `Contract.from_cli()`

```python
class ImportContract(Contract):
    source = TextFacet()
    dry_run = BoolFacet(default=False)
    tags = ListFacet(child=TextFacet(), required=False)

options = ImportContract.from_cli(["--source", "data.csv", "--dry-run",
                                   "--tags", "a", "--tags", "b"])
# {"source": "data.csv", "dry_run": True, "tags": ["a", "b"]}
```

Parses `--flag value`, `--flag=value`, and bare `--flag` (boolean). Dashes map to underscores, so `--database-url` fills `database_url`. A repeated flag collects into a list for a `ListFacet` to validate.

**Limitations, deliberately:** a small parser for feeding a Contract, not a replacement for the `aq` CLI's Click layer. Unknown flags are ignored so a Contract can read the subset of arguments it cares about from a larger command line. No short flags, no subcommands, no `--` terminator.

---

## Localized validation messages

Every built-in validation message now resolves through `contract_message()`:

```python
from aquilia.contracts.messages import contract_message

contract_message("min_length", min=5)
# "Must be at least 5 characters"
```

Resolution order:

1. The active i18n catalog's `contracts.` namespace, if an i18n service is bound to the request.
2. The built-in English default, with ICU-style `{name}` parameter substitution.

```yaml
# locales/fr/messages.yaml
contracts:
  required: "Ce champ est obligatoire"
  min_length: "Doit contenir au moins {min} caractères"
```

The service and locale are read from `contextvars`, so a request's locale applies to validation errors raised anywhere in its call tree without threading a locale parameter through every facet.

**Applications without i18n configured see byte-identical messages** to v1.3.4.

**Resolution never raises.** A missing key, a malformed template, or a broken i18n service falls back to the built-in text. Failing to render the message for a rejected payload would turn a 422 into a 500 — the client would lose the validation errors entirely because of a translation problem.

33 message keys ship: field presence, type, length, numeric range, collection size, choice, format (email/URL/slug/IP/MAC/UUID), and path safety.

---

## Related pages

- [Contracts — Nested Validation Pipeline](contracts_pipeline.md) — the nested-pipeline and async serialization fixes
- [Contracts — Stub Generation & Deprecations](contracts_tooling.md) — `aq contracts stubs`, `seal_*` deprecation
- [Migration Guide](migration.md) — upgrade checklist and behavioral-change review
