"""Tests for request body validation via @validate_body."""

import pytest

from aquilia.contracts import Contract
from aquilia.contracts.facets import IntFacet, TextFacet
from aquilia.controller.validation import (
    RequestBodyParseFault,
    RequestBodyValidationFault,
    validate_body,
)
from aquilia.response import Response


class CreateUserContract(Contract):
    name = TextFacet(required=True, max_length=150)
    email = TextFacet(required=True)
    age = IntFacet(required=False, min_value=0, max_value=150)

    class Spec:
        projections = {"__all__": ["name", "email", "age"]}


class TestValidationFaults:
    def test_validation_fault_is_fault(self):
        fault = RequestBodyValidationFault()
        assert fault.code == "validation.body_invalid"

    def test_parse_fault(self):
        fault = RequestBodyParseFault()
        assert fault.code == "validation.body_parse_error"


class TestValidateBody:
    @pytest.mark.asyncio
    async def test_valid_body_passes(self):
        executed = {}

        @validate_body(CreateUserContract)
        async def handler(self, ctx, body=None):
            executed["body"] = body

        class FakeCtx:
            async def body(self):
                return b'{"name":"Alice","email":"a@b.com","age":30}'

            class request:
                headers = {"content-type": "application/json"}

            async def form(self):
                return {}

        await handler(None, FakeCtx())
        assert executed["body"]["name"] == "Alice"

    @pytest.mark.asyncio
    async def test_invalid_json(self):
        @validate_body(CreateUserContract)
        async def handler(self, ctx, body=None):
            pass

        class FakeCtx:
            async def body(self):
                return b"not json"

            class request:
                headers = {"content-type": "application/json"}

            async def form(self):
                return {}

        resp = await handler(None, FakeCtx())
        assert isinstance(resp, Response)
        assert resp.status == 400

    def test_decorator_preserves_name(self):
        @validate_body(CreateUserContract)
        async def my_handler(self, ctx, body=None):
            pass

        assert my_handler.__name__ == "my_handler"
