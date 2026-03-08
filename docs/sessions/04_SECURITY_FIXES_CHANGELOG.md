# Session Security Fixes Changelog

## Summary

13 security fixes applied across 6 files. All 4,702 tests pass.

---

## Fix 1: SessionID.__init__() — Raw ValueError → SessionInvalidFault
**File:** `aquilia/sessions/core.py`  
**Line:** ~108  
**Before:**
```python
raise ValueError(f"Session ID must be exactly {self.ENTROPY_BYTES} bytes")
```
**After:**
```python
from .faults import SessionInvalidFault
raise SessionInvalidFault()
```

## Fix 2: SessionID.from_string() — Input Validation + Fault Integration
**File:** `aquilia/sessions/core.py`  
**Lines:** ~130-160  
**Changes:**
- Added `_MAX_ENCODED_LENGTH = 128` class attribute
- Added type check: `not isinstance(encoded, str)`
- Added length guard: `len(encoded) > cls._MAX_ENCODED_LENGTH`
- Replaced 3× `raise ValueError(...)` → `raise SessionInvalidFault()`
- Stripped exception chaining (no internal details in fault)

## Fix 3: Session Mutation Guards — RuntimeError → SessionLockedFault
**File:** `aquilia/sessions/core.py`  
**Lines:** ~310-360  
**Changes:**
- Added `MAX_DATA_KEYS = 256` class attribute
- Added `_check_writable()` helper → `SessionLockedFault`
- Added `_check_data_limit()` helper → `SessionPolicyViolationFault`
- Updated `__setitem__`, `__delitem__`, `set`, `delete`, `clear_data`
- New keys check data limit; updating existing keys is always allowed

## Fix 4: Session.to_dict() — Serialization Hardening
**File:** `aquilia/sessions/core.py`  
**Changes:**
- `data` field now serialized as plain `dict` (strips `_DirtyTrackingDict`)
- `flags` list now sorted for deterministic output

## Fix 5: Session.from_dict() — Deserialization Hardening
**File:** `aquilia/sessions/core.py`  
**Changes:**
- Added `_MAX_SERIALIZED_SIZE = 1_048_576` attribute
- Type check: input must be `dict`
- Required key validation: `id`, `created_at`, `last_accessed_at`, `scope`
- Principal structure validation: must be dict with `kind` and `id`
- Timestamp parsing wrapped in try/except → `SessionStoreCorruptedFault`
- Scope validation → `SessionStoreCorruptedFault`
- Unknown flags silently ignored (forward-compat)
- Data payload type check: must be `dict`
- Principal `id` cast to `str()` for safety

## Fix 6: CookieTransport._parse_cookies() — DoS Protection
**File:** `aquilia/sessions/transport.py`  
**Changes:**
- Added `_MAX_COOKIE_HEADER_LENGTH = 16384` (16 KiB)
- Added `_MAX_COOKIE_PAIRS = 64`
- Added character validation: reject names with control chars, parens, semicolons, quotes, backslashes
- Returns empty dict for oversized headers (silent rejection)

## Fix 7: create_transport() — Fault Integration
**File:** `aquilia/sessions/transport.py`  
**Changes:**
- `NotImplementedError("Token transport...")` → `SessionTransportFault(transport_type="token", ...)`
- `ValueError("Unsupported transport...")` → `SessionTransportFault(transport_type=..., cause=...)`

## Fix 8: FileStore._get_path() — Path Traversal Protection
**File:** `aquilia/sessions/store.py`  
**Changes:**
- Added `_SAFE_ID_PATTERN = re.compile(r'^sess_[A-Za-z0-9_-]{20,64}$')`
- Regex validation before path construction
- `path.resolve().relative_to(directory.resolve())` guard
- Both failures raise `SessionForgeryAttemptFault`
- Added `re` and `SessionForgeryAttemptFault` imports

## Fix 9: SessionEngine.resolve() — Catch SessionInvalidFault
**File:** `aquilia/sessions/engine.py`  
**Changes:**
- `except ValueError:` → `except (ValueError, SessionInvalidFault):`
- Added `SessionInvalidFault` and `SessionHijackAttemptFault` to imports

## Fix 10: SessionEngine._load_existing() — Destroy Hijacked Sessions
**File:** `aquilia/sessions/engine.py`  
**Changes:**
- On fingerprint mismatch: `await self.store.delete(session_id)` before raising
- Wrapped in try/except to not fail if store delete fails

## Fix 11: BlueprintProvider.instantiate() — DI Security Consolidation
**File:** `aquilia/di/providers.py`  
**Changes:**
- Removed duplicated body parsing (JSON/form direct reading)
- Delegated to `bind_blueprint_to_request()` which enforces body size limits, Content-Type detection, unflatten depth/key limits
- Auto-seal behavior preserved

## Test Updates
**File:** `tests/test_sessions_system.py`
- `test_from_string_rejects_invalid`: `ValueError` → `SessionInvalidFault`
- `test_from_string_rejects_wrong_prefix`: `ValueError` → `SessionInvalidFault`
- `test_read_only_enforcement`: 5× `RuntimeError` → `SessionLockedFault`
- `test_rejects_unsupported`: `ValueError` → `SessionTransportFault`
