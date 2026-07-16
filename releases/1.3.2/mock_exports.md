# Mock Server & Collection Exports

Specula features a schema-driven Mock Server and dynamic collection exporters to support rapid frontend integration and testing.

---

## Interactive Mock Server (`/specula/mock`)

The mock server lets developers call any documented API endpoint and receive a plausible response payload without executing any business logic.

### Enabling the Mock Server
The mock server is disabled by default. Enable it in your workspace configuration:

```python
workspace.integrate(Integration.specula(
    title="Customer API",
    mock_server_enabled=True,
    mock_max_depth=4 # limit recursive definitions mapping
))
```

### How Payload Synthesis Works
When a request is sent to `/specula/mock/<path>`, the mock router matches the path against the compiled API specification. It resolves the success response (`200`, `201`, or `202`) and inspects the JSON Schema:

1. **Explicit Examples**: If the schema or individual fields define an `example` or `examples` block, those values are returned directly.
2. **Plausible Synthesis**: If no examples are configured, Specula inspects the schema field types and synthesizes logical placeholders:
   * **Formatting Matchers**: String formats like `email`, `uuid`, `uri`, and `date-time` map to real formatted values (e.g. `user@example.com`, `550e8400-e29b-41d4-a716-446655440000`).
   * **Key Name Inference**: If a string field matches common keys (such as `email` or `url`), appropriate values are auto-injected.
   * **Standard Defaults**: Integers default to `42`, numbers to `3.14`, booleans to `True`, and arrays to single-item arrays.
3. **Recursion Safety**: Self-referencing models (e.g., a node containing a list of children of its own type) are automatically truncated when nesting depth exceeds `mock_max_depth` (default `4`).

---

## Exporters

Specula exposes dynamic endpoints to download client collections configured with your current workspace routing topology and security schemes.

### 1. Postman Collection v2.1
* **Endpoint**: `/specula/export/postman`
* **Output**: A compliant Postman v2.1 collection JSON file.
* **Details**:
  * Groups endpoints into folders based on their tags or manifest module names.
  * Translates route variables like `/users/<id:int>` into Postman-compatible environment syntax: `/users/{{id}}`.
  * Pre-populates request bodies with JSON examples synthesized from Contract definitions.
  * Embeds default authorization headers mapped to the `{{access_token}}` environment variable.

### 2. Insomnia v4 Collection
* **Endpoint**: `/specula/export/insomnia`
* **Output**: A standard Insomnia v4 export file.
* **Details**:
  * Includes workspace configuration mapping the current API.
  * Sets up base environment variables referencing `{{ _.base_url }}`.
  * Configures HTTP methods, headers, and body payloads automatically.
