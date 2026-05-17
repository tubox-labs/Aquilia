# Authentication And Authorization Configuration

## Configuration Entry Points

The implementation exposes the following configuration-like classes, policies, integrations, or dataclasses.

| Type | Source | Fields | Purpose |
| --- | --- | --- | --- |
| `AuditEvent` | `aquilia/auth/audit.py` | event_type: AuditEventType, severity: AuditSeverity, timestamp: float, identity_id: str &#124; None, ip_address: str &#124; None, user_agent: str &#124; None, resource: str &#124; None, action: str &#124; None, outcome: str, details: dict[str, Any], request_id: str &#124; None, session_id: str &#124; None, ... | Structured security audit event. |
| `AuthzContext` | `aquilia/auth/authz.py` | identity: Identity, resource: str, action: str, scopes: list[str], roles: list[str], attributes: dict[str, Any], tenant_id: str &#124; None, session_id: str &#124; None, metadata: dict[str, Any] | Authorization context for policy evaluation. |
| `AuthzResult` | `aquilia/auth/authz.py` | decision: Decision, reason: str &#124; None, policy_id: str &#124; None, metadata: dict[str, Any] | Authorization result. |
| `Clearance` | `aquilia/auth/clearance.py` | level: AccessLevel, entitlements: tuple[str, ...], conditions: tuple[Callable, ...], compartment: str &#124; None, deny_message: str, audit: bool | Immutable clearance requirement descriptor. |
| `ClearanceVerdict` | `aquilia/auth/clearance.py` | granted: bool, level_ok: bool, entitlements_ok: bool, conditions_ok: bool, compartment_ok: bool, missing_entitlements: tuple[str, ...], failed_conditions: tuple[str, ...], message: str, evaluated_at: float, identity_id: str &#124; None | Result of a clearance evaluation. |
| `Identity` | `aquilia/auth/core.py` | id: str, type: IdentityType, attributes: dict[str, Any], status: IdentityStatus, tenant_id: str &#124; None, created_at: datetime, updated_at: datetime | Authenticated principal (user or service). |
| `Credential` | `aquilia/auth/core.py` | identity_id: str, status: CredentialStatus, created_at: datetime, last_used_at: datetime &#124; None | Base protocol for credentials. |
| `PasswordCredential` | `aquilia/auth/core.py` | identity_id: str, password_hash: str, algorithm: str, created_at: datetime, last_changed_at: datetime, last_used_at: datetime &#124; None, must_change: bool, status: CredentialStatus | Password-based credential. |
| `ApiKeyCredential` | `aquilia/auth/core.py` | identity_id: str, key_id: str, key_hash: str, prefix: str, scopes: list[str], rate_limit: int &#124; None, expires_at: datetime &#124; None, created_at: datetime, last_used_at: datetime &#124; None, status: CredentialStatus, metadata: dict[str, Any] | API key credential (long-lived). |
| `OAuthClient` | `aquilia/auth/core.py` | client_id: str, client_secret_hash: str &#124; None, name: str, grant_types: list[Literal['authorization_code', 'client_credentials', 'refresh_token', 'device_code']], redirect_uris: list[str], scopes: list[str], require_pkce: bool, require_consent: bool, token_endpoint_auth_method: Literal['client_secret_basic', 'client_secret_post', 'none'], access_token_ttl: int, refresh_token_ttl: int, created_at: datetime, ... | OAuth2/OIDC client. |
| `MFACredential` | `aquilia/auth/core.py` | identity_id: str, mfa_type: Literal['totp', 'webauthn', 'sms', 'email'], mfa_secret: str &#124; None, backup_codes: list[str], webauthn_credentials: list[dict[str, Any]], phone_number: str &#124; None, email: str &#124; None, created_at: datetime, verified_at: datetime &#124; None, last_used_at: datetime &#124; None, status: CredentialStatus | Multi-factor authentication credential. |
| `TokenClaims` | `aquilia/auth/core.py` | iss: str, sub: str, aud: list[str], exp: int, iat: int, nbf: int, jti: str, scopes: list[str], sid: str &#124; None, roles: list[str], tenant_id: str &#124; None | Access token claims (JWT payload). |
| `AuthResult` | `aquilia/auth/core.py` | identity: Identity, access_token: str &#124; None, refresh_token: str &#124; None, session_id: str &#124; None, expires_in: int &#124; None, token_type: str, scopes: list[str], metadata: dict[str, Any] | Result of authentication operation. |
| `CrousArtifact` | `aquilia/auth/crous.py` | artifact_type: str, artifact_id: str, version: int, created_at: datetime, created_by: str, signature: str &#124; None, metadata: dict[str, Any] &#124; None | Base crous artifact. |
| `KeyArtifact` | `aquilia/auth/crous.py` | key_descriptor: KeyDescriptor | Cryptographic key artifact. |
| `PolicyArtifact` | `aquilia/auth/crous.py` | policy_id: str, policy_data: dict[str, Any] | Authorization policy artifact. |
| `AuditEventArtifact` | `aquilia/auth/crous.py` | event_type: str, identity_id: str &#124; None, resource: str &#124; None, action: str &#124; None, result: str, details: dict[str, Any] | Audit event artifact. |
| `RequestFingerprint` | `aquilia/auth/hardening.py` | ip_hash: str, ua_hash: str, accept_hash: str | Fingerprint a request for session binding. |
| `SecurityHeaders` | `aquilia/auth/hardening.py` | content_security_policy: str, strict_transport_security: str, x_content_type_options: str, x_frame_options: str, referrer_policy: str, permissions_policy: str, cross_origin_opener_policy: str, cross_origin_embedder_policy: str, cross_origin_resource_policy: str, cache_control: str, pragma: str | Configurable security headers for HTTP responses. |
| `HasherConfig` | `aquilia/auth/hashing.py` | algorithm: str, time_cost: int, memory_cost: int, parallelism: int, hash_len: int, salt_len: int, scrypt_n: int, scrypt_r: int, scrypt_p: int, scrypt_dklen: int, bcrypt_rounds: int, pbkdf2_iterations: int, ... | Algorithm-agnostic configuration for :class:`PasswordHasher`. |
| `PasswordPolicy` | `aquilia/auth/hashing.py` | See class attributes and constructor methods. | Password policy validator. |
| `AuthConfig` | `aquilia/auth/integration/di_providers.py` | See class attributes and constructor methods. | Authentication configuration builder. |
| `AuthRuntimeContext` | `aquilia/auth/integration/runtime_context.py` | request: Any, session: Any &#124; None, identity: Any &#124; None, auth: Any &#124; None, response: Any &#124; None, container: Any &#124; None | Request-scoped auth runtime state. |
| `SignInProvisionPolicy` | `aquilia/auth/manager.py` | enable_identity_seed: bool, create_identity_if_missing: bool, backfill_password_credential: bool, overwrite_password_credential: bool, allow_username_bootstrap: bool | Provisioning policy for sign_in bootstrap behavior. |
| `PolicyResult` | `aquilia/auth/policy/__init__.py` | decision: PolicyDecision, reason: str &#124; None, metadata: dict[str, Any] | Result of evaluating a policy rule. |
| `Policy` | `aquilia/auth/policy/__init__.py` | resource: str | Base class for resource-based authorization policies. |
| `KeyDescriptor` | `aquilia/auth/tokens.py` | kid: str, algorithm: str, public_key_pem: str, private_key_pem: str &#124; None, status: str, created_at: datetime, retire_after: datetime &#124; None, revoked_at: datetime &#124; None | Cryptographic key metadata. |
| `TokenConfig` | `aquilia/auth/tokens.py` | issuer: str, audience: list[str], access_token_ttl: int, refresh_token_ttl: int, algorithm: str | Token manager configuration. |

## Common Entry Points

- `AuthConfig`
- `AuthIntegration`
- `TokenConfig`
- `SignInProvisionPolicy`
- `PasswordHasher`

## Precedence Model

Aquilia generally resolves configuration in this order:

1. Explicit constructor arguments or typed integration dataclass values.
2. `Workspace` builder methods and `Workspace.integrate(...)` output.
3. `ConfigLoader` defaults and environment overlays.
4. Runtime defaults inside the subsystem service or provider constructor.

When this module is registered through an `AppManifest`, keep component declarations inside `modules/<name>/manifest.py` and keep cross-cutting integration settings in `workspace.py`.

## Datatype Guidance

- Prefer typed dataclasses, policy objects, and config objects listed above when they exist.
- Keep secret values in environment-backed config, not literal strings in committed workspace files.
- Keep runtime-only state in services, stores, providers, or request state rather than static configuration.
- Use `to_dict()` on integration dataclasses when you need to inspect exactly what enters `ConfigLoader`.
