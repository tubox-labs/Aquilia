"""Micro-benchmarks for aquilia._json vs stdlib json.

Measures the actual speedup from the native JSON encoder/decoder by comparing
identical operations through both paths. The HTTP benchmarks measure the whole
stack; these benchmarks measure only the JSON layer.
"""

from __future__ import annotations

import json as stdlib_json
import statistics
import timeit
from typing import Any

try:
    import aquilia._json as native_json
    HAS_NATIVE = True
except ImportError:
    HAS_NATIVE = False
    native_json = None  # type: ignore


SMALL_DICT = {"message": "Hello, World!", "status": 200, "timestamp": 1625097600}

NESTED_DICT = {
    "user": {"id": 12345, "username": "testuser", "email": "test@example.com"},
    "posts": [
        {"id": 1, "title": "First Post", "likes": 42},
        {"id": 2, "title": "Second Post", "likes": 17},
    ],
    "metadata": {"version": "1.0", "created": "2021-07-01"},
}

# 100KB nested structure
LARGE_DICT = {
    "items": [{"id": i, "name": f"item_{i}", "value": i * 1.5} for i in range(2000)]
}


def bench_encode(obj: Any, label: str, iterations: int = 10000) -> dict[str, float]:
    """Time JSON encoding stdlib vs native."""
    stdlib_samples = timeit.repeat(lambda: stdlib_json.dumps(obj), number=iterations, repeat=5)
    stdlib_us = min(stdlib_samples) / iterations * 1e6

    if not HAS_NATIVE:
        return {"stdlib_us": stdlib_us, "native_us": 0.0, "speedup": 0.0}

    native_samples = timeit.repeat(lambda: native_json.dumps(obj), number=iterations, repeat=5)
    native_us = min(native_samples) / iterations * 1e6

    speedup = stdlib_us / native_us if native_us > 0 else 0.0
    return {"stdlib_us": stdlib_us, "native_us": native_us, "speedup": speedup}


def bench_decode(json_str: str, label: str, iterations: int = 10000) -> dict[str, float]:
    """Time JSON decoding stdlib vs native."""
    stdlib_samples = timeit.repeat(lambda: stdlib_json.loads(json_str), number=iterations, repeat=5)
    stdlib_us = min(stdlib_samples) / iterations * 1e6

    if not HAS_NATIVE:
        return {"stdlib_us": stdlib_us, "native_us": 0.0, "speedup": 0.0}

    native_samples = timeit.repeat(lambda: native_json.loads(json_str), number=iterations, repeat=5)
    native_us = min(native_samples) / iterations * 1e6

    speedup = stdlib_us / native_us if native_us > 0 else 0.0
    return {"stdlib_us": stdlib_us, "native_us": native_us, "speedup": speedup}


def main() -> None:
    if not HAS_NATIVE:
        print("ERROR: aquilia._json not found. Build with `pip install -e .`")
        return

    print("=" * 60)
    print("JSON Encoding Benchmarks (μs per operation)")
    print("=" * 60)

    for name, obj, iters in [
        ("small_dict", SMALL_DICT, 10000),
        ("nested_dict", NESTED_DICT, 10000),
        ("large_dict", LARGE_DICT, 1000),
    ]:
        result = bench_encode(obj, name, iters)
        print(f"{name:20} stdlib={result['stdlib_us']:7.2f}  native={result['native_us']:7.2f}  speedup={result['speedup']:5.2f}x")

    print()
    print("=" * 60)
    print("JSON Decoding Benchmarks (μs per operation)")
    print("=" * 60)

    small_json = stdlib_json.dumps(SMALL_DICT)
    nested_json = stdlib_json.dumps(NESTED_DICT)
    large_json = stdlib_json.dumps(LARGE_DICT)

    for name, json_str, iters in [
        ("small_dict", small_json, 10000),
        ("nested_dict", nested_json, 10000),
        ("large_dict", large_json, 1000),
    ]:
        result = bench_decode(json_str, name, iters)
        print(f"{name:20} stdlib={result['stdlib_us']:7.2f}  native={result['native_us']:7.2f}  speedup={result['speedup']:5.2f}x")


if __name__ == "__main__":
    main()
