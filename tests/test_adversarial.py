from typing import Annotated

import pytest

from aquilia.contracts import Contract, Facet, ward
from aquilia.contracts.exceptions import CastFault


def test_regex_redos_defense():
    # Defining a potentially vulnerable regex pattern should raise CastFault at definition time
    with pytest.raises(CastFault) as exc_info:

        class PatternBP(Contract):
            val: Annotated[str, Facet.text(pattern=r"^(a+)+$")]

    assert "ReDoS risk" in str(exc_info.value)

    # Avoid Redos by ensuring length checks work before pattern matching (if facet constraints are used)
    class RedosSafeBP(Contract):
        val: Annotated[str, Facet.text(max_length=10, pattern=r"^[a-zA-Z0-9]+$")]

    # Long malicious input should be rejected by length check immediately
    bad_bp = RedosSafeBP(data={"val": "a" * 1000})
    assert bad_bp.is_sealed() is False
    assert "val" in bad_bp.errors


def test_unicode_validation():
    class UnicodeBP(Contract):
        name: str
        emoji: str

    payload = {
        "name": "こんにちはAda",
        "emoji": "🐍🚀✨",
    }
    bp = UnicodeBP(data=payload)
    assert bp.is_sealed() is True
    assert bp.validated_data["name"] == "こんにちはAda"
    assert bp.validated_data["emoji"] == "🐍🚀✨"


def test_exceptions_inside_ward_hooks():
    class BrokenWardBP(Contract):
        name: str

        @ward
        def check_name_raises(self, data):
            raise RuntimeError("Unexpected internal crash inside hook")

    bp = BrokenWardBP(data={"name": "Ada"})
    # An unexpected exception inside a ward hook should not crash the runner;
    # it must surface as an error in the outcomes / errors dict
    assert bp.is_sealed() is False
    assert "__all__" in bp.errors
    assert "Unexpected internal crash inside hook" in bp.errors["__all__"][0]


@pytest.mark.asyncio
async def test_bad_streams_ndjson_bytes():
    class StreamBP(Contract):
        id: int
        name: str

    # Simulate an async generator yielding NDJSON bytes, containing one bad JSON line
    async def bytes_generator():
        yield b'{"id": 1, "name": "Ada"}\n'
        yield b'{"id": 2, "name": "Bob"\n'  # bad JSON (missing closing brace)
        yield b'{"id": 3, "name": "Charlie"}\n'

    outcomes = []
    async for outcome in StreamBP.seal_stream(bytes_generator()):
        outcomes.append(outcome)

    assert len(outcomes) == 3
    assert outcomes[0].ok is True
    assert outcomes[0].value["name"] == "Ada"

    # The bad JSON line should yield ok=False, value=None and error message
    assert outcomes[1].ok is False
    assert outcomes[1].value is None
    assert "__all__" in outcomes[1].errors
    assert "JSON parse error" in outcomes[1].errors["__all__"][0]

    assert outcomes[2].ok is True
    assert outcomes[2].value["name"] == "Charlie"
