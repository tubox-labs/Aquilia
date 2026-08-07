# Bug Fixes & Root Cause Analysis — v1.4.0b1

Aquilia v1.4.0b1 resolves critical bugs across the routing, database, memory management, and build layers. 

---

## 1. `validate_body` Double-Bind Overhead
**Previous Behavior:**
Endpoints utilizing the `@validate_body` decorator exhibited unexpectedly low throughput.
**Root Cause:**
The decorator correctly parsed the incoming HTTP body and validated it against a contract. However, it did not communicate this state to the core Controller Engine. The Controller Engine then attempted to resolve the `body` parameter via its own dependency injection graph. This caused a duplicate parse, a duplicate validation, and threw an internal `"got multiple values for keyword argument 'body'"` exception, which the framework swallowed and recovered from.
**New Behavior:**
`validate_body` now writes its output to `request.validated_data`. The Controller Engine checks for this cached state before binding.
**User Impact:**
Massive performance boost. Validation endpoints jumped from 1,809 RPS to 15,075 RPS. No user code changes required.

---

## 2. `Response.json` String vs. Bytes Double-Encoding
**Previous Behavior:**
`Response.json` would serialize the payload twice if `orjson` was not installed.
**Root Cause:**
ASGI specifications dictate that the body payload sent over the socket must be raw `bytes`. The fallback JSON encoder in previous versions returned a Python `str`. `Response.json` checked the type, saw a string, and called `.encode('utf-8')`. For a 100KB payload, this meant allocating a 100KB string, and then a 100KB byte array, effectively doubling memory usage and CPU time.
**New Behavior:**
The new `aquilia.json` codec strictly returns `bytes`. `Response.json` streams this directly.
**User Impact:**
Reduced memory footprint and 3.9x faster encoding for large payloads.

---

## 3. `_check_json_depth` Recursion 
**Previous Behavior:**
Deeply nested JSON payloads crashed the server process.
**Root Cause:**
`_check_json_depth` was implemented recursively. A payload nested hundreds of levels deep would trigger a `RecursionError` (blowing the Python call stack). This resulted in an unhandled 500 Internal Server Error, bypassing standard validation 400s.
**New Behavior:**
The depth checker now uses an iterative stack approach, which cannot overflow the call stack.
**User Impact:**
Secure handling of malicious JSON depth attacks. Proper `400 Bad Request` responses are issued.

---

## 4. Benchmark `successRate` Miscalculation
**Previous Behavior:**
Benchmarks reported 100% success even when endpoints were silently failing.
**Root Cause:**
The benchmark harness relied on `oha`'s internal `successRate` metric, which sometimes evaluated HTTP 4xx and 5xx responses as "successful" socket connections.
**New Behavior:**
The harness now performs a preflight HTTP call, checks for a strict `2xx`/`3xx` status code, and halts immediately if the application returns an error. 
**User Impact:**
Accurate performance metrics moving forward.

---

## 5. SWAR Mask String Corruption
**Previous Behavior:**
During the development of the native JSON engine, strings containing non-ASCII (e.g., emojis, foreign characters) were truncated or corrupted.
**Root Cause:**
The SIMD Within A Register (SWAR) string scanner used an overly aggressive bitmask. It interpreted any byte `>= 0x80` as a control character requiring escaping.
**New Behavior:**
The SWAR mask was refined to target only true JSON control characters (`0x00`-`0x1F`), double quotes, and backslashes.
**User Impact:**
Memory-safe, high-speed encoding of UTF-8 data.

---

## 6. Bignum Decoding Precision Loss
**Previous Behavior:**
Numbers larger than `2**64` lost precision upon deserialization.
**Root Cause:**
C parsers (like `yyjson`) default to standard IEEE 754 doubles for numbers that exceed 64-bit integer limits. Python's `int` has arbitrary precision, meaning precision was being thrown away needlessly.
**New Behavior:**
`YYJSON_READ_BIGNUM_AS_RAW` is flagged during parsing. Bignums are read as raw strings and cast directly to Python `int`.
**User Impact:**
Financial and scientific applications can safely process massive integers.

---

## 7. Nested Container Key Overwrite
**Previous Behavior:**
Parsing `{"a": {"b": 1}, "c": 2}` resulted in `{"b": 1, "c": 2}`. Key `"a"` vanished.
**Root Cause:**
The non-recursive heap work stack in the `yyjson` wrapper used a single variable to track the "active key". Returning from the nested `"b"` object overwrote the `"a"` key state.
**New Behavior:**
Key state is pushed onto the frame stack, preserving hierarchy.
**User Impact:**
100% parity with standard library JSON parsing.

---

## 8. RequestContext GC Leak (`tp_traverse`)
**Previous Behavior:**
The framework leaked exactly one `RequestCtx` object per HTTP request.
**Root Cause:**
`RequestCtx` held references to the application state, creating a cyclic reference. The class was bound using `nanobind`. However, `nanobind`'s `inst_traverse` feature had limitations in exposing these cycles to the Python Garbage Collector.
**New Behavior:**
The native extension implements raw Python C-API `tp_traverse` and `tp_clear` slot methods, allowing the Python GC to correctly identify and break the cycle.
**User Impact:**
Memory usage remains flat over millions of requests.

---

## 9. DotEnvLoader Reset State
**Previous Behavior:**
Environment variables bled across test suites during hot-reloads.
**Root Cause:**
`DotEnvLoader` maintained static state that was not flushed upon reset.
**New Behavior:**
`DotEnvLoader.reset()` forcefully purges the internal cache.
**User Impact:**
Clean isolation for testing and dev-server hot-reloads.

---

## 10. Windows CI Compatibility & Python 3.13 Thread Starvation
**Previous Behavior:**
CI failed on Windows runners; Python 3.13 preview exhibited thread stalls.
**Root Cause:**
Windows MSVC compilation flags were overly strict regarding standard library imports in the `_core` C++ code. Python 3.13 GIL changes impacted `asyncio.wait_for` wrappers in the SQLite pool.
**New Behavior:**
MSVC `/O2` and compatible headers applied. The SQLite inline execution engine (see [Performance](performance.md)) completely bypasses the thread-starvation vector.
**User Impact:**
Full support for Windows and forward compatibility with Python 3.13.
