# Session Threat Model

## Overview

This document identifies threat vectors targeting the Aquilia session management
system and maps them to mitigations implemented by the framework.

## Threat Actors

| Actor | Capability | Motivation |
|---|---|---|
| External Attacker | Network access, cookie manipulation | Session hijacking, data theft |
| Insider Threat | Local system access | Session forgery, privilege escalation |
| Automated Bot | High volume requests | Brute-force session IDs, DoS |
| Compromised Client | JavaScript execution | XSS-based session theft |

## STRIDE Analysis

### Spoofing
| Threat | Mitigation | Status |
|---|---|---|
| Session ID guessing | 256-bit entropy (2^256 keyspace) | ✅ Mitigated |
| Session ID format abuse | `SessionInvalidFault` + input length limits | ✅ Fixed |
| Cookie injection | Character validation in `_parse_cookies()` | ✅ Fixed |

### Tampering
| Threat | Mitigation | Status |
|---|---|---|
| Session data tampering in store | `from_dict()` strict validation | ✅ Fixed |
| Path traversal in FileStore | Regex + `relative_to()` guard | ✅ Fixed |
| Read-only session bypass | `SessionLockedFault` enforcement | ✅ Fixed |
| Session data overflow | `MAX_DATA_KEYS = 256` limit | ✅ Fixed |

### Repudiation
| Threat | Mitigation | Status |
|---|---|---|
| Untracked session mutations | `_DirtyTrackingDict` auto-detection | ✅ Existing |
| Session event gaps | Engine `_emit_event()` system | ✅ Existing |
| Principal ID spoofing | Identity binding via `SessionPrincipal` | ✅ Existing |

### Information Disclosure
| Threat | Mitigation | Status |
|---|---|---|
| Session ID in logs | `fingerprint()` SHA-256 truncation | ✅ Existing |
| Error message leakage | `SessionInvalidFault` (no internals) | ✅ Fixed |
| Cookie access via JS | `HttpOnly=True` default | ✅ Existing |
| Session data in transit | `Secure=True` cookie flag | ✅ Existing |

### Denial of Service
| Threat | Mitigation | Status |
|---|---|---|
| Giant Cookie header | `_MAX_COOKIE_HEADER_LENGTH = 16384` | ✅ Fixed |
| Cookie pair flooding | `_MAX_COOKIE_PAIRS = 64` | ✅ Fixed |
| Session store exhaustion | `max_sessions` cap + LRU eviction | ✅ Existing |
| Session data bloat | `MAX_DATA_KEYS = 256` limit | ✅ Fixed |

### Elevation of Privilege
| Threat | Mitigation | Status |
|---|---|---|
| Session fixation | ID rotation on privilege change | ✅ Existing |
| Session hijacking (IP change) | Fingerprint binding + session destruction | ✅ Fixed |
| Concurrent session abuse | `ConcurrencyPolicy` enforcement | ✅ Existing |
| Admin session reuse | `ADMIN_POLICY` with strict settings | ✅ Existing |

## Attack Tree

```
Session Compromise
├── Session Hijacking
│   ├── XSS Cookie Theft → Mitigated (HttpOnly)
│   ├── Network Sniffing → Mitigated (Secure flag + HTTPS)
│   ├── IP Spoofing → Mitigated (Fingerprint binding)
│   └── Session Fixation → Mitigated (Rotation on auth change)
├── Session Forgery
│   ├── Brute Force ID → Mitigated (256-bit entropy)
│   ├── Predictable ID → Mitigated (CSPRNG via secrets module)
│   └── Path Traversal → Mitigated (Regex + relative_to guard)
├── Session DoS
│   ├── Store Exhaustion → Mitigated (max_sessions + LRU)
│   ├── Cookie Header Bomb → Mitigated (16 KiB limit)
│   └── Data Key Flooding → Mitigated (256 key limit)
└── Session Data Corruption
    ├── Malformed Deserialization → Mitigated (strict from_dict)
    └── Type Confusion → Mitigated (type validation in from_dict)
```

## Residual Risks

| Risk | Severity | Recommendation |
|---|---|---|
| Session data not encrypted at rest | Low | Add optional AES-GCM encryption |
| No HMAC on serialized sessions | Low | Add HMAC signing to to_dict/from_dict |
| FileStore uses blocking I/O | Low | Use aiofiles or asyncio.to_thread |
| No CSRF token integration | Medium | Add optional CSRF double-submit pattern |
| No rate limiting on session parsing | Low | Add per-IP rate limiting middleware |
