from __future__ import annotations

from pathlib import Path
from typing import Any

APP_ROOT = Path(__file__).resolve().parent
ASSETS_DIR = APP_ROOT / "assets"
SAMPLE_TEXT_PATH = ASSETS_DIR / "sample.txt"


def build_large_payload(records: int = 800) -> dict[str, Any]:
    """Create a deterministic, non-trivial JSON payload for serializer tests."""
    items: list[dict[str, Any]] = []
    for idx in range(records):
        items.append(
            {
                "id": idx,
                "name": f"record-{idx}",
                "active": idx % 2 == 0,
                "score": round((idx * 1.618) % 100, 4),
                "tags": [f"tag-{idx % 11}", f"group-{idx % 7}", "benchmark"],
                "metadata": {
                    "owner": f"user-{idx % 37}",
                    "region": ["us-east", "us-west", "eu-west", "ap-south"][idx % 4],
                    "flags": {
                        "cacheable": idx % 3 == 0,
                        "audited": idx % 5 == 0,
                        "compress": idx % 2 == 1,
                    },
                },
            }
        )

    return {
        "ok": True,
        "dataset": "large-json-payload",
        "version": 1,
        "items": items,
    }


LARGE_PAYLOAD = build_large_payload()


def build_stream_chunk(index: int, size: int = 1024) -> bytes:
    """Build deterministic stream chunks to avoid per-request randomization noise."""
    prefix = f"chunk-{index:03d}:".encode()
    pad = b"x" * max(0, size - len(prefix))
    return prefix + pad
