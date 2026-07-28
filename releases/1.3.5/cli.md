# CLI Changes — Aquilia v1.3.5

No commands were added, removed, or renamed in this release. One existing command gained new validation.

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

- [Mail Security & MIME](mail_security.md)
- [Migration Guide](migration.md)
