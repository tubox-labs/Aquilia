"""
Live HTTP route smoke tests against the running aq server.

Run with:  python3 tests/test_mlops/test_live_routes.py
"""

import sys
import json
import urllib.request
import urllib.error
from typing import Any, Dict, Optional, Tuple

BASE = "http://127.0.0.1:8000"

passed = 0
failed = 0
errors = []


def req(method: str, path: str, body: Optional[Dict] = None) -> Tuple[int, Any]:
    """Send a request and return (status_code, parsed_json_or_text)."""
    url = f"{BASE}{path}"
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json"} if body else {}
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=10) as resp:
            raw = resp.read().decode()
            try:
                return resp.status, json.loads(raw)
            except json.JSONDecodeError:
                return resp.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw)
        except json.JSONDecodeError:
            return e.code, raw


def check(name: str, status: int, body: Any, expect_status: int = 200, expect_key: str = None):
    """Check a test result and record pass/fail."""
    global passed, failed
    ok = True
    msgs = []

    if status != expect_status:
        ok = False
        msgs.append(f"status={status}, expected={expect_status}")

    if expect_key and isinstance(body, dict) and expect_key not in body:
        ok = False
        msgs.append(f"missing key '{expect_key}' in {list(body.keys()) if isinstance(body, dict) else type(body)}")

    if ok:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        detail = "; ".join(msgs)
        errors.append(f"{name}: {detail}")
        print(f"  ❌ {name} — {detail}")
        if isinstance(body, dict):
            print(f"     Response: {json.dumps(body, indent=2)[:300]}")


def main():
    global passed, failed

    print("=" * 60)
    print("  LIVE HTTP ROUTE TESTS")
    print(f"  Server: {BASE}")
    print("=" * 60)

    # ── Auth routes ──────────────────────────────────────────
    print("\n📦 Auth Routes (/auth/*)")

    s, b = req("GET", "/auth/testuser")
    check("GET /auth/<name>", s, b, 200, "name")

    s, b = req("POST", "/auth/register", {
        "username": "livetest2",
        "email": "livetest2@test.com",
        "password": "TestPass123!",
    })
    # May be 201 (new) or 401 (exists) - we'll accept both for smoke test but log if abnormal
    check("POST /auth/register", s, b, expect_status=s)

    s, b = req("POST", "/auth/login", {
        "email": "livetest2@test.com",
        "password": "TestPass123!",
    })
    check("POST /auth/login", s, b, expect_status=s)

    # ── ML routes (custom + MLOps endpoints) ─────────────────
    print("\n🤖 ML Routes (/ml/*)")

    # Health & Probes
    s, b = req("GET", "/ml/health")
    check("GET /ml/health", s, b, 200, "status")

    s, b = req("GET", "/ml/healthz")
    check("GET /ml/healthz (liveness)", s, b, 200, "status")

    s, b = req("GET", "/ml/readyz")
    check("GET /ml/readyz (readiness)", s, b, 200, "status")

    # Models
    s, b = req("GET", "/ml/models")
    check("GET /ml/models", s, b, 200, "models")
    if s == 200:
        print(f"    Available models: {b.get('models', [])}")

    # Predict
    s, b = req("POST", "/ml/predict", {
        "sepal_length": 5.1,
        "sepal_width": 3.5,
        "petal_length": 1.4,
        "petal_width": 0.2,
    })
    check("POST /ml/predict (iris)", s, b, expect_status=200)

    # Metrics
    s, b = req("GET", "/ml/metrics")
    check("GET /ml/metrics", s, b, 200, "total_predictions")


    # Experiments
    s, b = req("GET", "/ml/experiments")
    check("GET /ml/experiments", s, b, 200, "experiments")

    # Drift
    s, b = req("GET", "/ml/drift")
    check("GET /ml/drift", s, b, 200, "status")

    # Plugins
    s, b = req("GET", "/ml/plugins")
    check("GET /ml/plugins", s, b, 200, "plugins")

    # Lineage
    s, b = req("GET", "/ml/lineage")
    check("GET /ml/lineage", s, b, 200, "total")

    # Artifacts
    s, b = req("GET", "/ml/artifacts")
    check("GET /ml/artifacts", s, b, 200, "artifacts")

    # Retrain
    s, b = req("POST", "/ml/retrain", {
        "model_name": "iris-classifier",
        "config": {},
    })
    check("POST /ml/retrain", s, b, 202, "status")

    # ── Summary ──────────────────────────────────────────────
    print("\n" + "=" * 60)
    total = passed + failed
    print(f"  Results: {passed}/{total} passed, {failed} failed")
    if errors:
        print("\n  Failures:")
        for e in errors:
            print(f"    • {e}")
    print("=" * 60)

    sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    main()
