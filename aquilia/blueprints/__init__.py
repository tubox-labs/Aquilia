"""
Aquilia Blueprints -- first-class model↔world contracts.

A Blueprint declares the contract between a Model and the outside world:
what the world sees (Facets), named subsets (Projections), how data
enters (Casts), how integrity is enforced (Seals), and how data is
written back (Imprints).

Quick Start::

    from aquilia.blueprints import Blueprint, Facet, Lens, Computed, Constant

    class ProductBlueprint(Blueprint):
        class Spec:
            model = Product
            projections = {
                "summary": ["id", "name", "price"],
                "detail": "__all__",
            }

    # Outbound: Model → dict
    bp = ProductBlueprint(instance=product)
    data = bp.data  # respects default projection

    # With projection:
    bp = ProductBlueprint(instance=product, projection="summary")
    data = bp.data

    # Inbound: dict → validated data
    bp = ProductBlueprint(data={"name": "Widget", "price": 9.99})
    if bp.is_sealed():
        product = await bp.imprint()

    # Route-level:
    @GET("/products", response_blueprint=ProductBlueprint["summary"])
    async def list_products():
        return await Product.objects.all()
"""

from .annotations import Field, NestedBlueprintFacet, computed
from .core import Blueprint, BlueprintMeta, BlueprintUnion, ColumnarReport, SealOutcome
from .exceptions import (
    BLUEPRINT,
    BlueprintAsyncMismatchFault,
    BlueprintFault,
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
    bind_blueprint_to_request,
    is_blueprint_class,
    is_projected_blueprint,
    render_blueprint_response,
    resolve_blueprint_from_annotation,
)
from .lenses import Lens
from .projections import ProjectionRegistry
from .schema import generate_component_schemas, generate_schema
from .sigil import FieldSpec, Sigil
from .ward import WardMethod, ward

__all__ = [
    # Core
    "Blueprint",
    "BlueprintMeta",
    "ward",
    "WardMethod",
    "Sigil",
    "FieldSpec",
    "SealOutcome",
    "ColumnarReport",
    "BlueprintUnion",
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
    "NestedBlueprintFacet",
    # Lenses
    "Lens",
    # Projections
    "ProjectionRegistry",
    # Exceptions
    "BlueprintFault",
    "BlueprintAsyncMismatchFault",
    "CastFault",
    "SealFault",
    "ImprintFault",
    "ProjectionFault",
    "LensDepthFault",
    "LensCycleFault",
    "BLUEPRINT",
    # Schema
    "generate_schema",
    "generate_component_schemas",
    # Integration
    "is_blueprint_class",
    "is_projected_blueprint",
    "resolve_blueprint_from_annotation",
    "bind_blueprint_to_request",
    "render_blueprint_response",
]
