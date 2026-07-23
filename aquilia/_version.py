"""
Single source of truth for the Aquilia framework version.

All subsystem __init__.py files import from here:

    from aquilia._version import __version__

The workspace generator always uses WORKSPACE_VERSION ("1.0.0") so that
generated workspace.py files are not pinned to the framework release cycle.

Versioning scheme: CalVer-inspired SemVer  MAJOR.MINOR.PATCHbN
  MAJOR  — breaking API changes
  MINOR  — new features, backwards-compatible
  PATCH  — bug fixes, security patches
  bN     — beta pre-release (removed on stable release)

Release names follow a pirate theme — each release gets a unique moniker
from the golden age of piracy. Names are human-friendly aliases for the
numeric version and appear in CLI banners, docs, and metadata.
"""

#: Framework version — single source of truth.
__version__: str = "1.3.3"

#: Version tuple for programmatic comparison.
VERSION: tuple[int, int, int] = (1, 3, 3)

#: Human-friendly release name (pirate-themed).
RELEASE_NAME: str = "Ironclad Anchor"

#: Workspace scaffold version — intentionally frozen at 1.0.0.
#: Generated workspace.py files should never auto-track framework releases.
WORKSPACE_VERSION: str = "1.0.0"
