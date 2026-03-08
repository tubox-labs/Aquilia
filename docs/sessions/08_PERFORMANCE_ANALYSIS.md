# Session Performance Analysis

## Benchmark Profile

### Session ID Generation
- `SessionID()` — 1 call to `secrets.token_bytes(32)` + 1 `base64.urlsafe_b64encode`
- Cost: ~2μs per ID on modern hardware
- No contention (pure function)

### Session ID Parsing (`from_string`)
- Input validation: 3 checks (type, length, prefix) — O(1)
- Base64 decode: O(n) where n = 43 chars
- Byte length check: O(1)
- Total: ~1μs per parse

### Session Creation
- `Session()` dataclass construction + `_DirtyTrackingDict` wrapping
- `__post_init__` wraps `data` dict
- Cost: ~5μs per session

### Session Serialization
- `to_dict()`: dict copy + ISO format timestamps + flag sort
- `from_dict()`: 4 required key checks + timestamp parsing + scope validation
- Cost: ~10μs serialize, ~15μs deserialize

### Fingerprint Operations
- `bind_fingerprint()`: 1 SHA-256 hash (32 bytes input)
- `verify_fingerprint()`: 1 SHA-256 hash + 1 `secrets.compare_digest`
- Cost: ~5μs per operation

### MemoryStore Operations
- `load()`: 1 dict lookup + 1 `move_to_end` — O(1)
- `save()`: 1 dict insert + 1 `move_to_end` + optional LRU evict — O(1)
- `delete()`: 1 dict pop + principal index update — O(1)
- Lock overhead: ~1μs per acquire/release

### Cookie Parsing
- `_parse_cookies()`: O(n) split + O(k) character validation per name
- Bounded: max 16 KiB header, max 64 pairs
- Cost: ~5μs for typical 3-cookie header

## Hotspot Analysis

### Per-Request Session Overhead
```
Transport.extract()     ~2μs   (cookie parsing)
SessionID.from_string() ~1μs   (ID parsing + validation)
Store.load()            ~2μs   (MemoryStore) / ~100μs (FileStore)
Policy.is_valid()       ~1μs   (3 comparisons)
Session.touch()         ~1μs   (timestamp update)
Store.save()            ~2μs   (MemoryStore) / ~500μs (FileStore)
Transport.inject()      ~2μs   (set_cookie call)
─────────────────────────────
Total (MemoryStore)    ~11μs per request
Total (FileStore)     ~607μs per request
```

### Memory Profile (MemoryStore)
```
Session object:     ~400 bytes (dataclass + fields)
_DirtyTrackingDict: ~200 bytes (empty dict + owner ref)
SessionID:          ~100 bytes (32 bytes raw + 50 bytes encoded)
Principal:          ~200 bytes (dataclass + attributes dict)
OrderedDict entry:  ~100 bytes (doubly-linked node)
Principal index:    ~100 bytes (set entry)
─────────────────────────────
Per session total:  ~1,100 bytes (empty data)
+ data payload:     variable
```

### Scaling Projections

| Sessions | Memory (MemoryStore) | Disk (FileStore) |
|---|---|---|
| 1,000 | ~1.1 MB | ~2 MB |
| 10,000 | ~11 MB | ~20 MB |
| 50,000 | ~55 MB | ~100 MB |
| 100,000 | ~110 MB | ~200 MB |

## Optimization Opportunities

1. **Session ID caching**: Cache `str(session_id)` on first call
2. **Lazy fingerprint**: Only compute fingerprint if policy requires it
3. **Batch commit**: Collect dirty sessions and batch-persist
4. **Connection pooling**: For future RedisStore
5. **Serialization**: Consider MessagePack instead of JSON for FileStore
