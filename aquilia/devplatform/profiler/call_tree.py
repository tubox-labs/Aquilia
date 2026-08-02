"""
aquilia.devplatform.profiler.call_tree — Terminal call-tree printer.

Converts cProfile pstats into a rich.Tree for plain-text terminal output.
"""

from __future__ import annotations

import io
import pstats
from typing import Any


class CallTreePrinter:
    """
    Converts cProfile output to a hierarchical text tree.

    Delegates to rich.Tree if available; falls back to plain indented text.
    """

    def __init__(self, max_entries: int = 30) -> None:
        self._max_entries = max_entries

    def print_text(self, profile_stats_text: str) -> str:
        """Return indented ASCII call-tree text from pstats text output."""
        lines = []
        in_data = False
        count = 0

        for line in profile_stats_text.splitlines():
            stripped = line.strip()
            if stripped.startswith("ncalls") or stripped.startswith("tottime"):
                in_data = True
                lines.append(f"{'ncalls':>10} {'tottime':>10} {'cumtime':>10}  function")
                lines.append("-" * 60)
                continue
            if not in_data or not stripped:
                continue
            parts = stripped.split(None, 5)
            if len(parts) < 6:
                continue
            try:
                ncalls = parts[0]
                tottime = float(parts[1])
                cumtime = float(parts[3])
                func = parts[5].strip()
                lines.append(f"{ncalls:>10} {tottime:>10.4f} {cumtime:>10.4f}  {func}")
                count += 1
                if count >= self._max_entries:
                    lines.append(f"  … ({self._max_entries} entries shown)")
                    break
            except (ValueError, IndexError):
                continue

        return "\n".join(lines)

    def build_rich_tree(self, profile_stats_text: str) -> Any:
        """Return a rich.Tree object if rich is installed, else None."""
        try:
            from rich.tree import Tree

            root = Tree("[bold cyan]Call Profile[/bold cyan]")
            in_data = False
            count = 0

            for line in profile_stats_text.splitlines():
                stripped = line.strip()
                if stripped.startswith("ncalls"):
                    in_data = True
                    continue
                if not in_data or not stripped:
                    continue
                parts = stripped.split(None, 5)
                if len(parts) < 6:
                    continue
                try:
                    ncalls = parts[0]
                    cumtime = float(parts[3])
                    func = parts[5].strip()
                    color = "green" if cumtime < 0.01 else "yellow" if cumtime < 0.1 else "red"
                    root.add(f"[{color}]{func}[/{color}] ncalls={ncalls} cum={cumtime:.4f}s")
                    count += 1
                    if count >= self._max_entries:
                        root.add("[dim]… more entries omitted[/dim]")
                        break
                except (ValueError, IndexError):
                    continue

            return root
        except ImportError:
            return None

    def format_from_profile(self, profile: Any) -> str:
        """Format directly from a cProfile.Profile object."""
        stream = io.StringIO()
        stats = pstats.Stats(profile, stream=stream)
        stats.sort_stats("cumulative")
        stats.print_stats(self._max_entries)
        return self.print_text(stream.getvalue())
