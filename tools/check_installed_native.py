"""Verify a cibuildwheel test environment imports the installed native wheel."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _outside_checkout() -> None:
    """Prevent the source tree from shadowing the wheel under test."""
    os.chdir(tempfile.mkdtemp(prefix="aquilia-wheel-test-"))
    clean_path: list[str] = []
    for entry in sys.path:
        if not entry:
            continue
        try:
            if Path(entry).resolve() == PROJECT_ROOT:
                continue
        except OSError:
            pass
        clean_path.append(entry)
    sys.path[:] = clean_path


def main() -> None:
    _outside_checkout()

    import aquilia
    from aquilia._core_loader import NATIVE, engine_info
    from aquilia._dataengine_loader import DATAENGINE_NATIVE, dataengine_info
    from aquilia.json import native as JSON_NATIVE

    status = (NATIVE, DATAENGINE_NATIVE, JSON_NATIVE)
    assert all(status), {
        "native": status,
        "core": engine_info(),
        "dataengine": dataengine_info(),
        "package": str(Path(aquilia.__file__).resolve()),
    }
    print(f"installed native wheel verified: {aquilia.__file__}")


if __name__ == "__main__":
    main()
