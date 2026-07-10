import pytest

from aquilia._datastructures import MultiDict
from aquilia._uploads import FormData, UploadFile, create_upload_file_from_bytes
from aquilia.contracts import Contract
from aquilia.contracts.integration import bind_contract_to_request
from aquilia.controller.validation import validate_body
from aquilia.response import Response

# ── Declarations ───────────────────────────────────────────────────────────


class ImplicitUploadContract(Contract):
    file: UploadFile
    name: FormData


class ExplicitUploadContract(Contract):
    file: UploadFile(max_size=1024, allowed_types=["image/png", "image/jpeg"])
    name: FormData(type=int, default=42)


class OptionalUploadContract(Contract):
    file: UploadFile | None = None
    name: FormData | None = None


class CollectionUploadContract(Contract):
    files: list[UploadFile]
    tags: list[FormData]


class InnerContract(Contract):
    file: UploadFile
    title: FormData


class NestedUploadContract(Contract):
    inner: InnerContract
    outer_name: FormData


# ── Tests ───────────────────────────────────────────────────────────────────


def test_implicit_contract_instantiation():
    # Test with raw dictionary
    f = create_upload_file_from_bytes("test.png", b"hello", "image/png")
    data = {
        "file": f,
        "name": "Alice",
    }
    bp = ImplicitUploadContract(data=data)
    assert bp.is_sealed() is True
    validated = bp.validated_data
    assert validated["file"] == f
    assert validated["name"] == "Alice"


def test_explicit_contract_instantiation():
    # Test explicit contract config and validation
    f_valid = create_upload_file_from_bytes("test.png", b"small content", "image/png")

    # Valid explicit fields
    data_valid = {
        "file": f_valid,
        "name": "100",  # Will be cast to int (100)
    }
    bp1 = ExplicitUploadContract(data=data_valid)
    assert bp1.is_sealed() is True
    assert bp1.validated_data["name"] == 100
    assert bp1.validated_data["file"] == f_valid

    # Test size validation failure
    f_large = create_upload_file_from_bytes("large.png", b"x" * 2000, "image/png")
    data_large = {
        "file": f_large,
        "name": "50",
    }
    bp2 = ExplicitUploadContract(data=data_large)
    assert bp2.is_sealed() is False
    assert "file" in bp2.errors
    assert "exceeds maximum limit" in bp2.errors["file"][0]

    # Test content-type validation failure
    f_invalid_type = create_upload_file_from_bytes("test.txt", b"hello", "text/plain")
    data_invalid_type = {
        "file": f_invalid_type,
        "name": "50",
    }
    bp3 = ExplicitUploadContract(data=data_invalid_type)
    assert bp3.is_sealed() is False
    assert "file" in bp3.errors
    assert "is not allowed" in bp3.errors["file"][0]

    # Test wildcard content-type validation
    class WildcardContract(Contract):
        file: UploadFile(allowed_types=["image/*"])

    f_wildcard = create_upload_file_from_bytes("test.jpg", b"hello", "image/jpeg")
    bp_wc = WildcardContract(data={"file": f_wildcard})
    assert bp_wc.is_sealed() is True


def test_optional_fields():
    # Test that optional fields permit None
    bp1 = OptionalUploadContract(data={"file": None, "name": None})
    assert bp1.is_sealed() is True
    assert bp1.validated_data["file"] is None
    assert bp1.validated_data["name"] is None

    # Test missing fields on optional also seals correctly (defaults to None)
    bp2 = OptionalUploadContract(data={})
    assert bp2.is_sealed() is True
    assert bp2.validated_data["file"] is None
    assert bp2.validated_data["name"] is None


def test_collections():
    f1 = create_upload_file_from_bytes("f1.png", b"f1", "image/png")
    f2 = create_upload_file_from_bytes("f2.png", b"f2", "image/png")

    # Test collections of files and form data
    # Standard MultiDict structure
    form_data = FormData(fields=MultiDict([("tags", "tag1"), ("tags", "tag2")]), files={"files": [f1, f2]})
    bp = CollectionUploadContract(data=form_data)
    assert bp.is_sealed() is True
    assert bp.validated_data["files"] == [f1, f2]
    assert bp.validated_data["tags"] == ["tag1", "tag2"]


def test_nested_contracts():
    f = create_upload_file_from_bytes("nested.png", b"nested", "image/png")

    # Nested mapping payload
    form_data = FormData(
        fields=MultiDict([("inner.title", "Inner Title"), ("outer_name", "Outer Name")]), files={"inner.file": [f]}
    )
    bp = NestedUploadContract(data=form_data)
    assert bp.is_sealed() is True
    assert bp.validated_data["outer_name"] == "Outer Name"
    assert bp.validated_data["inner"]["title"] == "Inner Title"
    assert bp.validated_data["inner"]["file"] == f


# ── Request Binding Integration Tests ──────────────────────────────────────


@pytest.mark.asyncio
async def test_bind_contract_to_multipart_request():
    f = create_upload_file_from_bytes("avatar.png", b"avatar bytes", "image/png")
    form_data = FormData(fields=MultiDict([("name", "Bob")]), files={"file": [f]})

    class MockRequest:
        def __init__(self):
            self.headers = {"content-type": "multipart/form-data; boundary=xyz"}

        async def multipart(self):
            return form_data

    # Test integration binding
    bp = await bind_contract_to_request(ImplicitUploadContract, MockRequest())
    assert bp.is_sealed() is True
    assert bp.validated_data["name"] == "Bob"
    assert bp.validated_data["file"] == f


@pytest.mark.asyncio
async def test_bind_contract_to_urlencoded_request():
    class UrlencodedContract(Contract):
        name: FormData(type=str)
        age: FormData(type=int)
        is_admin: FormData(type=bool)

    form_data = FormData(fields=MultiDict([("name", "Bob"), ("age", "30"), ("is_admin", "true")]), files={})

    class MockRequest:
        def __init__(self):
            self.headers = {"content-type": "application/x-www-form-urlencoded"}

        async def form(self):
            return form_data

    bp = await bind_contract_to_request(UrlencodedContract, MockRequest())
    assert bp.is_sealed() is True
    assert bp.validated_data["name"] == "Bob"
    assert bp.validated_data["age"] == 30
    assert bp.validated_data["is_admin"] is True


@pytest.mark.asyncio
async def test_validate_body_decorator_multipart():
    f = create_upload_file_from_bytes("avatar.png", b"avatar bytes", "image/png")
    form_data = FormData(fields=MultiDict([("name", "Bob")]), files={"file": [f]})

    executed = {}

    @validate_body(ImplicitUploadContract)
    async def handler(self, ctx, body=None):
        executed["body"] = body
        return Response.json({"ok": True})

    class FakeCtx:
        async def multipart(self):
            return form_data

        class request:
            headers = {"content-type": "multipart/form-data; boundary=xyz"}

    resp = await handler(None, FakeCtx())
    assert executed["body"]["name"] == "Bob"
    assert executed["body"]["file"] == f


# ── Regression / JSON Validation Tests ──────────────────────────────────────


@pytest.mark.asyncio
async def test_json_validation_unchanged():
    class SimpleJSONContract(Contract):
        name: str
        age: int

    class FakeCtx:
        async def body(self):
            return b'{"name": "Alice", "age": 25}'

        class request:
            headers = {"content-type": "application/json"}

    executed = {}

    @validate_body(SimpleJSONContract)
    async def handler(self, ctx, body=None):
        executed["body"] = body
        return Response.json({"ok": True})

    await handler(None, FakeCtx())
    assert executed["body"]["name"] == "Alice"
    assert executed["body"]["age"] == 25


def test_missing_required_fields():
    bp = ImplicitUploadContract(data={})
    assert bp.is_sealed() is False
    assert "file" in bp.errors
    assert "name" in bp.errors


def test_invalid_field_types():
    bp = ExplicitUploadContract(
        data={"file": create_upload_file_from_bytes("test.png", b"hello", "image/png"), "name": "not-an-int"}
    )
    assert bp.is_sealed() is False
    assert "name" in bp.errors


def test_empty_uploads():
    f_empty = create_upload_file_from_bytes("empty.png", b"", "image/png")
    bp = ImplicitUploadContract(data={"file": f_empty, "name": "Bob"})
    assert bp.is_sealed() is True
    assert bp.validated_data["file"].size == 0
