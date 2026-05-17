# Mlops Edge Cases And Limitations

Model operations platform: modelpacks, serving, registries, runtimes, orchestration, observability, rollout, optimization, plugins, scheduler, and security.

## Source-Backed Limits

- No module-specific edge branch was detected beyond optional imports, validation, and dependency availability.

## Fault And Error Classes Detected

`MLOpsFault`, `PackFault`, `PackBuildFault`, `PackIntegrityFault`, `PackSignatureFault`, `RegistryFault`, `RegistryConnectionFault`, `PackNotFoundFault`, `ImmutabilityViolationFault`, `ServingFault`, `RuntimeLoadFault`, `InferenceFault`, `BatchTimeoutFault`, `WarmupFault`, `ObserveFault`, `DriftDetectionFault`, `MetricsExportFault`, `RolloutFault`, `RolloutAdvanceFault`, `AutoRollbackFault`, `SchedulerFault`, `PlacementFault`, `ScalingFault`, `MLOpsSecurityFault`, `SigningFault`, `PermissionDeniedFault`, `EncryptionFault`, `PluginFault`, `PluginLoadFault`, `PluginHookFault`, `CircuitBreakerFault`, `CircuitBreakerOpenFault`, `CircuitBreakerExhaustedFault`, `RateLimitFault`, `StreamingFault`, `StreamInterruptedFault`, `TokenLimitExceededFault`, `MemoryFault`, `MemorySoftLimitFault`, `MemoryHardLimitFault`, `ManifestValidationError`, `SignatureError`, `RegistryError`, `PackNotFoundError`, `ImmutabilityError`

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
