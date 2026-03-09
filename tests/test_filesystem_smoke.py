"""Smoke tests for aquilia.filesystem — native async file I/O module."""
import asyncio
import os
import shutil
import tempfile

import pytest

from aquilia.filesystem import (
    write_file, read_file, file_exists, delete_file,
    async_open, FileSystem, async_tempfile, async_tempdir,
    stream_read, AsyncPath, file_stat,
)


@pytest.fixture()
def sandbox(tmp_path):
    return tmp_path


@pytest.mark.asyncio
async def test_write_and_read_file(sandbox):
    p = sandbox / "test.txt"
    n = await write_file(str(p), "Hello Aquilia", sandbox=str(sandbox))
    assert n == len("Hello Aquilia".encode())
    content = await read_file(str(p), encoding="utf-8", sandbox=str(sandbox))
    assert content == "Hello Aquilia"


@pytest.mark.asyncio
async def test_file_exists_and_stat(sandbox):
    p = sandbox / "stat.txt"
    await write_file(str(p), "data", sandbox=str(sandbox))
    assert await file_exists(str(p), sandbox=str(sandbox))
    st = await file_stat(str(p), sandbox=str(sandbox))
    assert st.size == 4
    assert st.is_file


@pytest.mark.asyncio
async def test_async_open(sandbox):
    p = sandbox / "open.txt"
    await write_file(str(p), "content", sandbox=str(sandbox))
    async with async_open(str(p), "r", encoding="utf-8", sandbox=str(sandbox)) as f:
        data = await f.read()
    assert data == "content"


@pytest.mark.asyncio
async def test_stream_read(sandbox):
    p = sandbox / "stream.txt"
    await write_file(str(p), b"Hello Aquilia", sandbox=str(sandbox))
    chunks = []
    async for c in stream_read(str(p), chunk_size=5, sandbox=str(sandbox)):
        chunks.append(c)
    assert b"".join(chunks) == b"Hello Aquilia"


@pytest.mark.asyncio
async def test_async_tempfile(sandbox):
    async with async_tempfile(dir=str(sandbox)) as tmp:
        await tmp.write(b"temp data")
        await tmp.flush()
        tname = tmp.name
    assert not os.path.exists(tname)


@pytest.mark.asyncio
async def test_async_tempdir(sandbox):
    async with async_tempdir(dir=str(sandbox)) as tmpdir:
        f2 = tmpdir / "inner.txt"
        await f2.write_text("inside")
        assert await f2.read_text() == "inside"


@pytest.mark.asyncio
async def test_async_path(sandbox):
    p = sandbox / "path.txt"
    await write_file(str(p), "via path", sandbox=str(sandbox))
    ap = AsyncPath(str(p))
    assert await ap.exists()
    assert (await ap.read_text()) == "via path"


@pytest.mark.asyncio
async def test_delete_file(sandbox):
    p = sandbox / "del.txt"
    await write_file(str(p), "bye", sandbox=str(sandbox))
    assert await delete_file(str(p), sandbox=str(sandbox))
    assert not await file_exists(str(p), sandbox=str(sandbox))


@pytest.mark.asyncio
async def test_filesystem_service(sandbox):
    fs = FileSystem()
    await fs.initialize()
    p = sandbox / "svc.txt"
    await fs.write_file(str(p), b"service-test", sandbox=str(sandbox))
    result = await fs.read_file(str(p), sandbox=str(sandbox))
    assert result == b"service-test"
    health = await fs.health_check()
    assert health["status"] == "healthy"
    await fs.shutdown()
