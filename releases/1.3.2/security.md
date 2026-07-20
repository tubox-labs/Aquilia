# Automated Security & Clearance Detection

Specula integrates with Aquilia's security pipeline to automatically detect, map, and document authentication configurations. It translates pipeline guards and clearance levels into standard OpenAPI security requirements and rich custom metadata tags.

---

## Inferred Security Schemes

The spec builder scans your controllers' and routes' pipeline nodes and handler decorators to identify authentication mechanisms. It automatically registers and configures security definitions in the OpenAPI `components.securitySchemes` catalog:

| Inferred Guard Class Name | Generated Security Scheme | Schema Details |
| :--- | :--- | :--- |
| `AuthGuard` / `Auth` / `@authenticated` | `bearerAuth` | HTTP Bearer token (JWT) authentication. |
| `ApiKeyGuard` / `ApiKey` | `apiKeyAuth` | `X-API-Key` request header authorization. |
| `SessionGuard` / `Session` | `cookieAuth` | Session-based cookie verification (`session`). |
| `BasicAuthGuard` / `Basic` | `basicAuth` | HTTP Basic authentication. |
| `OAuth2Guard` / `OAuth2` | `oauth2` | OAuth2 Authorization Code flow. |

```python
# Specula automatically registers bearerAuth with ["read", "write"] scopes
class OrderController(Controller):
    pipeline = [AuthGuard(), ScopeGuard("read", "write")]
    
    @GET("/")
    async def list_orders(self, ctx: RequestCtx): ...
```

---

## Integrated Clearance Detection

Specula integrates directly with the `aquilia.auth.clearance` system to identify role-based and attribute-based clearance levels. 

The builder resolves the merged clearance level from the controller boundary and individual route overrides:
1. **Public Routes**: If the effective clearance resolves to `AccessLevel.PUBLIC` (e.g. via `@grant(level=AccessLevel.PUBLIC)`), security requirements are omitted for that route.
2. **Protected Routes**: If the effective clearance is higher than public, `bearerAuth` is automatically registered as a requirement.

---

## Rich Metadata Extensions (`x-specula-security`)

To support advanced observability and client generation, Specula embeds the full resolved authorization metadata in a custom vendor extension block (`x-specula-security`) inside each route's spec operation:

```json
"x-specula-security": {
  "authenticated": true,
  "guards": [
    {
      "name": "RoleGuard",
      "type": "instance",
      "roles": ["admin", "compliance"],
      "require_all": false
    }
  ],
  "clearance": {
    "level": "INTERNAL",
    "level_value": 30,
    "entitlements": ["view_audit_logs", "override_fees"],
    "conditions": ["IsDuringOfficeHours", "IPRangeCondition"],
    "compartment": "finance"
  }
}
```

This vendor block exposes:
* **`authenticated`**: Boolean flag indicating if verification is required.
* **`guards`**: Detailed list of active pipeline guard configurations, including roles, scopes, optional tags, resources, and evaluation settings.
* **`clearance`**: The full clearance metadata, including `level` name, `level_value` integer, required `entitlements` lists, active `conditions` names, and matching resource `compartment` boundaries.
