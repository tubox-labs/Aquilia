from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from aquilia.config import ConfigLoader
from aquilia.server import AquiliaServer
from aquilia.models.startup_guard import check_db_ready, get_db_state, DatabaseState


def _get_test_server():
    cfg = ConfigLoader()
    cfg.config_data = {
        "debug": True,
        "runtime": {"mode": "test"},
        "database": {
            "url": "sqlite:///test.db",
            "auto_create": True,
            "auto_migrate": False,
        },
        "middleware_chain": [],
        "integrations": {
            "cache": {"enabled": False},
            "sessions": {"enabled": False},
            "auth": {"enabled": False},
            "mail": {"enabled": False},
            "templates": {"enabled": False},
        },
    }
    return AquiliaServer(config=cfg, aquilary_registry=MagicMock())


@pytest.mark.asyncio
async def test_startup_guard_warns_non_fatal_when_db_not_ready(tmp_path):
    """
    If check_db_ready returns False, startup logs a warning and does NOT raise a fatal exception.
    """
    server = _get_test_server()

    with (
        patch("aquilia.models.startup_guard.check_db_ready", return_value=False) as mock_check,
        patch("aquilia.db.engine.configure_database") as mock_conf_db,
    ):
        mock_db = MagicMock()
        mock_db.connect = AsyncMock()
        mock_conf_db.return_value = mock_db

        # Should complete without raising SchemaFault
        await server._register_models()

        mock_check.assert_called_once()
        mock_db.connect.assert_called_once()


@pytest.mark.asyncio
async def test_startup_guard_state_classification():
    """
    Verify get_db_state returns clean state classifications.
    """
    state = get_db_state("sqlite:///nonexistent_file_path.db")
    assert state == DatabaseState.MISSING_DATABASE
