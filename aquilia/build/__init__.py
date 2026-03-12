"""
Aquilia Build System -- compile-before-serve pipeline.

Provides a complete build pipeline that:
1. Discovers all modules and components (AST-based, no imports)
2. Validates manifests, routes, dependencies, and Python syntax
3. Compiles manifests to typed artifacts
4. Bundles artifacts into Crous binary format (compact, checksummed)
5. Generates integrity fingerprints for deployment gating
6. Reports errors with file:line references (build fails = server doesn't start)

Usage::

 from aquilia.build import AquiliaBuildPipeline, BuildConfig

 # Dev mode (fast, no compression)
 result = AquiliaBuildPipeline.build(workspace_root=".", mode="dev")

 # Prod mode (compressed, signed, integrity-verified)
 result = AquiliaBuildPipeline.build(workspace_root=".", mode="prod")

 if result.success:
 server = result.create_server
 else:
 for err in result.errors:
 print(err)

The ``aq run``, ``aq serve``, and ``aq build`` CLI commands all use this
pipeline to ensure consistent build semantics across dev/prod workflows.
"""

from .bundler import BundleManifest, CrousBundler
from .checker import CheckError, CheckResult, StaticChecker
from .pipeline import (
    AquiliaBuildPipeline,
    BuildConfig,
    BuildError,
    BuildManifest,
    BuildPhase,
    BuildResult,
)
from .resolver import BuildResolver, ResolvedBuild

__all__ = [
    # Pipeline
    "AquiliaBuildPipeline",
    "BuildResult",
    "BuildConfig",
    "BuildPhase",
    "BuildError",
    "BuildManifest",
    # Checker
    "StaticChecker",
    "CheckResult",
    "CheckError",
    # Bundler
    "CrousBundler",
    "BundleManifest",
    # Resolver
    "BuildResolver",
    "ResolvedBuild",
]
