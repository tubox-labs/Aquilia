# Aquilia ORM — Scalability Design

**Version**: 1.0.1 | Phase 9 Security Audit  

---

## 1. Current Scalability Profile

### 1.1 Query Performance Characteristics

| Feature | Implementation | Scalability Impact |
|---------|---------------|-------------------|
| Connection management | Single connection per `AquiliaDatabase` | ⚠️ No connection pooling |
| Query caching | `Q._result_cache` per queryset instance | ✅ Avoids re-execution |
| Chunked iteration | `iterator(chunk_size=N)` | ✅ Memory-efficient for large datasets |
| Batch operations | `in_bulk(batch_size=999)` | ✅ Prevents huge IN clauses |
| Bulk write | `bulk_create(batch_size=N)` | ✅ Batched INSERTs |
| Lazy evaluation | QuerySets don't execute until terminal method | ✅ Reduces unnecessary queries |
| Dirty tracking | `_original_values` snapshot | ✅ Minimal UPDATE statements |

### 1.2 Identified Bottlenecks

1. **No connection pooling** — Each `AquiliaDatabase` uses a single connection.
   Under concurrent load, queries serialize on the connection lock.

2. **Eager `all()` materialization** — `all()` loads all rows into memory.
   For tables with millions of rows, this causes OOM.

3. **N+1 without explicit prefetch** — Related object access without
   `select_related()` or `prefetch_related()` causes N+1 queries.

4. **No query plan caching** — Each `_build_select()` call rebuilds the
   SQL string from scratch. For hot paths, this adds CPU overhead.

5. **No read replica routing** — All queries go to the primary database.
   Read-heavy workloads can't be distributed.

---

## 2. Scalability Recommendations

### 2.1 Connection Pooling (Priority: Critical)

**Current**: Single connection with `asyncio.Lock`  
**Recommended**: Pool-based connection management

```python
# Future design
class AquiliaDatabase:
    async def connect(self, pool_size=10, max_overflow=20):
        self._pool = await self._adapter.create_pool(
            self._url,
            min_size=pool_size,
            max_size=pool_size + max_overflow,
        )
```

Benefits:
- Concurrent query execution (critical for async frameworks)
- Connection reuse reduces setup overhead
- Overflow handling for burst traffic

### 2.2 Query Plan Caching

Cache compiled SQL for parameterized queries:

```python
class Q:
    _sql_cache: ClassVar[dict] = {}
    
    def _build_select(self, count=False):
        cache_key = self._cache_key(count)
        if cache_key in self._sql_cache:
            sql_template = self._sql_cache[cache_key]
            return sql_template, self._params.copy()
        sql, params = self._build_select_impl(count)
        self._sql_cache[cache_key] = sql
        return sql, params
```

### 2.3 Read Replica Routing

```python
class User(Model):
    class Meta:
        read_db = "replica"    # Route reads to replica
        write_db = "primary"   # Route writes to primary
```

### 2.4 Cursor-Based Pagination

Replace OFFSET-based pagination for deep pages:

```python
# Instead of:
await User.objects.order("id").offset(1000000).limit(10).all()

# Use cursor-based:
await User.objects.filter(id__gt=last_id).order("id").limit(10).all()
```

### 2.5 Select For Update Optimization

Add `OF` clause support for PostgreSQL:

```python
# Lock only the specific table in a JOIN
await Order.objects.select_related("user").select_for_update(of=["order"]).all()
```

---

## 3. Memory Optimization

### 3.1 Current Memory Profile

| Operation | Memory Usage | Notes |
|-----------|-------------|-------|
| `all()` 10K rows | ~10MB | All rows in list |
| `iterator(500)` 10K rows | ~0.5MB | Chunks of 500 |
| `values("id")` 10K rows | ~1MB | Dict per row |
| `values_list("id", flat=True)` 10K rows | ~0.3MB | Flat list |

### 3.2 Recommendations

1. **Streaming results** — Add server-side cursor support for PostgreSQL
2. **`__slots__` on Model** — Reduce per-instance memory overhead
3. **Deferred field loading** — Load only PKs initially, fetch fields on access
4. **Result set limits** — Add configurable `MAX_QUERY_RESULTS` safety net

---

## 4. Index Optimization

### 4.1 Automatic Index Suggestions

Future enhancement: Analyze query patterns and suggest missing indexes:

```python
# Admin panel query inspector could suggest:
# "Query on User filtered by email executed 1000 times, avg 50ms"
# "Suggestion: CREATE INDEX idx_users_email ON users(email)"
```

### 4.2 Composite Index Support

Already supported via `Meta.indexes`:

```python
class User(Model):
    class Meta:
        indexes = [
            Index(fields=["email", "active"]),  # Composite
            Index(fields=["created_at"], name="idx_created"),
        ]
```

---

## 5. Concurrency Safety

### 5.1 Current Transaction Model

- `atomic()` provides transaction/savepoint nesting
- `select_for_update()` provides row-level locking
- `F()` expressions enable race-safe updates

### 5.2 Recommendations

1. **Optimistic locking** — Add `version` field support:
   ```python
   class Article(Model):
       version = IntegerField(default=0)
       
       class Meta:
           optimistic_locking = True
   ```

2. **Advisory locks** — PostgreSQL advisory lock wrapper:
   ```python
   async with db.advisory_lock("process_orders"):
       await process_pending_orders()
   ```

---

*End of Scalability Design*
