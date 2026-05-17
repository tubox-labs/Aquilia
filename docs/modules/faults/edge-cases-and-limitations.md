# Faults Edge Cases And Limitations

Structured fault taxonomy, domains, handlers, middleware, response mapping, and subsystem patch integrations.

## Source-Backed Limits

- No module-specific edge branch was detected beyond optional imports, validation, and dependency availability.

## Fault And Error Classes Detected

`FaultDomain`, `Fault`, `FaultContext`, `SecurityFaultHandler`, `ConfigFault`, `ConfigMissingFault`, `ConfigInvalidFault`, `DotenvParseFault`, `DotenvNotFoundFault`, `RegistryFault`, `DependencyCycleFault`, `ManifestInvalidFault`, `DIFault`, `ProviderNotFoundFault`, `ScopeViolationFault`, `DIResolutionFault`, `RoutingFault`, `RouteNotFoundFault`, `RouteAmbiguousFault`, `PatternInvalidFault`, `FlowFault`, `HandlerFault`, `MiddlewareFault`, `FlowCancelledFault`, `EffectFault`, `DatabaseFault`, `CacheFault`, `IOFault`, `NetworkFault`, `FilesystemFault`, `SecurityFault`, `AuthenticationFault`, `AuthorizationFault`, `CSRFViolationFault`, `CORSViolationFault`, `RateLimitExceededFault`, `CSPViolationFault`, `SigningFault`, `BadSignatureFault`, `SignatureExpiredFault`, `SignatureMalformedFault`, `UnsupportedAlgorithmFault`, `SystemFault`, `UnrecoverableFault`, `ResourceExhaustedFault`, `ModelFault`, `AMDLParseFault`, `ModelNotFoundFault`, `ModelRegistrationFault`, `MigrationFault`, `MigrationConflictFault`, `QueryFault`, `DatabaseConnectionFault`, `SchemaFault`, `FieldValidationFault`, `ProtectedDeleteFault`, `RestrictedDeleteFault`, `HTTPFault`, `BadRequestFault`, `UnauthorizedFault`, `PaymentRequiredFault`, `ForbiddenFault`, `NotFoundFault`, `MethodNotAllowedFault`, `NotAcceptableFault`, `RequestTimeoutFault`, `ConflictFault`, `GoneFault`, `PayloadTooLargeFault`, `URITooLongFault`, `UnsupportedMediaTypeFault`, `UnprocessableEntityFault`, `LockedFault`, `TooEarlyFault`, `PreconditionRequiredFault`, `TooManyRequestsFault`, `RequestHeaderFieldsTooLargeFault`, `UnavailableForLegalReasonsFault`, `InternalServerErrorFault`, `NotImplementedFault`, `BadGatewayFault`, `ServiceUnavailableFault`, `GatewayTimeoutFault`, `ProviderFault`, `ProviderAPIFault`, `ProviderAuthFault`, `ProviderRateLimitFault`, `ProviderTokenFault`, `ProviderCredentialFault`, `ProviderConnectionFault`, `DeployFault`, `DeployConfigFault`, `DeployImageFault`, `DeployHealthFault`, `DeployAppFault`, `DeployServiceFault`, `FaultEngine`, `FaultMiddleware`, `FaultHandler`, `CircularDependencyFault`, `ProviderRegistrationFault`, `AsyncResolutionFault`, `PipelineAbortedFault`, `HandlerTimeoutFault`, `MiddlewareChainFault`, `ModelFaultHandler`, `ManifestLoadFault`, `AppContextInvalidFault`, `RouteCompilationFault`, `DependencyResolutionFault`, `RouteConflictFault`, `MethodNotAllowedFault`, `RouteParameterFault`

## Operational Boundaries

- Optional external libraries are only required when the corresponding provider/backend/runtime is configured.
- Deprecated APIs generally warn when retained for migration rather than disappearing silently.
- Server startup intentionally degrades non-critical optional subsystems where source catches and logs exceptions.
- Use `api-reference.md` to check exact constructor defaults and method signatures before depending on behavior.

## Verification

- `aq doctor` for workspace/integration issues.
- `aq validate` for manifest issues.
- `aq inspect config` for merged configuration.
- `GET /_health` for live subsystem status once the app is running.
