import pytest

from examples.storage_filehub_app.modules.files.services import FileHubService, build_ephemeral_backend


@pytest.mark.asyncio
async def test_filehub_stores_metadata_and_reads_bytes():
    service = FileHubService()
    await service.startup()
    meta = await service.upload_document("contract.txt", b"terms", tenant="acme")
    body = await service.download(meta["name"])
    inventory = await service.inventory()
    await service.shutdown()

    assert body == b"terms"
    assert meta["metadata"]["tenant"] == "acme"
    assert "acme" in inventory["dirs"]
    assert inventory["health"]["documents"] is True


def test_ephemeral_backend_factory_uses_real_memory_storage():
    backend = build_ephemeral_backend()
    assert backend.backend_name == "memory"
