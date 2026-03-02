# Crous — Python API Documentation

> A compact, canonical binary serializer and human-readable alternative to JSON.

**Version:** 1.0.0 · **Python:** ≥ 3.10 · **License:** MIT OR Apache-2.0

---s

## Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [Pure Python API](#pure-python-api)
   - [encode / decode](#encode--decode)
   - [File I/O (load / dump)](#file-io-load--dump)
   - [Value](#value)
   - [Encoder](#encoder)
   - [Decoder](#decoder)
   - [Text Format](#text-format)
   - [Limits](#limits)
   - [Wire Types](#wire-types)
   - [Varint Utilities](#varint-utilities)
   - [Checksum Utilities](#checksum-utilities)
   - [Errors](#errors)
5. [Native Extension API (PyO3)](#native-extension-api-pyo3)
   - [encode / decode](#native-encode--decode)
   - [File I/O](#native-file-io)
   - [Encoder Class](#native-encoder-class)
   - [CrousDecoder Class](#native-crousdecoder-class)
6. [Interoperability](#interoperability)
7. [Performance Notes](#performance-notes)

---

## Overview

Crous provides two Python packages:

| Package | Type | Import | Description |
|---------|------|--------|-------------|
| `crous` | Pure Python | `import crous` | Full-featured encoder, decoder, text parser, and all utilities. Zero external dependencies for core functionality. |
| `_crous_native` | PyO3 extension | `import _crous_native` | Rust-backed high-performance encoder/decoder. Built with `maturin`. |

Both produce **wire-compatible** output — data encoded with one can be decoded by the other, and by the Rust library.

## Installation

### Pure Python

```bash
cd python/
pip install -e .
```

### Native Extension (PyO3)

```bash
cd crous-python/
pip install maturin
maturin develop --release
```

---

## Quick Start

### Pure Python

```python
import crous

# Encode any Python object
data = crous.encode({"name": "Alice", "age": 30, "active": True})

# Decode back to Python
obj = crous.decode(data)
# → {'name': 'Alice', 'age': 30, 'active': True}
```

### Native Extension

```python
import _crous_native as cn

data = cn.encode({"name": "Alice", "age": 30})
obj = cn.decode(data)
# → {'name': 'Alice', 'age': 30}
```

---

## Pure Python API

### `encode` / `decode`

```python
from crous import encode, decode
```

#### `encode(obj) → bytes`

Encode a Python object to Crous binary format.

**Supported types:** `dict`, `list`, `tuple`, `str`, `int`, `float`, `bool`, `None`, `bytes`, `bytearray`.

```python
data = encode({"users": [{"name": "Alice"}, {"name": "Bob"}]})
assert data[:7] == b"CROUSv1"
```

#### `decode(data) → object`

Decode Crous binary bytes back to a native Python object.

Returns a single value if the data contains one top-level value, or a list otherwise.

```python
obj = decode(data)
assert obj == {"users": [{"name": "Alice"}, {"name": "Bob"}]}
```

---

### File I/O (`load` / `dump`)

```python
from crous import load, dump, load_values, dump_values, append
```

These functions provide a familiar `json.load()` / `json.dump()` style API for reading and writing `.crous` files directly from/to disk.

#### `dump(obj, path) → int`

Encode a Python object and write it to a `.crous` file. Returns bytes written.

```python
import crous

n = crous.dump({"name": "Alice", "age": 30}, "data.crous")
print(f"Wrote {n} bytes")
```

#### `load(path) → object`

Read and decode a `.crous` file, returning native Python objects.

```python
obj = crous.load("data.crous")
# → {'name': 'Alice', 'age': 30}
```

#### `dump_values(values, path) → int`

Write `Value` objects to a file, preserving Crous type information.

```python
from crous.value import Value

crous.dump_values([Value.str_("hello"), Value.uint(42)], "multi.crous")
```

#### `load_values(path) → list[Value]`

Read a file and return `Value` objects (lossless round-trip).

```python
values = crous.load_values("multi.crous")
print(values[0].type)  # ValueType.STR
```

#### `append(obj, path) → int`

Append a value to an existing `.crous` file (or create a new one).

```python
crous.dump({"event": "start"}, "log.crous")
crous.append({"event": "stop"}, "log.crous")
result = crous.load("log.crous")
# → [{'event': 'start'}, {'event': 'stop'}]
```

| Function | Description |
|----------|-------------|
| `dump(obj, path) → int` | Encode Python object and write to file |
| `load(path) → object` | Read file and return Python objects |
| `dump_values(values, path) → int` | Write `Value` objects to file |
| `load_values(path) → list[Value]` | Read file and return `Value` objects |
| `append(obj, path) → int` | Append value to existing file |

---

### `Value`

```python
from crous.value import Value, ValueType
```

The `Value` class provides explicit type discrimination matching the Crous wire format. This ensures lossless round-trips (e.g., `uint` vs `int`).

#### Constructors

| Factory | Type | Example |
|---------|------|---------|
| `Value.null()` | `NULL` | `Value.null()` |
| `Value.bool_(v)` | `BOOL` | `Value.bool_(True)` |
| `Value.uint(v)` | `UINT` | `Value.uint(42)` |
| `Value.int_(v)` | `INT` | `Value.int_(-1)` |
| `Value.float_(v)` | `FLOAT` | `Value.float_(3.14)` |
| `Value.str_(v)` | `STR` | `Value.str_("hello")` |
| `Value.bytes_(v)` | `BYTES` | `Value.bytes_(b"\x00\x01")` |
| `Value.array(items)` | `ARRAY` | `Value.array([Value.uint(1), Value.uint(2)])` |
| `Value.object(entries)` | `OBJECT` | `Value.object([("key", Value.str_("val"))])` |

#### Conversion Methods

| Method | Description |
|--------|-------------|
| `Value.from_python(obj)` | Convert `dict`/`list`/`str`/`int`/`float`/`bool`/`None`/`bytes` to `Value` |
| `value.to_python()` | Convert back to native Python types |
| `value.to_json()` | Convert to JSON-compatible Python object (bytes → base64 string) |
| `Value.from_json(obj)` | Alias for `from_python` |
| `value.to_json_string(pretty=False)` | Serialize to JSON string |

#### Type Mapping

| Python type | Crous Value | Notes |
|-------------|-------------|-------|
| `None` | `Null` | |
| `bool` | `Bool` | Checked before `int` (Python `bool` subclasses `int`) |
| `int` ≥ 0 | `UInt` | Unsigned 64-bit |
| `int` < 0 | `Int` | Signed 64-bit (ZigZag encoded) |
| `float` | `Float` | IEEE 754 double, 8 bytes LE |
| `str` | `Str` | UTF-8 encoded, length-prefixed |
| `bytes` | `Bytes` | Raw binary, length-prefixed |
| `list`/`tuple` | `Array` | Recursive |
| `dict` | `Object` | Preserves insertion order |

#### Properties

```python
v = Value.uint(42)
v.type   # ValueType.UINT
v.data   # 42
```

#### Equality

```python
Value.uint(42) == Value.uint(42)   # True
Value.uint(42) == Value.int_(42)   # False (different types!)
```

---

### `Encoder`

```python
from crous.encoder import Encoder, Limits
```

#### Basic Usage

```python
enc = Encoder()
enc.encode_value(Value.from_python({"key": "value"}))
data = enc.finish()
```

#### With String Deduplication

```python
enc = Encoder()
enc.enable_dedup()
enc.encode_value(Value.array([
    Value.str_("repeated"),
    Value.str_("repeated"),  # stored as Reference
]))
data = enc.finish()
```

#### Constructor

```python
Encoder(limits: Limits | None = None)
```

#### Methods

| Method | Description |
|--------|-------------|
| `encode_value(value: Value)` | Encode a Value into the current block |
| `enable_dedup()` | Enable string deduplication |
| `set_compression(CompressionType)` | Set block compression type |
| `set_flags(int)` | Set file header flags |
| `flush_block() → int` | Flush current block, return bytes written |
| `finish() → bytes` | Finalize and return complete binary output |
| `current_size() → int` | Current output size including unflushed data |

---

### `Decoder`

```python
from crous.decoder import Decoder
```

#### Basic Usage

```python
dec = Decoder(data)
value = dec.decode_next()   # Value
obj = value.to_python()     # dict/list/str/int/...
```

#### Decode All

```python
dec = Decoder(data)
values = dec.decode_all()   # list[Value]
```

#### Constructor

```python
Decoder(data: bytes | bytearray | memoryview, limits: Limits | None = None)
```

#### Methods

| Method | Description |
|--------|-------------|
| `decode_next() → Value` | Decode the next value (reads blocks automatically) |
| `decode_all() → list[Value]` | Decode all remaining values |
| `header() → dict` | Parse and return the file header |

#### Properties

| Property | Description |
|----------|-------------|
| `memory_used` | Cumulative tracked memory allocation |
| `position` | Current byte offset in input |

#### Behavior

- Automatically reads the `CROUSv1` header on first decode.
- Verifies XXH64 checksums on each block.
- Resolves `Reference` wire types from the per-block string dictionary.
- Enforces all `Limits` (nesting depth, memory, block size, string length, item count).
- Non-data blocks are skipped transparently.

---

### `Text Format`

```python
from crous.text import parse, pretty_print
```

#### `parse(text: str) → Value`

Parse a Crous text document into a `Value`.

```python
v = parse('{ name: "Alice"; age: 30; scores: [100, 95]; }')
```

#### `pretty_print(value: Value, indent: int = 2) → str`

Pretty-print a `Value` in canonical Crous text notation.

```python
text = pretty_print(v, indent=4)
# {
#     name: "Alice";
#     age: 30;
#     scores: [100, 95];
# }
```

#### Text Syntax

```
Objects:   { key: value; key2: value2; }    (semicolons required)
Arrays:    [a, b, c]                        (commas as separators)
Strings:   "hello world"                    (double-quoted, with escapes)
Binary:    b64#AQID;                        (base64 with ; terminator)
Numbers:   42, -1, 3.14, 1e10              (uint, int, float)
Keywords:  null, true, false
Annotate:  42::u32, "x"::str               (optional, ignored by parser)
Comments:  // line   /* block (nested) */
```

---

### `Limits`

```python
from crous.encoder import Limits
```

```python
@dataclass
class Limits:
    max_nesting_depth: int = 128
    max_block_size: int = 64 * 1024 * 1024     # 64 MiB
    max_items: int = 1_000_000
    max_memory: int = 256 * 1024 * 1024        # 256 MiB
    max_string_length: int = 16 * 1024 * 1024  # 16 MiB
```

| Factory | Description |
|---------|-------------|
| `Limits()` | Default limits |
| `Limits.strict()` | Restrictive limits for untrusted input |
| `Limits.unlimited()` | No limits (trusted data only) |

Both `Encoder` and `Decoder` accept an optional `limits` parameter.

---

### `Wire Types`

```python
from crous.wire import WireType, BlockType, CompressionType
```

#### `WireType` (enum)

| Name | Value | Description |
|------|-------|-------------|
| `NULL` | `0x00` | No payload |
| `BOOL` | `0x01` | 1 byte |
| `VAR_UINT` | `0x02` | LEB128 varint |
| `VAR_INT` | `0x03` | ZigZag + LEB128 |
| `FIXED64` | `0x04` | 8 bytes LE |
| `LEN_DELIMITED` | `0x05` | subtype + len + data |
| `START_OBJECT` | `0x06` | count + entries |
| `END_OBJECT` | `0x07` | marker |
| `START_ARRAY` | `0x08` | count + items |
| `END_ARRAY` | `0x09` | marker |
| `REFERENCE` | `0x0A` | varint dict index |

#### `BlockType` (enum)

| Name | Value |
|------|-------|
| `DATA` | `0x01` |
| `INDEX` | `0x02` |
| `SCHEMA` | `0x03` |
| `STRING_DICT` | `0x04` |
| `TRAILER` | `0xFF` |

#### `CompressionType` (enum)

| Name | Value |
|------|-------|
| `NONE` | `0x00` |
| `ZSTD` | `0x01` |
| `SNAPPY` | `0x02` |
| `LZ4` | `0x03` |

---

### `Varint Utilities`

```python
from crous.varint import (
    encode_varint, decode_varint,
    zigzag_encode, zigzag_decode,
    encode_signed_varint, decode_signed_varint,
)
```

| Function | Description |
|----------|-------------|
| `encode_varint(value: int) → bytes` | Encode unsigned int as LEB128 |
| `decode_varint(data, offset) → (int, int)` | Decode LEB128, returns `(value, bytes_consumed)` |
| `zigzag_encode(value: int) → int` | ZigZag encode signed → unsigned |
| `zigzag_decode(value: int) → int` | ZigZag decode unsigned → signed |
| `encode_signed_varint(value: int) → bytes` | ZigZag + LEB128 encode |
| `decode_signed_varint(data, offset) → (int, int)` | ZigZag + LEB128 decode |

---

### `Checksum Utilities`

```python
from crous.checksum import compute_xxh64, verify_xxh64
```

| Function | Description |
|----------|-------------|
| `compute_xxh64(data: bytes) → int` | Compute XXH64 hash (seed=0) |
| `verify_xxh64(data: bytes, expected: int) → bool` | Verify XXH64 hash |

Reference vectors:

```python
assert compute_xxh64(b"") == 0xEF46DB3751D8E999
assert compute_xxh64(b"hello") == 0x26C7827D889F6DA3
```

---

### `Errors`

```python
from crous.error import (
    CrousError,            # Base class
    InvalidMagicError,     # Bad file header
    ChecksumMismatchError, # Block checksum failed
    NestingTooDeepError,   # Exceeded max_nesting_depth
    UnexpectedEofError,    # Truncated input
    MemoryLimitError,      # Exceeded max_memory or max_string_length
)
```

All errors inherit from `CrousError`.

---

## Native Extension API (PyO3)

The `_crous_native` module provides Rust-backed encoding/decoding for maximum performance.

```python
import _crous_native as cn
```

### Native `encode` / `decode`

#### `cn.encode(obj) → bytes`

Encode a Python object to Crous binary. Accepts: `dict`, `list`, `str`, `int`, `float`, `bool`, `None`, `bytes`.

```python
data = cn.encode({"name": "Alice", "age": 30})
```

Raises `TypeError` for unsupported types, `RuntimeError` for encoding errors.

#### `cn.decode(data: bytes) → object`

Decode Crous binary back to Python objects. Returns a single value if one top-level value, otherwise a list.

```python
obj = cn.decode(data)  # → {'name': 'Alice', 'age': 30}
```

### Native File I/O

#### `cn.encode_to_file(obj, path: str) → int`

Encode a Python object and write it to a `.crous` file. Returns bytes written.

```python
cn.encode_to_file({"name": "Alice", "age": 30}, "data.crous")
```

#### `cn.decode_from_file(path: str) → object`

Read and decode a `.crous` file, returning native Python objects.

```python
obj = cn.decode_from_file("data.crous")
# → {'name': 'Alice', 'age': 30}
```

Raises `FileNotFoundError` if the file does not exist.

#### `cn.append_to_file(obj, path: str) → int`

Append a value to an existing `.crous` file (or create a new one). Returns bytes written.

```python
cn.encode_to_file({"event": "start"}, "log.crous")
cn.append_to_file({"event": "stop"}, "log.crous")
cn.decode_from_file("log.crous")
# → [{'event': 'start'}, {'event': 'stop'}]
```

| Function | Description |
|----------|-------------|
| `cn.encode_to_file(obj, path) → int` | Encode and write to file |
| `cn.decode_from_file(path) → object` | Read and decode from file |
| `cn.append_to_file(obj, path) → int` | Append value to existing file |

### Native `Encoder` Class

```python
enc = cn.Encoder()
```

| Method | Description |
|--------|-------------|
| `enable_dedup()` | Enable string deduplication |
| `set_compression(name: str)` | Set compression: `"none"`, `"lz4"`, `"zstd"`, `"snappy"` |
| `encode(obj)` | Encode a Python value |
| `finish() → bytes` | Finalize and return bytes. **Encoder is consumed.** |

```python
enc = cn.Encoder()
enc.enable_dedup()
enc.set_compression("lz4")
enc.encode({"key": "value"})
data = enc.finish()
# enc.encode(...) → RuntimeError: encoder already finished
```

### Native `CrousDecoder` Class

```python
dec = cn.CrousDecoder(data)
```

| Method | Description |
|--------|-------------|
| `decode_all() → list` | Decode all values. **Decoder is consumed.** |

```python
dec = cn.CrousDecoder(data)
values = dec.decode_all()  # list of Python objects
# dec.decode_all() → RuntimeError: decoder already consumed
```

---

## Interoperability

### Python ↔ Rust Parity

Data encoded by one implementation can be decoded by any other:

```python
# Pure Python → Native Rust
import crous
import _crous_native as cn

data_py = crous.encode({"name": "Alice"})
obj = cn.decode(data_py)
assert obj == {"name": "Alice"}

# Native Rust → Pure Python
data_rs = cn.encode({"name": "Bob"})
obj = crous.decode(data_rs)
assert obj == {"name": "Bob"}
```

### String Deduplication Interop

Both implementations produce compatible dedup-encoded output:

```python
# Python dedup
import crous
from crous.encoder import Encoder
from crous.value import Value

enc = Encoder()
enc.enable_dedup()
enc.encode_value(Value.array([Value.str_("x"), Value.str_("x")]))
data = enc.finish()

# Rust decode
import _crous_native as cn
assert cn.decode(data) == ["x", "x"]
```

### Wire Format

The file always starts with `b"CROUSv1"` (7 bytes) + flags byte, making it trivial to detect:

```python
def is_crous(data: bytes) -> bool:
    return data[:7] == b"CROUSv1"
```

---

## Performance Notes

The pure Python implementation is fully functional and spec-compliant but optimized for clarity, not speed. For performance-critical workloads, use the native extension:

| Operation | Pure Python | Native (PyO3/Rust) | Speedup |
|-----------|-------------|---------------------|---------|
| Encode small dict | ~100 µs | ~5 µs | ~20× |
| Decode small dict | ~80 µs | ~4 µs | ~20× |
| Encode 1000 objects | ~50 ms | ~2 ms | ~25× |

The native extension uses the same `crous-core` Rust library that powers the CLI and FFI bindings, ensuring identical behavior and wire format compatibility.

**Recommendation:** Use `_crous_native` (via `maturin develop`) for production workloads. Use `crous` (pure Python) for learning, debugging, prototyping, and environments where a Rust toolchain is unavailable.

---

*Generated from Crous v1.1.0 Python codebase. See `docs/SPEC.md` for the full wire format specification.*
s