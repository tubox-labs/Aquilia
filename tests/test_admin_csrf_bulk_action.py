"""
Regression test for the admin bulk-action CSRF crash.

`bulk_action()` (aquilia/admin/controller.py) parses the request form with
`multi=True` so the repeated `selected` checkbox field survives as a list --
but that wraps every field, including the singular `_csrf_token`, in a
1-item list too. `AdminCSRFProtection.validate_request()` then called
`.encode()` directly on it, raising:

    AttributeError: 'list' object has no attribute 'encode'

on every admin "Delete selected" / bulk-action request.
"""

from __future__ import annotations

from types import SimpleNamespace

from aquilia.admin.security import AdminCSRFProtection


def _ctx_with_session_token(token: str) -> SimpleNamespace:
    session = SimpleNamespace(data={AdminCSRFProtection.SESSION_KEY: token})
    return SimpleNamespace(session=session, request=None)


class TestValidateRequestHandlesListWrappedToken:
    def test_list_wrapped_token_matching_session_is_valid(self):
        csrf = AdminCSRFProtection(secret="test-secret")
        token = csrf.generate_token()
        ctx = _ctx_with_session_token(token)

        # This is exactly the shape multi=True form parsing produces.
        form_data = {"_csrf_token": [token], "action": ["delete"], "selected": ["1", "2"]}

        assert csrf.validate_request(ctx, form_data) is True

    def test_list_wrapped_token_not_matching_session_is_rejected(self):
        csrf = AdminCSRFProtection(secret="test-secret")
        token = csrf.generate_token()
        ctx = _ctx_with_session_token(token)

        form_data = {"_csrf_token": ["not-the-right-token"]}

        assert csrf.validate_request(ctx, form_data) is False

    def test_empty_list_token_is_rejected_not_a_crash(self):
        csrf = AdminCSRFProtection(secret="test-secret")
        token = csrf.generate_token()
        ctx = _ctx_with_session_token(token)

        form_data = {"_csrf_token": []}

        assert csrf.validate_request(ctx, form_data) is False

    def test_plain_scalar_token_still_works(self):
        csrf = AdminCSRFProtection(secret="test-secret")
        token = csrf.generate_token()
        ctx = _ctx_with_session_token(token)

        form_data = {"_csrf_token": token}

        assert csrf.validate_request(ctx, form_data) is True
