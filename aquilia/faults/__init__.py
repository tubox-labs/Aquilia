"""
AquilaFaults - Production-grade fault handling system.

Exceptions in Aquilia are NOT just errors -- they are **typed fault signals**
that flow through the system with context, lifecycle, and intent.

Philosophy:
- Errors are data, not surprises
- Errors flow through pipelines
- Errors are scoped
- Errors are observable
- Errors are explicit

Core exports:
- Fault: Base fault class
- FaultContext: Runtime context wrapper
- FaultDomain: Domain enumeration
- Severity: Severity levels
- FaultEngine: Runtime fault handler
- FaultHandler: Abstract handler base

Subsystem integrations available in:
- faults.integrations.registry: Registry validation faults
- faults.integrations.di: Dependency injection faults
- faults.integrations.routing: Route matching faults
- faults.integrations.flow: Pipeline and middleware faults
"""

from .core import (
    Escalate,
    Fault,
    FaultContext,
    FaultDomain,
    FaultResult,
    RecoveryStrategy,
    Resolved,
    Severity,
    Transformed,
)
from .default_handlers import (
    ExceptionAdapter,
    FatalHandler,
    HTTPResponse,
    LoggingHandler,
    ResponseMapper,
    RetryHandler,
    SecurityFaultHandler,
)
from .domains import (
    AMDLParseFault,
    AuthenticationFault,
    AuthorizationFault,
    BadGatewayFault,
    BadRequestFault,
    BadSignatureFault,
    CacheFault,
    # Config faults
    ConfigFault,
    ConfigInvalidFault,
    ConfigMissingFault,
    ConflictFault,
    CORSViolationFault,
    CSPViolationFault,
    CSRFViolationFault,
    DatabaseConnectionFault,
    DatabaseFault,
    DependencyCycleFault,
    DeployAppFault,
    DeployConfigFault,
    # Deploy faults
    DeployFault,
    DeployHealthFault,
    DeployImageFault,
    DeployServiceFault,
    # DI faults
    DIFault,
    DIResolutionFault,
    # Effect faults
    EffectFault,
    FieldValidationFault,
    FilesystemFault,
    FlowCancelledFault,
    # Flow faults
    FlowFault,
    ForbiddenFault,
    GatewayTimeoutFault,
    GoneFault,
    HandlerFault,
    # HTTP faults
    HTTPFault,
    InternalServerErrorFault,
    # IO faults
    IOFault,
    LockedFault,
    ManifestInvalidFault,
    MethodNotAllowedFault,
    MiddlewareFault,
    MigrationConflictFault,
    MigrationFault,
    # Model faults
    ModelFault,
    ModelNotFoundFault,
    ModelRegistrationFault,
    NetworkFault,
    NotAcceptableFault,
    NotFoundFault,
    NotImplementedFault,
    PatternInvalidFault,
    PayloadTooLargeFault,
    PaymentRequiredFault,
    PreconditionRequiredFault,
    ProtectedDeleteFault,
    ProviderAPIFault,
    ProviderAuthFault,
    ProviderConnectionFault,
    ProviderCredentialFault,
    # Provider faults
    ProviderFault,
    ProviderNotFoundFault,
    ProviderRateLimitFault,
    ProviderTokenFault,
    QueryFault,
    RateLimitExceededFault,
    # Registry faults
    RegistryFault,
    RequestHeaderFieldsTooLargeFault,
    RequestTimeoutFault,
    ResourceExhaustedFault,
    RestrictedDeleteFault,
    RouteAmbiguousFault,
    RouteNotFoundFault,
    # Routing faults
    RoutingFault,
    SchemaFault,
    ScopeViolationFault,
    # Security faults
    SecurityFault,
    ServiceUnavailableFault,
    SignatureExpiredFault,
    SignatureMalformedFault,
    # Signing faults
    SigningFault,
    # System faults
    SystemFault,
    TooEarlyFault,
    TooManyRequestsFault,
    UnauthorizedFault,
    UnavailableForLegalReasonsFault,
    UnprocessableEntityFault,
    UnrecoverableFault,
    UnsupportedAlgorithmFault,
    UnsupportedMediaTypeFault,
    URITooLongFault,
    http_reason,
)
from .engine import (
    FaultEngine,
    get_default_engine,
    process_fault,
)
from .handlers import FaultHandler

__all__ = [
    # Core types
    "Fault",
    "FaultContext",
    "FaultDomain",
    "Severity",
    "FaultResult",
    "Resolved",
    "Transformed",
    "Escalate",
    "RecoveryStrategy",
    # Runtime
    "FaultEngine",
    "FaultHandler",
    "get_default_engine",
    "process_fault",
    # Default handlers
    "ExceptionAdapter",
    "RetryHandler",
    "SecurityFaultHandler",
    "ResponseMapper",
    "FatalHandler",
    "LoggingHandler",
    "HTTPResponse",
    # Config faults
    "ConfigFault",
    "ConfigMissingFault",
    "ConfigInvalidFault",
    # Registry faults
    "RegistryFault",
    "DependencyCycleFault",
    "ManifestInvalidFault",
    # DI faults
    "DIFault",
    "ProviderNotFoundFault",
    "ScopeViolationFault",
    "DIResolutionFault",
    # Routing faults
    "RoutingFault",
    "RouteNotFoundFault",
    "RouteAmbiguousFault",
    "PatternInvalidFault",
    # Flow faults
    "FlowFault",
    "HandlerFault",
    "MiddlewareFault",
    "FlowCancelledFault",
    # Effect faults
    "EffectFault",
    "DatabaseFault",
    "CacheFault",
    # IO faults
    "IOFault",
    "NetworkFault",
    "FilesystemFault",
    # Model faults
    "ModelFault",
    "AMDLParseFault",
    "ModelNotFoundFault",
    "ModelRegistrationFault",
    "MigrationFault",
    "MigrationConflictFault",
    "QueryFault",
    "DatabaseConnectionFault",
    "SchemaFault",
    "FieldValidationFault",
    "ProtectedDeleteFault",
    "RestrictedDeleteFault",
    # Security faults
    "SecurityFault",
    "AuthenticationFault",
    "AuthorizationFault",
    "CSRFViolationFault",
    "CORSViolationFault",
    "RateLimitExceededFault",
    "CSPViolationFault",
    # Signing faults
    "SigningFault",
    "BadSignatureFault",
    "SignatureExpiredFault",
    "SignatureMalformedFault",
    "UnsupportedAlgorithmFault",
    # System faults
    "SystemFault",
    "UnrecoverableFault",
    "ResourceExhaustedFault",
    # Provider faults
    "ProviderFault",
    "ProviderAPIFault",
    "ProviderAuthFault",
    "ProviderRateLimitFault",
    "ProviderTokenFault",
    "ProviderCredentialFault",
    "ProviderConnectionFault",
    # Deploy faults
    "DeployFault",
    "DeployConfigFault",
    "DeployImageFault",
    "DeployHealthFault",
    "DeployAppFault",
    "DeployServiceFault",
    # HTTP faults
    "HTTPFault",
    "http_reason",
    "BadRequestFault",
    "UnauthorizedFault",
    "PaymentRequiredFault",
    "ForbiddenFault",
    "NotFoundFault",
    "MethodNotAllowedFault",
    "NotAcceptableFault",
    "RequestTimeoutFault",
    "ConflictFault",
    "GoneFault",
    "PayloadTooLargeFault",
    "URITooLongFault",
    "UnsupportedMediaTypeFault",
    "UnprocessableEntityFault",
    "LockedFault",
    "TooEarlyFault",
    "PreconditionRequiredFault",
    "TooManyRequestsFault",
    "RequestHeaderFieldsTooLargeFault",
    "UnavailableForLegalReasonsFault",
    "InternalServerErrorFault",
    "NotImplementedFault",
    "BadGatewayFault",
    "ServiceUnavailableFault",
    "GatewayTimeoutFault",
]
