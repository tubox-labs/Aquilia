"""Example corpus loader."""

from __future__ import annotations

from ..models import SourceFile


def example_mappings(sources: list[SourceFile]) -> list[dict[str, object]]:
    examples: dict[str, dict[str, object]] = {}
    for source in sources:
        if not source.path.startswith("examples/"):
            continue
        parts = source.path.split("/")
        if len(parts) < 2:
            continue
        name = parts[1]
        item = examples.setdefault(name, {"name": name, "paths": [], "features": set()})
        item["paths"].append(source.path)
        text = (source.path + " " + source.summary + " " + " ".join(source.symbols)).lower()
        features = item["features"]
        assert isinstance(features, set)
        for keyword in (
            "admin",
            "artifacts",
            "auth",
            "blueprint",
            "cache",
            "crud",
            "i18n",
            "mail",
            "sqlite",
            "storage",
            "tasks",
            "templates",
            "versioning",
            "websocket",
        ):
            if keyword in text:
                features.add(keyword)
    result = []
    for item in examples.values():
        features = item.pop("features")
        assert isinstance(features, set)
        item["features"] = sorted(features)
        result.append(item)
    return sorted(result, key=lambda item: str(item["name"]))
