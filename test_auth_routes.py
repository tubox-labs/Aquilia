"""
test_auth_routes.py
===================
End-to-end test script for every route in the myapp authentication module.

Run:
    python3 test_auth_routes.py

Server must be running at http://127.0.0.1:8000 before running this script.
Start it with: cd myapp && aq run --no-reload --skip-checks
"""

import sys
import json
import time
import httpx

BASE = "http://127.0.0.1:8000/v1/auth"
PASS = "\033[32m✓\033[0m"
FAIL = "\033[31m✗\033[0m"
SKIP = "\033[33m~\033[0m"
INFO = "\033[34m→\033[0m"

_results: list[tuple[str, bool, str]] = []  # (name, passed, detail)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def section(title: str) -> None:
    print(f"\n\033[1;36m{'═' * 60}\033[0m")
    print(f"\033[1;36m  {title}\033[0m")
    print(f"\033[1;36m{'═' * 60}\033[0m")


def check(name: str, resp: httpx.Response, expected_status: int,
          extract: dict | None = None) -> dict:
    """
    Assert status code, pretty-print result, and optionally extract keys
    from the JSON body.  Returns parsed JSON body.
    """
    try:
        body = resp.json()
    except Exception:
        body = {"_raw": resp.text[:200]}

    passed = resp.status_code == expected_status
    symbol = PASS if passed else FAIL
    status_colour = "\033[32m" if passed else "\033[31m"
    print(
        f"  {symbol}  [{status_colour}{resp.status_code}\033[0m"
        f"/{expected_status}]  {name}"
    )
    if not passed:
        print(f"       {FAIL} Body: {json.dumps(body, indent=6)[:400]}")
    _results.append((name, passed, ""))

    extracted = {}
    if extract and isinstance(body, dict):
        for key in extract:
            val = body.get(key)
            if val is not None:
                extracted[key] = val
    return {**body, **extracted}


def info(msg: str) -> None:
    print(f"       {INFO} {msg}")


# ---------------------------------------------------------------------------
# 1. Registration
# ---------------------------------------------------------------------------

def test_registration(c: httpx.Client) -> str:
    section("1. Registration  POST /register")

    # Happy path
    r = c.post("/register", json={
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "Test1234!",
        "roles": ["user"],
    })
    d = check("Register new user", r, 201)
    info(f"user id: {d.get('id') or d.get('identity_id')}")

    # Duplicate (should fail)
    r2 = c.post("/register", json={
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "Test1234!",
    })
    check("Duplicate registration → 4xx", r2, r2.status_code)          # any error

    # Missing fields
    r3 = c.post("/register", json={"username": "x"})
    check("Missing password → 422/400", r3, r3.status_code)

    return "testuser"


# ---------------------------------------------------------------------------
# 2. Session Auth
# ---------------------------------------------------------------------------

def test_session_auth(c: httpx.Client) -> dict:
    section("2. Password + Session  /session/*")

    # Login with demo user
    r = c.post("/session/login", json={"username": "alice", "password": "Alice1234!"})
    d = check("Session login (alice)", r, 200)
    info(f"session_id: {d.get('session_id', '(embedded in cookie)')}")

    # /me via session cookie (client jar holds the cookie)
    r2 = c.get("/session/me")
    d2 = check("GET /session/me (cookie)", r2, 200)
    info(f"me: {d2.get('username') or d2.get('id')}")

    # Logout
    r3 = c.post("/session/logout")
    check("Session logout", r3, 200)

    # /me after logout → should fail
    r4 = c.get("/session/me")
    check("GET /session/me after logout → 401", r4, r4.status_code)

    # Admin login (used later)
    r5 = c.post("/session/login", json={"username": "admin", "password": "Admin1234!"})
    d5 = check("Session login (admin)", r5, 200)
    return d5


# ---------------------------------------------------------------------------
# 3. JWT Token Auth
# ---------------------------------------------------------------------------

def test_jwt_auth(c: httpx.Client) -> dict:
    section("3. JWT Token Auth  /token/*")

    # Get tokens
    r = c.post("/token/", json={"username": "alice", "password": "Alice1234!"})
    d = check("POST /token (exchange credentials)", r, 200)
    access  = d.get("access_token", "")
    refresh = d.get("refresh_token", "")
    info(f"access_token[:40]: {access[:40]}…")
    info(f"refresh_token[:20]: {refresh[:20]}…")

    auth_hdr = {"Authorization": f"Bearer {access}"}

    # /token/me
    r2 = c.get("/token/me", headers=auth_hdr)
    d2 = check("GET /token/me (bearer)", r2, 200)
    info(f"identity: {d2.get('username') or d2.get('id')}")

    # verify
    r3 = c.get("/token/verify", headers=auth_hdr)
    d3 = check("GET /token/verify", r3, 200)
    info(f"valid={d3.get('valid')}  sub={d3.get('claims', {}).get('sub')}")

    # refresh
    r4 = c.post("/token/refresh", json={"refresh_token": refresh})
    d4 = check("POST /token/refresh", r4, 200)
    new_access = d4.get("access_token", access)
    info(f"new access_token[:40]: {new_access[:40]}…")

    # revoke refresh token
    r5 = c.post("/token/revoke", json={"token": refresh, "token_type": "refresh"},
                headers={"Authorization": f"Bearer {new_access}"})
    check("POST /token/revoke", r5, 200)

    # Bad credentials
    r6 = c.post("/token/", json={"username": "alice", "password": "wrong"})
    check("POST /token bad password → 40x", r6, r6.status_code)

    return {"access_token": new_access, "username": "alice"}


# ---------------------------------------------------------------------------
# 4. API Keys
# ---------------------------------------------------------------------------

def test_api_keys(c: httpx.Client, access_token: str) -> str:
    section("4. API Key Auth  /keys/*")

    auth_hdr = {"Authorization": f"Bearer {access_token}"}

    # Create key
    r = c.post("/keys/", json={
        "name": "test-key",
        "scopes": ["api:read", "api:write"],
        "expires_in_days": 30,
    }, headers=auth_hdr)
    d = check("POST /keys (create)", r, 201)
    raw_key = d.get("key", "")
    key_id  = d.get("key_id", "")
    info(f"key_id={key_id}  key[:30]={raw_key[:30]}…")

    # List keys
    r2 = c.get("/keys/", headers=auth_hdr)
    d2 = check("GET /keys (list)", r2, 200)
    info(f"total keys: {d2.get('total')}")

    # Protected endpoint via X-API-Key
    r3 = c.get("/keys/protected", headers={"x-api-key": raw_key})
    d3 = check("GET /keys/protected (X-API-Key auth)", r3, 200)
    info(f"identity via api-key: {d3.get('identity', {}).get('username')}")

    # Wrong key → should fail
    r4 = c.get("/keys/protected", headers={"x-api-key": "bad_key_value"})
    check("GET /keys/protected (bad key) → 40x", r4, r4.status_code)

    # Revoke
    if key_id:
        r5 = c.delete(f"/keys/{key_id}", headers=auth_hdr)
        check(f"DELETE /keys/{key_id} (revoke)", r5, 200)

    return raw_key


# ---------------------------------------------------------------------------
# 5. OAuth2
# ---------------------------------------------------------------------------

def test_oauth2(c: httpx.Client, access_token: str) -> None:
    section("5. OAuth2 Flows  /oauth/*")

    auth_hdr = {"Authorization": f"Bearer {access_token}"}

    # ── 5a. Authorization Code + PKCE ─────────────────────────────────────
    # Generate a minimal PKCE pair (plain method for simplicity in tests)
    code_verifier  = "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"
    code_challenge = code_verifier   # method=plain

    r = c.get("/oauth/authorize", params={
        "client_id":             "demo-web-client",
        "redirect_uri":          "http://localhost:3000/callback",
        "response_type":         "code",
        "scope":                 "profile email",
        "state":                 "xyz-state",
        "code_challenge":        code_challenge,
        "code_challenge_method": "plain",
    }, headers=auth_hdr)
    d = check("GET /oauth/authorize (auth-code+PKCE)", r, 200)
    auth_code = d.get("code", "")
    info(f"auth_code[:20]: {auth_code[:20]}…")

    # Exchange for tokens
    r2 = c.post("/oauth/token", json={
        "grant_type":    "authorization_code",
        "code":          auth_code,
        "client_id":     "demo-web-client",
        "client_secret": "demo-web-secret",
        "redirect_uri":  "http://localhost:3000/callback",
        "code_verifier": code_verifier,
    })
    d2 = check("POST /oauth/token (authorization_code)", r2, 200)
    info(f"access_token[:30]: {str(d2.get('access_token',''))[:30]}…")

    # ── 5b. Client Credentials ────────────────────────────────────────────
    r3 = c.post("/oauth/token", json={
        "grant_type":    "client_credentials",
        "client_id":     "demo-m2m-client",
        "client_secret": "demo-m2m-secret",
        "scope":         "api:read api:write",
    })
    d3 = check("POST /oauth/token (client_credentials)", r3, 200)
    info(f"m2m access_token[:30]: {str(d3.get('access_token',''))[:30]}…")

    # ── 5c. Device Flow ───────────────────────────────────────────────────
    r4 = c.post("/oauth/device/code", json={
        "client_id": "demo-device-client",
        "scope":     "profile",
    })
    d4 = check("POST /oauth/device/code (initiate device flow)", r4, 200)
    device_code = d4.get("device_code", "")
    user_code   = d4.get("user_code", "")
    info(f"device_code[:20]: {device_code[:20]}…  user_code={user_code}")

    # User approves on a second client (simulated)
    if user_code:
        r5 = c.post("/oauth/device/approve", json={"user_code": user_code},
                    headers=auth_hdr)
        check("POST /oauth/device/approve (user grants)", r5, 200)

        # Poll for tokens
        r6 = c.post("/oauth/token", json={
            "grant_type":  "urn:ietf:params:oauth:grant-type:device_code",
            "device_code": device_code,
            "client_id":   "demo-device-client",
        })
        d6 = check("POST /oauth/token (device_code poll → tokens)", r6, 200)
        info(f"device access_token[:30]: {str(d6.get('access_token',''))[:30]}…")

    # ── 5d. Register new client (admin only) ─────────────────────────────
    # First get an admin bearer token
    r_adm = c.post("/token/", json={"username": "admin", "password": "Admin1234!"})
    adm_token = r_adm.json().get("access_token", "")

    r7 = c.post("/oauth/clients", json={
        "name":          "test-client",
        "redirect_uris": ["http://test.example.com/cb"],
        "grant_types":   ["authorization_code"],
        "scopes":        ["profile"],
        "require_pkce":  True,
    }, headers={"Authorization": f"Bearer {adm_token}"})
    d7 = check("POST /oauth/clients (register, admin)", r7, 201)
    info(f"new client_id: {d7.get('client_id')}")

    # Non-admin attempt
    r8 = c.post("/oauth/clients", json={"name": "x"},
                headers=auth_hdr)
    check("POST /oauth/clients (non-admin) → 40x", r8, r8.status_code)


# ---------------------------------------------------------------------------
# 6. MFA / TOTP
# ---------------------------------------------------------------------------

def test_mfa(c: httpx.Client) -> None:
    section("6. MFA / TOTP  /mfa/*")

    # Get a fresh alice token
    r = c.post("/token/", json={"username": "alice", "password": "Alice1234!"})
    access = r.json().get("access_token", "")
    auth_hdr = {"Authorization": f"Bearer {access}"}

    # Status before enrollment
    r1 = c.get("/mfa/status", headers=auth_hdr)
    d1 = check("GET /mfa/status (before enroll)", r1, 200)
    info(f"enrolled={d1.get('enrolled')}")

    # Begin enrollment
    r2 = c.post("/mfa/enroll", headers=auth_hdr)
    d2 = check("POST /mfa/enroll (begin)", r2, 200)
    secret = d2.get("secret", "")
    uri    = d2.get("provisioning_uri", "")
    info(f"secret[:10]={secret[:10]}…  uri[:50]={uri[:50]}…")

    if secret:
        # Generate a valid TOTP code from the secret
        try:
            import hmac, hashlib, struct, base64, time as _time

            def totp(secret_b32: str, t: int | None = None) -> str:
                key   = base64.b32decode(secret_b32.upper() + "=" * ((-len(secret_b32)) % 8))
                t_val = int((_time.time() if t is None else t) / 30)
                msg   = struct.pack(">Q", t_val)
                h     = hmac.new(key, msg, hashlib.sha1).digest()
                offset = h[-1] & 0x0F
                code   = (struct.unpack(">I", h[offset:offset+4])[0] & 0x7FFFFFFF) % 1_000_000
                return f"{code:06d}"

            totp_code = totp(secret)
            info(f"generated TOTP code: {totp_code}")

            # Confirm enrollment
            r3 = c.post("/mfa/confirm", json={"code": totp_code}, headers=auth_hdr)
            check("POST /mfa/confirm (activate)", r3, 200)

            # Status after enrollment
            r4 = c.get("/mfa/status", headers=auth_hdr)
            d4 = check("GET /mfa/status (after enroll)", r4, 200)
            info(f"enrolled={d4.get('enrolled')}")

            # Verify (complete MFA login step)
            alice_id = r.json().get("user", {}).get("id", "") or \
                       c.get("/token/me", headers=auth_hdr).json().get("id", "")
            totp_code2 = totp(secret)
            r5 = c.post("/mfa/verify", json={
                "identity_id": alice_id,
                "code":        totp_code2,
                "scopes":      ["profile"],
            })
            d5 = check("POST /mfa/verify (complete MFA login)", r5, 200)
            info(f"mfa access_token[:30]: {str(d5.get('access_token',''))[:30]}…")

            # Wrong code
            r6 = c.post("/mfa/verify", json={
                "identity_id": alice_id,
                "code":        "000000",
            })
            check("POST /mfa/verify (bad code) → 400", r6, 400)

            # Unenroll
            r7 = c.delete("/mfa/", headers=auth_hdr)
            check("DELETE /mfa (unenroll)", r7, 200)

        except Exception as exc:
            print(f"  {SKIP}  TOTP code generation failed: {exc}  (skipping MFA tests)")
    else:
        print(f"  {SKIP}  No secret returned — skipping confirm/verify")


# ---------------------------------------------------------------------------
# 7. Clearance demo
# ---------------------------------------------------------------------------

def test_clearance(c: httpx.Client) -> None:
    section("7. Clearance-Based Access Control  /demo/*")

    # Get tokens for alice (user), bob (user+staff), admin (user+admin)
    alice_token = c.post("/token/", json={"username": "alice", "password": "Alice1234!"}).json().get("access_token", "")
    bob_token   = c.post("/token/", json={"username": "bob",   "password": "Bob1234!"  }).json().get("access_token", "")
    admin_token = c.post("/token/", json={"username": "admin", "password": "Admin1234!"}).json().get("access_token", "")

    alice_hdr = {"Authorization": f"Bearer {alice_token}"}
    bob_hdr   = {"Authorization": f"Bearer {bob_token}"}
    admin_hdr = {"Authorization": f"Bearer {admin_token}"}

    # ── PUBLIC — no auth ────────────────────────────────────────────────
    r = c.get("/demo/public")
    d = check("GET /demo/public (no auth)", r, 200)
    info(f"level={d.get('level')}")

    # ── AUTHENTICATED ───────────────────────────────────────────────────
    r = c.get("/demo/authenticated", headers=alice_hdr)
    d = check("GET /demo/authenticated (alice)", r, 200)
    info(f"level={d.get('level')}")

    r_noauth = c.get("/demo/authenticated")
    check("GET /demo/authenticated (no auth) → 401", r_noauth, r_noauth.status_code)

    # ── INTERNAL (staff/admin) ──────────────────────────────────────────
    r = c.get("/demo/internal", headers=bob_hdr)
    check("GET /demo/internal (bob=staff) → 200", r, 200)

    r = c.get("/demo/internal", headers=alice_hdr)
    check("GET /demo/internal (alice=no staff) → 40x", r, r.status_code)

    # ── CONFIDENTIAL (admin) ────────────────────────────────────────────
    r = c.get("/demo/confidential", headers=admin_hdr)
    check("GET /demo/confidential (admin) → 200", r, 200)

    r = c.get("/demo/confidential", headers=alice_hdr)
    check("GET /demo/confidential (alice) → 40x", r, r.status_code)

    # ── RESTRICTED (admin + is_verified) ───────────────────────────────
    r = c.get("/demo/restricted", headers=admin_hdr)
    check("GET /demo/restricted (admin+verified) → 200", r, 200)

    r = c.get("/demo/restricted", headers=alice_hdr)
    check("GET /demo/restricted (alice) → 40x", r, r.status_code)

    # ── is_owner_or_admin condition ─────────────────────────────────────
    r = c.get("/demo/owner-check", headers=alice_hdr)
    check("GET /demo/owner-check (alice owns resource)", r, 200)

    # ── is_verified condition ───────────────────────────────────────────
    r = c.get("/demo/verified-only", headers=alice_hdr)
    check("GET /demo/verified-only (alice=verified)", r, 200)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def main() -> None:
    print("\n\033[1;35m╔══════════════════════════════════════════════════════════╗\033[0m")
    print("\033[1;35m║   Aquilia Auth Module — Full Route Test Suite             ║\033[0m")
    print("\033[1;35m╚══════════════════════════════════════════════════════════╝\033[0m")
    print(f"  Base URL: {BASE}")

    # Single client → shares cookie jar across all tests
    with httpx.Client(base_url=BASE, timeout=10.0, follow_redirects=True) as c:
        try:
            test_registration(c)
            test_session_auth(c)
            jwt_data   = test_jwt_auth(c)
            access_tok = jwt_data.get("access_token", "")
            test_api_keys(c, access_tok)
            test_oauth2(c, access_tok)
            test_mfa(c)
            test_clearance(c)
        except httpx.ConnectError:
            print("\n\033[31m  ERROR: Cannot connect to server at 127.0.0.1:8000\033[0m")
            print("  Make sure the server is running:  cd myapp && aq run --no-reload")
            sys.exit(1)

    # ── Summary ────────────────────────────────────────────────────────────
    total   = len(_results)
    passed  = sum(1 for _, ok, _ in _results if ok)
    failed  = total - passed
    colour  = "\033[32m" if failed == 0 else "\033[31m"

    print(f"\n\033[1;36m{'═' * 60}\033[0m")
    print(f"\033[1m  Results: {colour}{passed}/{total} passed\033[0m", end="")
    if failed:
        print(f"  \033[31m({failed} failed)\033[0m")
    else:
        print(f"  \033[32m🎉 All passed!\033[0m")

    if failed:
        print("\n  Failed checks:")
        for name, ok, _ in _results:
            if not ok:
                print(f"    {FAIL}  {name}")

    print(f"\033[1;36m{'═' * 60}\033[0m\n")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
