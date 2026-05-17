from __future__ import annotations

import asyncio
import json

from examples.reference_suite.scripts import (
    artifacts_signing_versioning,
    cache_storage_filesystem,
    core_config_runtime,
    dependency_injection,
    http_patterns_faults,
    i18n_templates_mail,
    sqlite_models,
)


async def main() -> dict[str, dict]:
    results = {}
    for module in (
        core_config_runtime,
        dependency_injection,
        cache_storage_filesystem,
        sqlite_models,
        i18n_templates_mail,
        artifacts_signing_versioning,
        http_patterns_faults,
    ):
        results[module.__name__.rsplit(".", 1)[-1]] = await module.run()
    return results


if __name__ == "__main__":
    print(json.dumps(asyncio.run(main()), indent=2, sort_keys=True, default=str))
