from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from aquilia.config import ConfigLoader
from aquilia.faults.domains import SchemaFault
from aquilia.server import AquiliaServer


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
async def test_startup_guard_fails_when_db_not_ready_and_migrations_exist(tmp_path):
    """
    If check_db_ready returns False and migrations exist, server.startup()
    should raise SchemaFault.
    """
    server = _get_test_server()

    # Mock check_db_ready to return False
    with patch("aquilia.models.startup_guard.check_db_ready", return_value=False), \
         patch("pathlib.Path.exists", return_value=True), \
         patch("pathlib.Path.glob", return_value=[Path("0001_initial.py")]):

        with pytest.raises(SchemaFault) as exc_info:
            # We bypass full ASGI startup and just invoke the _register_models sequence
            with patch.object(server, "logger") as mock_logger:
                # We expect the SchemaFault to bubble up
                await server._register_models()

        assert "[SCHEMA_FAULT]" in str(exc_info.value)
        assert "Database is not ready" in exc_info.value.message


@pytest.mark.asyncio
async def test_startup_guard_proceeds_when_db_not_ready_but_no_migrations(tmp_path):
    """
    If check_db_ready returns False but NO migrations exist, and auto_create is True,
    the startup should proceed (to allow auto-creation on first boot).
    """
    server = _get_test_server()

    # Mock check_db_ready to return False, but glob returns nothing
    with patch("aquilia.models.startup_guard.check_db_ready", return_value=False), \
         patch("pathlib.Path.exists", return_value=True), \
         patch("pathlib.Path.glob", return_value=[]), \
         patch("aquilia.db.engine.configure_database") as mock_conf_db, \
         patch("aquilia.models.base.ModelRegistry.create_tables") as mock_create_tables:

        mock_db = MagicMock()
        mock_db.connect = AsyncMock()
        mock_conf_db.return_value = mock_db

        await server._register_models()

        # Should configure database, connect, and call create_tables
        mock_conf_db.assert_called_once_with("sqlite:///test.db")
        mock_db.connect.assert_called_once()
        mock_create_tables.assert_called_once()
