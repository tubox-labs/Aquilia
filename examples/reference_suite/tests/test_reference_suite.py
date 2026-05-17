from __future__ import annotations

import pytest

from examples.reference_suite import run_all


@pytest.mark.asyncio
async def test_reference_suite_runs_all_examples():
    results = await run_all.main()

    assert results["core_config_runtime"]["app_is_ready"] is True
    assert results["dependency_injection"]["formatted_total"] == "USD 12.99"
    assert results["cache_storage_filesystem"]["cache_hit"] is True
    assert results["sqlite_models"]["stock"] == 12
    assert results["i18n_templates_mail"]["mail_status"] == "success"
    assert results["artifacts_signing_versioning"]["artifact_verified"] is True
    assert results["http_patterns_faults"]["pattern_params"]["id"] == 42
