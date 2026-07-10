"""
Aquilia Contracts -- first-class model↔world contracts.

A Contract declares the contract between a Model and the outside world:
what the world sees (Facets), named subsets (Projections), how data
enters (Casts), how integrity is enforced (Seals), and how data is
written back (Imprints).

Quick Start::

    from aquilia.contracts import Contract, Facet, Lens, Computed, Constant

    class ProductContract(Contract):
        class Spec:
            model = Product
            projections = {
                "summary": ["id", "name", "price"],
                "detail": "__all__",
            }

    # Outbound: Model → dict
    bp = ProductContract(instance=product)
    data = bp.data  # respects default projection

    # With projection:
    bp = ProductContract(instance=product, projection="summary")
    data = bp.data

    # Inbound: dict → validated data
    bp = ProductContract(data={"name": "Widget", "price": 9.99})
    if bp.is_sealed():
        product = await bp.imprint()

    # Route-level:
    @GET("/products", response_contract=ProductContract["summary"])
    async def list_products():
        return await Product.objects.all()
"""

from .annotations import Field, NestedContractFacet, computed
from .core import Contract, ContractMeta, ContractUnion, ColumnarReport, SealOutcome
from .exceptions import (
    CONTRACT,
    ContractAsyncMismatchFault,
    ContractFault,
    CastFault,
    ImprintFault,
    LensCycleFault,
    LensDepthFault,
    ProjectionFault,
    SealFault,
)
from .facets import (
    MODEL_FIELD_TO_FACET,
    UNSET,
    # Boolean
    BoolFacet,
    ChoiceFacet,
    # Special
    Computed,
    Constant,
    # Date/Time
    DateFacet,
    DateTimeFacet,
    DecimalFacet,
    DictFacet,
    DurationFacet,
    EmailFacet,
    EnumFacet,
    # Base
    Facet,
    FileFacet,
    FloatFacet,
    FormDataFacet,
    Hidden,
    Inject,
    # Numeric
    IntFacet,
    IPFacet,
    JSONFacet,
    # Structured
    ListFacet,
    LiteralFacet,
    ReadOnly,
    SetFacet,
    SlugFacet,
    # Text
    TextFacet,
    TimeFacet,
    TupleFacet,
    UploadFileFacet,
    URLFacet,
    UUIDFacet,
    WriteOnly,
    # Utilities
    derive_facet,
)
from .integration import (
    bind_contract_to_request,
    is_contract_class,
    is_projected_contract,
    render_contract_response,
    resolve_contract_from_annotation,
)
from .lenses import Lens
from .projections import ProjectionRegistry
from .schema import generate_component_schemas, generate_schema
from .sigil import FieldSpec, Sigil
from .ward import WardMethod, ward

__all__ = [
    # Core
    "Contract",
    "ContractMeta",
    "ward",
    "WardMethod",
    "Sigil",
    "FieldSpec",
    "SealOutcome",
    "ColumnarReport",
    "ContractUnion",
    # Facets
    "Facet",
    "UNSET",
    "TextFacet",
    "EmailFacet",
    "URLFacet",
    "SlugFacet",
    "IPFacet",
    "IntFacet",
    "FloatFacet",
    "DecimalFacet",
    "BoolFacet",
    "DateFacet",
    "TimeFacet",
    "DateTimeFacet",
    "DurationFacet",
    "UUIDFacet",
    "ListFacet",
    "SetFacet",
    "TupleFacet",
    "DictFacet",
    "JSONFacet",
    "FileFacet",
    "ChoiceFacet",
    "LiteralFacet",
    "EnumFacet",
    "UploadFileFacet",
    "FormDataFacet",
    "Computed",
    "Constant",
    "WriteOnly",
    "ReadOnly",
    "Hidden",
    "Inject",
    "derive_facet",
    "MODEL_FIELD_TO_FACET",
    # Annotations
    "Field",
    "computed",
    "NestedContractFacet",
    # Lenses
    "Lens",
    # Projections
    "ProjectionRegistry",
    # Exceptions
    "ContractFault",
    "ContractAsyncMismatchFault",
    "CastFault",
    "SealFault",
    "ImprintFault",
    "ProjectionFault",
    "LensDepthFault",
    "LensCycleFault",
    "CONTRACT",
    # Schema
    "generate_schema",
    "generate_component_schemas",
    # Integration
    "is_contract_class",
    "is_projected_contract",
    "resolve_contract_from_annotation",
    "bind_contract_to_request",
    "render_contract_response",
]
