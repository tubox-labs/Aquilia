"""``AqContext`` -- the object threaded through commands and checks.

Replaces ad-hoc ``ctx.obj`` dictionary access and the three competing
workspace-guard mechanisms (``_ensure_workspace_root``, ``_require_workspace``,
raw ``ConfigMissingFault``) with one lazily-loaded value.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from aquilia.cli.core.faults import WorkspaceNotFoundFault
from aquilia.cli.core.workspace import LoadedWorkspace, load_workspace

__all__ = ["AqContext"]


@dataclass
class AqContext:
    """Ambient CLI state.

    The workspace is loaded on first access, so commands that do not need one
    (``aq init``, ``aq --help``) never pay for it.
    """

    cwd: Path = field(default_factory=Path.cwd)
    verbose: bool = False
    quiet: bool = False
    json_output: bool = False
    no_color: bool = False
    strict: bool = False
    module_filter: str | None = None
    mode: str = field(default_factory=lambda: os.environ.get("AQUILIA_ENV", "dev"))
    _workspace: LoadedWorkspace | None = field(default=None, repr=False)

    @property
    def as_json(self) -> bool:
        """Alias for ``json_output`` -- commands use both spellings."""
        return self.json_output

    @property
    def workspace(self) -> LoadedWorkspace:
        """The loaded workspace (lazily resolved, never raises)."""
        if self._workspace is None:
            self._workspace = load_workspace(self.cwd)
        return self._workspace

    def require_workspace(self) -> LoadedWorkspace:
        """Return the workspace or raise ``WorkspaceNotFoundFault``."""
        ws = self.workspace
        if not ws.exists:
            raise WorkspaceNotFoundFault(path=str(self.cwd))
        return ws

    @property
    def root(self) -> Path:
        return self.workspace.root

    @classmethod
    def from_click(cls, ctx) -> AqContext:
        """Build from a Click context, reusing an existing instance if present."""
        obj = getattr(ctx, "obj", None)
        if isinstance(obj, AqContext):
            return obj
        opts = obj if isinstance(obj, dict) else {}
        instance = cls(
            verbose=bool(opts.get("verbose", False)),
            quiet=bool(opts.get("quiet", False)),
            json_output=bool(opts.get("json", False)),
            no_color=bool(opts.get("no_color", False)),
        )
        if ctx is not None:
            ctx.obj = instance
        return instance
