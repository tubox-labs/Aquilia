"""
aquilia.devplatform.profiler.flamegraph — Speedscope JSON formatter.

Converts cProfile pstats output into speedscope-compatible JSON for
interactive flamegraph visualization. Not yet wired into a serving
endpoint — Inspector's web dashboard (aquilia/inspector/) is the natural
consumer once request-scoped profile data needs a flamegraph view.

Speedscope format: https://github.com/jlfwong/speedscope/wiki/Importing-from-custom-sources
"""

from __future__ import annotations

import io
import json
import pstats
from typing import Any


def _parse_pstats(profile_stats_text: str) -> list[dict[str, Any]]:
    """
    Parse cProfile text output into a list of call records.
    Returns list of {func, ncalls, cumtime, tottime, callers}.
    """
    records: list[dict[str, Any]] = []
    lines = profile_stats_text.splitlines()
    in_data = False

    for line in lines:
        line = line.strip()
        if line.startswith("ncalls") or line.startswith("tottime"):
            in_data = True
            continue
        if not in_data or not line:
            continue

        parts = line.split(None, 5)
        if len(parts) < 6:
            continue
        try:
            records.append(
                {
                    "ncalls": parts[0],
                    "tottime": float(parts[1]),
                    "percall_tot": float(parts[2]),
                    "cumtime": float(parts[3]),
                    "percall_cum": float(parts[4]),
                    "func": parts[5].strip(),
                }
            )
        except (ValueError, IndexError):
            continue

    return records


class FlamegraphFormatter:
    """
    Converts cProfile output to Speedscope JSON format.

    Usage::

        formatter = FlamegraphFormatter()
        json_str = formatter.format(profile_stats_text, trace_id="abc123")
    """

    def format(self, profile_stats_text: str, trace_id: str = "") -> str:
        """Return Speedscope-compatible JSON string."""
        records = _parse_pstats(profile_stats_text)

        # Build frames list
        frames = []
        frame_index: dict[str, int] = {}
        for rec in records:
            func_name = rec["func"]
            if func_name not in frame_index:
                frame_index[func_name] = len(frames)
                frames.append({"name": func_name})

        # Build a flat "sampled" profile from cumulative times
        # (approximation — cProfile is deterministic, not sampling)
        samples: list[list[int]] = []
        weights: list[float] = []

        for rec in records:
            frame_idx = frame_index.get(rec["func"])
            if frame_idx is not None and rec["tottime"] > 0:
                samples.append([frame_idx])
                weights.append(rec["tottime"] * 1_000_000)  # to microseconds

        speedscope_doc: dict[str, Any] = {
            "$schema": "https://www.speedscope.app/file-format-schema.json",
            "version": "0.0.1",
            "shared": {"frames": frames},
            "profiles": [
                {
                    "type": "sampled",
                    "name": f"Aquilia request {trace_id}",
                    "unit": "microseconds",
                    "startValue": 0,
                    "endValue": sum(weights),
                    "samples": samples,
                    "weights": weights,
                }
            ],
            "activeProfileIndex": 0,
            "exporter": "aquilia.devplatform",
        }

        return json.dumps(speedscope_doc)

    def format_from_profile(self, profile: Any, trace_id: str = "") -> str:
        """Format directly from a cProfile.Profile object."""
        stream = io.StringIO()
        stats = pstats.Stats(profile, stream=stream)
        stats.sort_stats("cumulative")
        stats.print_stats(100)
        return self.format(stream.getvalue(), trace_id=trace_id)
