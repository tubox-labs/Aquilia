# JSON Engine — v1.4.0b1

Aquilia v1.4.0b1 replaces its dependency on third-party libraries (`orjson`, `ujson`) with a bespoke, deeply integrated native JSON engine located at `aquilia/_json`. This engine is backed by a vendored copy of `yyjson 0.10.0` (MIT license), widely recognized as one of the fastest JSON libraries available in C.

## Architecture

The C++ extension is designed for zero-allocation parsing and direct, high-speed emission. It consists of five core header/source pairs:

### 1. `decode.cpp` (Arena Parsing)
Deserialization leverages `yyjson`'s arena allocator. Instead of allocating memory for every parsed string or object individually, the parser allocates large contiguous chunks of memory (arenas) and parses the entire document into this space. The Python layer then rapidly traverses this immutable tree to instantiate Python objects.

### 2. `encode.cpp` (Direct Emitter & Heap Work Stack)
Serialization uses a direct emitter. It does not build an intermediate JSON document tree in memory; it streams characters directly into a buffer. 

Crucially, **the encoder is not recursive**. Recursive encoding in C++ is a severe security vector; a maliciously nested JSON object (e.g., `{"a": {"a": {"a": ...}}}`) can cause a stack overflow, instantly crashing the server process. `encode.cpp` manages its traversal state using a heap-allocated work stack, completely immunizing the framework from JSON depth attacks.

### 3. `escape.hpp` (SWAR Word-At-A-Time Scan)
When encoding strings, the engine must identify characters that require JSON escaping (like `"`, `\`, or control characters). Iterating byte-by-byte is slow. `escape.hpp` uses SWAR (SIMD Within A Register). By treating an 8-byte chunk of the string as a single 64-bit integer, it applies bitwise masks to scan 8 characters simultaneously, radically speeding up string serialization.

### 4. `numeric.hpp` (itoa + Shortest Round Trip)
Converting integers to strings uses highly optimized custom `itoa` (integer-to-ASCII) routines. For floating-point numbers, it leverages `yyjson`'s shortest-round-trip formatting, ensuring exact IEEE 754 precision without emitting unnecessary trailing decimals.

### 5. `buffer.hpp` (Thread-Local Pool)
Memory allocation during serialization is minimized via a thread-local buffer pool. The engine remembers the largest payload it recently serialized on that thread. Subsequent serializations of similarly sized payloads require zero `malloc()` calls.

---

## Bugs Fixed During Development

Building a custom JSON engine from scratch surfaced complex edge cases, all resolved prior to release:

1. **The SWAR Mask Bug**
   - **Issue:** The SWAR bitwise mask incorrectly flagged every byte `>= 0x80` (any non-ASCII utf-8 sequence) as a control character requiring escaping.
   - **Resolution:** This corrupted the first non-ASCII string encountered in the document. The mask constants were corrected to strictly target `0x00`-`0x1F`, `"`, and `\`.

2. **Bignum Decoding Precision Loss**
   - **Issue:** Standard JSON parsers treat all numbers as doubles if they don't fit in a 64-bit integer. Python integers have arbitrary precision. Integers > `2**64` were being silently cast to doubles, losing exact precision.
   - **Resolution:** The engine now sets `YYJSON_READ_BIGNUM_AS_RAW`. When a bignum is encountered, it is parsed directly from the raw string into a Python arbitrary-precision `int`.

3. **Nested Container Key Overwrite**
   - **Issue:** When parsing nested dictionaries like `{"a": {"b": 1}, "c": 2}`, the state tracking the active key (`"a"`) was lost when popping back up from the nested `{"b": 1}` dictionary.
   - **Resolution:** The active key state is now pushed onto the heap work frame rather than held in a global traversal variable.

---

## Performance

The new engine consistently outpaces standard library json and holds its own against dedicated third-party codecs:

| Benchmark | Speedup | Note |
|-----------|---------|------|
| **Encode Small (1KB)** | **8.5x faster** | Direct emitter eliminates overhead |
| **Encode Large (100KB)** | **3.9x faster** | Buffer pooling avoids `malloc` |
| **Encode 500 Rows** | **4.9x faster** | SWAR string scanning heavily utilized |
| **Decode Small (1KB)** | **4.8x faster** | Arena parser instantiation |
| **Full Framework /json/large** | **+105% RPS** | End-to-end framework throughput |

---

## Usage: The `aquilia.json` Module

Aquilia now provides a single, unified entry point for all JSON operations. You no longer need to import `orjson` or manage fallbacks in your own code.

```python
import aquilia.json

# Serialization (returns bytes)
payload_bytes = aquilia.json.dumps({"status": "ok", "count": 42})

# Deserialization
data = aquilia.json.loads(payload_bytes)
```

### Introspection
You can verify the active backend programmatically:

```python
# Check which backend is powering the codec
print(aquilia.json.backend()) 
# Outputs: 'yyjson' (native) or 'python' (fallback)

# Check if native is active via boolean
if aquilia.json.native:
    print("Running at C-speed!")
```

### The Standard Library Fallback
If the native extension fails to load (e.g., due to architecture mismatch or `AQUILIA_ENGINE_OPTIONAL=ON`), `aquilia.json` transparently patches itself to wrap the Python standard library `json` module. It enforces the exact same API (e.g., `dumps` returns `bytes`, not `str`).

### Testing Approach
To guarantee absolute parity between the `yyjson` C++ implementation and the Python fallback, we implemented a differential fuzzing suite containing 104 tests that generate random, highly complex JSON structures and assert that both backends produce identical Python ASTs.
Furthermore, the engine is backed by 123 Python unit tests and 32 native C++ tests running under strict ASAN, UBSAN, and TSAN configurations.
