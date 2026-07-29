"""
Tests for ``.pyi`` stub generation (BP-SEC-035).

A Contract resolves its fields at class-body evaluation time and serves them
through ``__getattr__``, so a type checker sees nothing. These tests cover the
generator that closes that gap: the per-facet Python types, the module stub it
assembles, and the ``aq contracts stubs --check`` staleness gate.
"""

from __future__ import annotations

import enum
import sys
import textwrap
from pathlib import Path

import pytest

from aquilia.contracts import Contract
from aquilia.contracts.exceptions import StubGenerationFault
from aquilia.contracts.facets import (
    BoolFacet,
    ChoiceFacet,
    Constant,
    DateTimeFacet,
    DecimalFacet,
    DictFacet,
    FloatFacet,
    IntFacet,
    ListFacet,
    PathFacet,
    SecretFacet,
    SetFacet,
    TextFacet,
    TupleFacet,
    UUIDFacet,
)
from aquilia.contracts.lenses import Lens
from aquilia.contracts.stubs import contract_stub_body, generate_module_stub, write_module_stub


# ---------------------------------------------------------------------------
# BP-SEC-035a — facet Python types
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("facet", "expected"),
    [
        (TextFacet(), "str"),
        (IntFacet(), "int"),
        (FloatFacet(), "float"),
        (BoolFacet(), "bool"),
        (DecimalFacet(), "decimal.Decimal"),
        (DateTimeFacet(), "datetime.datetime"),
        (UUIDFacet(), "uuid.UUID"),
        (PathFacet(), "pathlib.PurePosixPath"),
        (SecretFacet(), "aquilia.contracts.facets.Secret"),
    ],
)
def test_scalar_facets_declare_their_validated_type(facet, expected):
    assert facet.python_type() == expected


def test_secret_is_not_typed_as_str():
    """``cast`` wraps the value, so promising ``str`` would be a lie the type
    checker cannot catch."""
    assert SecretFacet().python_type() != "str"


@pytest.mark.parametrize(
    ("facet", "expected"),
    [
        (ListFacet(child=TextFacet()), "list[str]"),
        (ListFacet(), "list[Any]"),
        (SetFacet(child=IntFacet()), "set[int]"),
        (TupleFacet(child=IntFacet()), "tuple[int, ...]"),
        (DictFacet(value_facet=IntFacet()), "dict[str, int]"),
        (DictFacet(), "dict[str, Any]"),
    ],
)
def test_container_facets_propagate_their_child_type(facet, expected):
    assert facet.python_type() == expected


def test_nested_containers_compose():
    facet = ListFacet(child=ListFacet(child=IntFacet()))
    assert facet.python_type() == "list[list[int]]"


def test_choice_facet_narrows_to_literal():
    assert ChoiceFacet(choices=["new", "paid"]).python_type() == "Literal['new', 'paid']"


def test_choice_facet_with_unliteralable_values_degrades_to_any():
    """``Literal`` admits only str/int/bool/None; anything else must not be
    emitted or the stub will not parse."""
    import datetime

    facet = ChoiceFacet(choices=[datetime.date(2020, 1, 1)])
    assert facet.python_type() == "Any"


def test_constant_facet_narrows_to_literal():
    assert Constant("v2").python_type() == "Literal['v2']"


def test_enum_facet_names_its_enum_class():
    from aquilia.contracts.facets import EnumFacet

    facet = EnumFacet(_Colour)
    assert facet.python_type() == f"{__name__}._Colour"


def test_lens_molds_to_a_mapping_not_a_contract():
    """A Lens produces the target's *molded dict*. Annotating it as the
    Contract class would let ``order.customer.is_sealed()`` type-check against
    a value that is a dict at runtime."""
    assert Lens(_AddressContract).python_type() == "dict[str, Any]"
    assert Lens(_AddressContract, many=True).python_type() == "list[dict[str, Any]]"


# ---------------------------------------------------------------------------
# BP-SEC-035b — contract bodies
# ---------------------------------------------------------------------------


class _Colour(enum.Enum):
    RED = "red"
    BLUE = "blue"


class _AddressContract(Contract):
    city = TextFacet()


class _OrderContract(Contract):
    id = IntFacet()
    total = DecimalFacet()
    tags = ListFacet(child=TextFacet())
    note = TextFacet(allow_null=True)


def test_contract_body_declares_every_facet():
    body = contract_stub_body(_OrderContract)
    assert "    id: int" in body
    assert "    total: decimal.Decimal" in body
    assert "    tags: list[str]" in body


def test_nullable_facet_is_widened_to_optional():
    """Omitting ``| None`` is worse than no stub: it tells the checker a guard
    is unnecessary at exactly the point one is required."""
    assert "    note: str | None" in contract_stub_body(_OrderContract)


def test_facet_defaulting_to_none_is_also_optional():
    class _WithDefault(Contract):
        nickname = TextFacet(default=None)

    assert "    nickname: str | None" in contract_stub_body(_WithDefault)


def test_contract_with_no_facets_still_produces_a_valid_body():
    class _Empty(Contract):
        pass

    assert contract_stub_body(_Empty) == ["    ..."]


# ---------------------------------------------------------------------------
# BP-SEC-035c — module stubs
# ---------------------------------------------------------------------------


_MODULE_SOURCE = textwrap.dedent(
    '''
    """Fixture module for stub generation."""

    from __future__ import annotations

    import enum

    from aquilia.contracts import Contract
    from aquilia.contracts.facets import ChoiceFacet, DecimalFacet, IntFacet, ListFacet, TextFacet


    class Colour(enum.Enum):
        RED = "red"
        BLUE = "blue"


    class AddressContract(Contract):
        city = TextFacet()
        zip = TextFacet(allow_null=True)


    class OrderContract(Contract):
        id = IntFacet()
        total = DecimalFacet()
        tags = ListFacet(child=TextFacet())
        status = ChoiceFacet(choices=["new", "paid"])

        async def refresh(self, count: int) -> str: ...
    '''
)


@pytest.fixture
def stub_module(tmp_path, monkeypatch, request):
    """Import a throwaway Contract module and clean it out of ``sys.modules``."""
    name = f"_stub_fixture_{abs(hash(request.node.nodeid)) % 10**8}"
    (tmp_path / f"{name}.py").write_text(_MODULE_SOURCE, encoding="utf-8")
    monkeypatch.syspath_prepend(str(tmp_path))

    import importlib

    module = importlib.import_module(name)
    yield module
    sys.modules.pop(name, None)


def test_module_stub_lands_beside_the_source(stub_module):
    report = generate_module_stub(stub_module)
    assert report.path.suffix == ".pyi"
    assert report.path.stem == Path(stub_module.__file__).stem


def test_module_stub_lists_the_contracts_it_covered(stub_module):
    report = generate_module_stub(stub_module)
    assert report.contracts == ("AddressContract", "OrderContract")


def test_module_stub_is_syntactically_valid_python(stub_module):
    import ast

    ast.parse(generate_module_stub(stub_module).source)


def test_module_stub_declares_facet_types(stub_module):
    source = generate_module_stub(stub_module).source
    assert "    id: int" in source
    assert "    total: decimal.Decimal" in source
    assert "    status: Literal['new', 'paid']" in source
    assert "    zip: str | None" in source


def test_module_stub_replays_source_imports(stub_module):
    """Method signatures come back as source text under PEP 563, so they only
    resolve against the module's own imports."""
    source = generate_module_stub(stub_module).source
    assert "from aquilia.contracts import Contract" in source


def test_module_stub_omits_the_future_import(stub_module):
    """``from __future__ import annotations`` must be the first statement, and
    the header comment already occupies that position."""
    assert "__future__" not in generate_module_stub(stub_module).source


def test_module_stub_imports_annotation_modules(stub_module):
    """``decimal.Decimal`` in an annotation is meaningless without the import."""
    assert "import decimal" in generate_module_stub(stub_module).source


def test_module_stub_does_not_duplicate_imports(stub_module):
    source = generate_module_stub(stub_module).source
    assert source.count("import enum\n") == 1


def test_enum_members_are_assigned_not_annotated(stub_module):
    """An annotated member is a *non-member attribute* per the typing spec, so
    mypy reads the enum as having zero members."""
    source = generate_module_stub(stub_module).source
    assert "    RED = 'red'" in source
    assert "    RED: Colour" not in source


def test_async_methods_keep_their_async_marker(stub_module):
    assert "async def refresh" in generate_module_stub(stub_module).source


def test_signature_annotations_are_not_quoted(stub_module):
    """PEP 563 hands ``inspect`` strings; rendering them raw keeps the stub
    consistent instead of mixing ``x: int`` and ``x: 'int'``."""
    source = generate_module_stub(stub_module).source
    assert "def refresh(self, count: int) -> str: ..." in source


def test_module_without_a_source_file_is_rejected():
    """A namespace or synthetic module has nowhere for a stub to live."""
    import types

    module = types.ModuleType("_no_file_module")
    with pytest.raises(StubGenerationFault):
        generate_module_stub(module)


# ---------------------------------------------------------------------------
# BP-SEC-035d — writing and the staleness gate
# ---------------------------------------------------------------------------


def test_write_creates_the_stub_file(stub_module):
    report = write_module_stub(stub_module)
    assert report.path.read_text(encoding="utf-8") == report.source


def test_dry_run_does_not_touch_the_filesystem(stub_module):
    report = write_module_stub(stub_module, dry_run=True)
    assert not report.path.exists()


def test_missing_stub_is_reported_as_not_current(stub_module):
    assert write_module_stub(stub_module, dry_run=True).is_current is False


def test_freshly_written_stub_is_current(stub_module):
    write_module_stub(stub_module)
    assert write_module_stub(stub_module, dry_run=True).is_current is True


def test_stale_stub_is_reported_as_not_current(stub_module):
    report = write_module_stub(stub_module)
    report.path.write_text("# hand-edited\n", encoding="utf-8")
    assert write_module_stub(stub_module, dry_run=True).is_current is False


def test_generation_is_deterministic(stub_module):
    """``--check`` is only meaningful if regenerating unchanged input is a
    no-op; iteration order that varies would fail CI at random."""
    first = generate_module_stub(stub_module).source
    second = generate_module_stub(stub_module).source
    assert first == second
