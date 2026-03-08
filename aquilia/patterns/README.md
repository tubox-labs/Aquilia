# AquilaPatterns

**A unique, expressive, static-first URL pattern language and compiler for Aquilia**

AquilaPatterns is a professional, production-grade URL routing system that provides:

- 🎯 **Static-first & toolable**: Patterns are data assets — parseable, analyzable, and deterministic
- 🛡️ **Safe by default**: Compile-time errors for ambiguous/conflicting patterns
- 📖 **Human-readable**: Clear token visuals with guillemets `«»`
- 🧩 **Composable**: Optional groups and multi-captures compose deterministically
- ⚡ **Performant**: Radix-first matching with compiled castors
- 🔌 **Extensible**: Custom types, transforms, and validators via registries

---

## Quick Start

### Installation

```bash
pip install anyio  # Required for async support
```

### Basic Usage

```python
from aquilia.patterns import parse_pattern, PatternCompiler, PatternMatcher
import asyncio

# Parse a pattern
pattern_str = "/users/«id:int»"
ast = parse_pattern(pattern_str)

# Compile it
compiler = PatternCompiler()
compiled = compiler.compile(ast)

# Match requests
matcher = PatternMatcher()
matcher.add_pattern(compiled)

async def match_request():
    result = await matcher.match("/users/42")
    print(result.params)  # {'id': 42}

asyncio.run(match_request())
```

---

## Pattern Syntax

### Token Parameters

```python
«id:int»                          # Single segment, cast to int
«slug:slug|re=^[a-z0-9-]+$»      # Slug with regex constraint
«year:int|min=1900|max=2100»     # Integer with range
«tag:str|in=(python,rust,go)»    # Enum constraint
«data:json»                       # JSON object
«uuid:uuid»                       # UUID v4
```

### Multi-Segment Captures (Splat)

```python
*path                             # Captures remaining segments as list
*path:path                        # Captures as slash-joined string
```

### Optional Groups

```python
/posts[/«year:int»[/«month:int»]]  # /posts, /posts/2024, /posts/2024/12
/products[/«category:slug»]/«id:int»
```

### Query Parameters

```python
?q:str|min=1&limit:int=10&offset:int=0
```

### Transforms

```python
«username:str@lower»              # Apply lowercase transform
«title:str@strip»                 # Strip whitespace
```

### Complete Examples

```python
# Basic routes
"/users/«id:int»"
"/files/*path"
"/blog/«slug:slug»"

# With constraints
"/articles/«year:int|min=1900|max=2100»"
"/products/«cat:str|in=(electronics,books,toys)»"
"/archive/«date:str|re=\"^\\d{4}-\\d{2}-\\d{2}$\"»"

# Optional groups
"/api/«version:str»/items[/«id:int»]"

# Query parameters
"/search?query:str|min=1&limit:int=10"

# Complex
"/api/v«version:int»/users/«id:int»/posts[/«post_id:int»]?include:str=comments"
```

---

## Built-in Types

| Type | Description | Example |
|------|-------------|---------|
| `str` | String (default) | `«name:str»` |
| `int` | Integer | `«id:int»` |
| `float` | Floating point | `«price:float»` |
| `uuid` | UUID v4 | `«id:uuid»` |
| `slug` | URL-safe slug | `«slug:slug»` |
| `path` | Multi-segment path | `*path:path` |
| `bool` | Boolean | `«active:bool»` |
| `json` | JSON object/array | `«data:json»` |
| `any` | No casting | `«value:any»` |

---

## Constraints

| Constraint | Description | Example |
|------------|-------------|---------|
| `min=` | Minimum value/length | `«age:int|min=18»` |
| `max=` | Maximum value/length | `«age:int|max=120»` |
| `re=` | Regex pattern | `«code:str|re=\"^[A-Z]{3}$\"»` |
| `in=` | Enum values | `«status:str|in=(active,inactive)»` |
| `hdr:` | Header predicate | `«id:int|hdr:X-API-Key=secret»` |

---

## Specificity Scoring

Patterns are ranked automatically by specificity for deterministic matching:

- Static segment: **+200**
- Typed token with strong constraint (regex, enum, int, uuid): **+120**
- Typed token generic (str): **+50**
- Splat (`*`): **+0**
- Optional segment: **-20** per optional node
- Predicate present: **+10**
- Segment count tiebreaker: **+ (count × 2)**

### Example Rankings

```
 324  /users/«id:int»                              # Static + int
 324  /articles/«year:int|min=1900|max=2100»      # Static + int with constraints
 324  /products/«cat:str|in=(a,b,c)»              # Static + enum constraint
 254  /blog/«slug:slug»                            # Static + slug type
 204  /files/*path                                 # Static + splat
  50  /«slug:str»                                  # Generic string only
```

---

## OpenAPI Integration

Generate OpenAPI 3.0 specifications automatically:

```python
from aquilia.patterns.openapi import patterns_to_openapi_spec

patterns = [
    (compiled_pattern1, "GET", "get_user"),
    (compiled_pattern2, "POST", "create_user"),
]

spec = patterns_to_openapi_spec(
    patterns,
    title="My API",
    version="1.0.0",
    description="Generated from AquilaPatterns"
)

# Save to file
with open("openapi.json", "w") as f:
    json.dump(spec, f, indent=2)
```

---

## LSP Support

Generate metadata for IDE tooling:

```python
from aquilia.patterns.lsp import generate_lsp_metadata
from pathlib import Path

patterns = [...]  # List of compiled patterns

generate_lsp_metadata(patterns, Path("patterns.json"))
```

This enables:
- ✨ **Hover docs**: Show param types and constraints
- 🔍 **Autocomplete**: Suggest tokens, types, and constraints
- 🐛 **Inline diagnostics**: Show syntax/semantic errors
- 🔧 **Quick fixes**: Auto-correct pattern syntax errors

---

## Custom Types

Register custom types:

```python
from aquilia.patterns import register_type
import re

@register_type("email", lambda v: validate_email(v))
def email_type(value: str) -> str:
    if not re.match(r'^[^@]+@[^@]+\.[^@]+$', value):
        raise ValueError("Invalid email")
    return value.lower()

# Use in patterns
"/users/«email:email»"
```

---

## Custom Transforms

Register custom transforms:

```python
from aquilia.patterns import register_transform

@register_transform("slugify")
def slugify(value: str) -> str:
    return value.lower().replace(" ", "-")

# Use in patterns
"/posts/«title:str@slugify»"
```

---

## Error Diagnostics

AquilaPatterns provides rich error reporting with spans:

```python
PatternSyntaxError: Unterminated token starting at pos 8 
  --> my_app.py:12:9
  |
12|   pattern = "/users/«id:int"
  |                    ^^^^^^^^
  |
  = Expected '»' to close token

RouteAmbiguityError: Ambiguous routes detected
  Pattern 1: /items/«id:int» (specificity=324)
  Pattern 2: /items/«name:str» (specificity=274)
  
Suggestions:
  1) Add stricter constraint to Pattern 2
  2) Add static prefix to differentiate
  3) Use explicit type casting
```

---

## Performance

### Targets

- **Cold compile** (1k routes): < 1s
- **Cold compile** (10k routes): < 5s
- **Match latency**: < 50µs (static routes), < 200µs (parameter routes)
- **Memory**: ~1KB per route (serialized)

### Benchmarks

```bash
python benchmarks/bench_patterns.py
```

---

## Architecture

```
aquilia/patterns/
├── __init__.py              # Public API
├── grammar.py               # Formal EBNF grammar
├── compiler/
│   ├── parser.py            # Tokenizer + parser → AST
│   ├── ast_nodes.py         # AST node definitions
│   ├── compiler.py          # AST → compiled metadata
│   └── specificity.py       # Scoring algorithm
├── types/
│   └── registry.py          # Type castors
├── validators/
│   └── registry.py          # Constraint validators
├── transforms/
│   └── registry.py          # Transform functions
├── diagnostics/
│   └── errors.py            # Error types and formatting
├── lsp/
│   └── metadata.py          # LSP metadata generation
├── matcher.py               # Pattern matching engine
└── openapi.py               # OpenAPI generation
```

---

## Testing

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run unit tests
pytest tests/patterns/ -v

# Run property tests
pytest tests/patterns/test_property.py -v

# Run with coverage
pytest tests/patterns/ --cov=aquilia.patterns --cov-report=html
```

---

## Examples

### E-commerce API

```python
patterns = [
    "/products",
    "/products/«id:int»",
    "/products/«id:int»/reviews",
    "/products/search?q:str&category:slug&min_price:float=0&max_price:float",
    "/categories/«slug:slug»/products",
    "/cart/«user_id:uuid»/items",
    "/orders/«order_id:uuid»",
]
```

### Blog API

```python
patterns = [
    "/posts",
    "/posts/«slug:slug»",
    "/posts/«year:int»/«month:int»",
    "/authors/«username:str»",
    "/tags/«tag:slug»/posts",
    "/search?q:str|min=3",
]
```

### File Server

```python
patterns = [
    "/files/*path",
    "/download/«id:uuid»",
    "/upload",
    "/browse/«dir:path»",
]
```

---

## Pattern Syntax Reference

### Basic patterns

```python
# Static route
"/users"

# Integer parameter
"/users/«id:int»"

# String parameter
"/users/«name:str»"

# UUID parameter
"/users/«id:uuid»"

# Wildcard / catch-all
"/files/*path"
```

### With constraints

```python
# Min/max length
"/posts/«slug:slug|min=3|max=80»"

# Numeric range
"/years/«year:int|min=2000|max=2099»"
```

### Query parameters

```python
# Required query param
"/search?q:str"

# Optional with default
"/search?q:str|min=2&page:int=1"
```

---

## Contributing

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for development guidelines.

---

## License

MIT License - see [LICENSE](../../LICENSE)

---

## Roadmap

### v1.0.0
- [ ] Full router integration with radix trie
- [ ] Complete test suite (unit + property + fuzzing)
- [ ] Performance benchmarks
- [ ] LSP server implementation

### v0.3.0
- [ ] VS Code extension
- [ ] Query parameter validation
- [ ] Request body pattern matching
- [ ] WebSocket route patterns

### v1.0.0
- [ ] Stability guarantees
- [ ] Complete documentation
- [ ] Production case studies

---

## Acknowledgments

Designed and implemented following industry best practices:
- EBNF grammar specification
- Deterministic conflict detection
- OpenAPI 3.0 compliance
- LSP protocol support
- Property-based testing with Hypothesis

---

**Status**: Beta - Core features complete, production-ready for v0.1.0

For questions and support, see [GitHub Issues](https://github.com/embrake/Aquilify/issues)
