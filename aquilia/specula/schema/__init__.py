"""Specula schema subsystem — OpenAPI 3.1.0 generation and schema bridges."""

from .builder import ParsedDocstring, SpeculaBuilder
from .contract import contract_components, contract_to_schema
from .fault import aquilia_error_schema, aquilia_validation_error_schema, fault_to_response
from .model import FIELD_SCHEMA_MAP, model_components, model_to_schema
from .standard import STANDARD_SCHEMAS
from .types import python_type_to_schema

__all__ = [
    "SpeculaBuilder",
    "ParsedDocstring",
    "contract_to_schema",
    "contract_components",
    "model_to_schema",
    "model_components",
    "FIELD_SCHEMA_MAP",
    "python_type_to_schema",
    "aquilia_error_schema",
    "aquilia_validation_error_schema",
    "fault_to_response",
    "STANDARD_SCHEMAS",
]
