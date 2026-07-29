# CLI Changes — Aquilia v1.3.5

One command group was added (`aq contracts`). One existing command gained new validation. Nothing was removed or renamed.

---

## New: `aq contracts stubs`

Emits `.pyi` type stubs so `mypy` and `pyright` can see Contract fields.

### Why

A Contract builds its fields at class-body evaluation time and serves them through `__getattr__`. Neither is visible to a static analyser, so `contract.email` was `Any` at best and an attribute error under `--strict` at worst. For a team with a type-checking gate in CI, this was the single largest adoption barrier.

A generated `.pyi` is a portable artifact: every type checker consumes it with no plugin, no configuration, and no version coupling.

### Usage

```bash
aq contracts stubs MODULES... [--check] [--path DIR]
```

| Flag | Purpose |
|---|---|
| `--check` | Do not write. Exit non-zero if any stub is missing or out of date. |
| `--path DIR` | Directory prepended to `sys.path` before importing. Default: current directory. |

### Examples

```bash
# Write myapp/contracts.pyi
aq contracts stubs myapp.contracts

# Several modules at once
aq contracts stubs myapp.users.contracts myapp.orders.contracts

# CI freshness gate
aq contracts stubs myapp.contracts --check
```

### Output

Success:

```
$ aq contracts stubs myapp.contracts
  ✔ myapp.contracts: wrote /app/myapp/contracts.pyi
      2 contract(s): AddressContract, OrderContract
```

Anything that could not be typed faithfully is emitted as `Any` and named, so a lost annotation is reported rather than silently weakening the module's types:

```
  ✔ myapp.contracts: wrote /app/myapp/contracts.pyi
      2 contract(s): AddressContract, OrderContract
      REGISTRY: module-level value emitted as Any
```

`--check` on a stale or missing stub exits `1` and prints the fix:

```
$ aq contracts stubs myapp.contracts --check
  ✘ myapp.contracts: contracts.pyi is missing or out of date
      2 contract(s): AddressContract, OrderContract

  Stubs are out of date. Regenerate with:
      aq contracts stubs myapp.contracts
```

A module that fails to import, or that has no source file, exits `1` with the reason.

### Recommended workflow

Commit the generated stubs, then gate on freshness:

```bash
# Once, after declaring or changing Contracts
aq contracts stubs myapp.contracts
git add myapp/contracts.pyi
```

```yaml
# .github/workflows/ci.yml
- name: Check Contract stubs are current
  run: aq contracts stubs myapp.contracts --check

- name: Type check
  run: mypy myapp/
```

Generation is deterministic — regenerating unchanged input is a byte-identical no-op, so `--check` cannot fail at random.

Full details in [Stub Generation & Deprecations](contracts_tooling.md).

---

## `aq mail check`

`aq mail check` validates mail configuration without sending anything. It now also validates DKIM configuration.

### Why

DKIM signing failures raise at send time rather than silently shipping an unsigned message — a receiving server treats a missing signature very differently from an invalid one, and an operator who enabled DKIM expects signed mail or a loud error. That is the right runtime behavior, but it means a misconfiguration is not discovered until the first real send, possibly in production.

`aq mail check` now surfaces both failure modes up front.

### New checks

When `dkim_enabled` is true:

1. **`dkim_domain` unset** — signing cannot proceed without a domain.
2. **`dkimpy` not installed** — the signing dependency is missing.

### Output

```
$ aq mail check
DKIM is enabled but dkim_domain is unset -- sends will fail
DKIM is enabled but 'dkimpy' is not installed -- pip install aquilia[mail-dkim]
```

A clean configuration reports no issues, as before.

### Recommended workflow

```bash
# After enabling DKIM in workspace.py
pip install aquilia[mail-dkim]
aq mail check                          # verify configuration
aq mail send-test --to you@example.com # verify real delivery
```

Add `aq mail check` to CI or a deploy preflight step for any application that sends mail.

---

## Unchanged Commands

`aq mail send-test` and `aq mail inspect` are unchanged. No flags were added, changed, or deprecated, and no output formats changed.

Background task workers are not started by a dedicated CLI command; a worker process is a normal Aquilia application configured with `num_workers` and a shared backend. See [Distributed & Persistent Backends](distributed_tasks.md).

---

## Related

- [Contracts — Stub Generation & Deprecations](contracts_tooling.md)
- [Mail Security & MIME](mail_security.md)
- [Migration Guide](migration.md)
