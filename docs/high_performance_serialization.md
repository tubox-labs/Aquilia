# Aquilia Blueprint — High-Performance Serialization

**Module:** `aquilia/blueprints/`  
**Focus:** Performance analysis and optimization strategies  

---

## 1. Performance Profile

### 1.1 Current Bottlenecks

| Operation | Bottleneck | Impact |
|-----------|-----------|--------|
| Blueprint.__init__ | Facet cloning (copy.copy per facet) | O(N) per request |
| is_sealed() | Full iteration over all facets | O(N) per validation |
| to_dict() | Full iteration + projection lookup | O(N) per serialization |
| _seal_many() | N × Blueprint instances | O(N × M) for lists |
| to_schema() | Rebuilds on every call | No caching |

### 1.2 Benchmark Estimates

For a Blueprint with 20 facets, 1000 items:

| Operation | Estimated Time | Memory |
|-----------|---------------|--------|
| Single validation | ~50μs | ~2KB per instance |
| Single mold | ~30μs | ~1KB output |
| Many (1000) validation | ~60ms | ~2MB |
| Many (1000) mold | ~35ms | ~1MB |
| Schema generation | ~100μs | ~5KB |

---

## 2. Optimization Strategies

### 2.1 Facet Binding Optimization

**Current:** Every Blueprint instance clones ALL facets.
```python
for fname, facet in self._all_facets.items():
    bound = facet.clone()  # copy.copy() each time
    bound.bind(fname, self)
    self._bound_facets[fname] = bound
```

**Optimization: Lazy binding with projection filtering**
```python
def __init__(self, ...):
    if projection:
        needed = self._projections.resolve(projection)
        self._bound_facets = {
            fname: facet.clone().tap(lambda f: f.bind(fname, self))
            for fname, facet in self._all_facets.items()
            if fname in needed
        }
    else:
        self._bound_facets = {
            fname: facet.clone().tap(lambda f: f.bind(fname, self))
            for fname, facet in self._all_facets.items()
        }
```

**Expected improvement:** 30-50% for projected Blueprints.

### 2.2 Cast+Seal Fusion

**Current:** Cast and seal are separate passes.
```python
cast_value = facet.cast(raw)
sealed_value = facet.seal(cast_value)
```

**Optimization:** Fuse into single method for simple facets.
```python
class IntFacet(Facet):
    def cast_and_seal(self, value):
        if isinstance(value, bool):
            raise CastFault(...)
        result = int(value)
        if self.min_value is not None and result < self.min_value:
            raise CastFault(...)
        if self.max_value is not None and result > self.max_value:
            raise CastFault(...)
        for validator in self.validators:
            validator(result)
        return result
```

**Expected improvement:** 15-20% fewer function calls.

### 2.3 Schema Caching

**Current:** `to_schema()` rebuilds every call.

**Optimization:** Class-level cache keyed by (projection, mode).
```python
_schema_cache: Dict[tuple, dict] = {}

@classmethod
def to_schema(cls, *, projection=None, mode="output"):
    key = (projection, mode)
    if key in cls._schema_cache:
        return cls._schema_cache[key]
    schema = cls._build_schema(projection=projection, mode=mode)
    cls._schema_cache[key] = schema
    return schema
```

**Expected improvement:** 95%+ on repeated calls.

### 2.4 Batch Mold with __slots__

**Optimization:** Use `__slots__` on intermediate data objects.
```python
class _MoldBuffer:
    __slots__ = ('_data',)
    def __init__(self):
        self._data = {}
```

### 2.5 Vectorized Many-Mode

**Current:** Sequential Blueprint instantiation per item.

**Optimization:** Shared facet binding, per-item data only.
```python
def _seal_many_optimized(self, raise_fault):
    # Clone facets once, rebind per item
    shared_facets = {fname: facet.clone() for fname, facet in self._all_facets.items()}
    for fname, facet in shared_facets.items():
        facet.bind(fname, self)
    
    results = []
    for item in self._input_data:
        validated = self._seal_single_with_shared_facets(item, shared_facets)
        results.append(validated)
```

**Expected improvement:** 60-70% memory reduction for large lists.

---

## 3. Memory Optimization

### 3.1 Facet Memory Layout

Current Facet base has ~15 attributes. With `__slots__`:
```python
class Facet:
    __slots__ = (
        'source', '_required', 'read_only', 'write_only', 'default',
        'allow_null', 'allow_blank', 'label', 'help_text', 'validators',
        'name', 'blueprint', '_bound', '_order',
    )
```

**Expected saving:** ~40% memory per Facet instance (dict → slots).

### 3.2 Projection as Bitmap

Replace `frozenset` projection with bitmap for O(1) field checking:
```python
class ProjectionRegistry:
    def resolve(self, name):
        # Returns a bitmap instead of frozenset
        return self._bitmaps.get(name, self._all_bitmap)
```

---

## 4. Serialization Format Optimization

### 4.1 Direct JSON Writing

Instead of building a dict then serializing:
```python
import io, json

def to_json(self, instance=None):
    buf = io.StringIO()
    buf.write('{')
    first = True
    for fname, facet in self._bound_facets.items():
        if facet.write_only: continue
        value = facet.extract(instance or self.instance)
        molded = facet.mold(value)
        if not first: buf.write(',')
        buf.write(f'"{fname}":')
        json.dump(molded, buf)
        first = False
    buf.write('}')
    return buf.getvalue()
```

**Expected improvement:** 20-30% faster than dict → json.dumps.

### 4.2 orjson Integration

```python
try:
    import orjson
    def to_json_bytes(self, instance=None):
        return orjson.dumps(self.to_dict(instance))
except ImportError:
    pass
```

**Expected improvement:** 3-10x faster JSON serialization.

---

## 5. Benchmark Targets

| Operation | Current (est.) | Target | Strategy |
|-----------|---------------|--------|----------|
| Single validation (20 fields) | 50μs | 25μs | Cast+seal fusion |
| Single mold (20 fields) | 30μs | 15μs | Direct JSON write |
| Many (1000) validation | 60ms | 20ms | Vectorized + shared facets |
| Many (1000) mold | 35ms | 10ms | Vectorized + orjson |
| Schema generation | 100μs | 5μs | Caching |
| Memory per Blueprint | 2KB | 800B | __slots__ + lazy bind |

---

*End of High-Performance Serialization — Phase 10*
