"""
Aquilia Discovery - Component auto-discovery subsystem.

Architecture v2: Provides both runtime package scanning and static AST-based
component discovery with manifest auto-sync capabilities.

Components:
    - PackageScanner: Runtime introspection-based class discovery (from utils)
    - AutoDiscoveryEngine: AST-based discovery + manifest sync (v2)
    - ASTClassifier: Classifies classes by base class/decorator without importing
    - FileScanner: Finds Python files matching discovery patterns
    - ManifestDiffer: Compares discovered vs. declared components
    - ManifestWriter: Auto-updates manifest.py files

Usage:
    # Runtime discovery (original)
    scanner = PackageScanner()
    classes = scanner.scan_package("myapp.modules.users.controllers")
    
    # Static discovery with auto-sync (v2)
    engine = AutoDiscoveryEngine(Path("myapp/modules"))
    result = engine.discover("users")
    report = engine.sync_manifest("users")
"""

from aquilia.utils.scanner import PackageScanner
from .engine import (
    AutoDiscoveryEngine,
    ASTClassifier,
    FileScanner,
    ManifestDiffer,
    ManifestWriter,
    ClassifiedComponent,
    DiscoveryResult,
    SyncAction,
    SyncReport,
)

__all__ = [
    "PackageScanner",
    "AutoDiscoveryEngine",
    "ASTClassifier",
    "FileScanner",
    "ManifestDiffer",
    "ManifestWriter",
    "ClassifiedComponent",
    "DiscoveryResult",
    "SyncAction",
    "SyncReport",
]

