from __future__ import annotations

from types import SimpleNamespace

import pytest

from aquilia.response import HLSManifestError, HLSSegment, HLSVariant, MediaChunk, Response


async def test_media_stream_async_chunks_are_encoded():
    async def _chunks():
        yield MediaChunk(data=b"aa")
        yield MediaChunk(data="bb")

    resp = Response.media_stream(_chunks(), media_type="video/mp2t")

    messages = []

    async def _send(msg):
        messages.append(msg)

    await resp.send_asgi(_send)

    body = b"".join(m.get("body", b"") for m in messages if m["type"] == "http.response.body")
    assert body == b"aabb"


def test_hls_playlist_renders_expected_lines():
    resp = Response.hls_playlist(
        [
            HLSSegment(uri="seg-000.ts", duration=4.0),
            HLSSegment(uri="seg-001.ts", duration=4.5, title="next"),
        ],
        media_sequence=10,
    )

    assert resp.headers["content-type"] == "application/vnd.apple.mpegurl; charset=utf-8"
    body = resp._encode_body(resp._content).decode("utf-8")
    assert "#EXTM3U" in body
    assert "#EXT-X-MEDIA-SEQUENCE:10" in body
    assert "#EXTINF:4.500,next" in body
    assert "#EXT-X-ENDLIST" in body


def test_hls_master_playlist_renders_variants():
    resp = Response.hls_master_playlist(
        [
            HLSVariant(uri="low/index.m3u8", bandwidth=250000, resolution="640x360"),
            HLSVariant(uri="high/index.m3u8", bandwidth=1200000, resolution="1920x1080", codecs="avc1.4d401f"),
        ]
    )

    body = resp._encode_body(resp._content).decode("utf-8")
    assert "#EXT-X-STREAM-INF:BANDWIDTH=250000,RESOLUTION=640x360" in body
    assert "#EXT-X-STREAM-INF:BANDWIDTH=1200000,RESOLUTION=1920x1080,CODECS=\"avc1.4d401f\"" in body


def test_hls_master_playlist_requires_variants():
    with pytest.raises(HLSManifestError):
        Response.hls_master_playlist([])


async def test_hls_segment_uses_media_type_and_range(tmp_path):
    seg = tmp_path / "clip.ts"
    seg.write_bytes(b"0123456789")

    resp = Response.hls_segment(str(seg))
    assert resp.headers["content-type"] == "video/mp2t"

    request = SimpleNamespace(headers={"range": "bytes=1-3"})
    messages = []

    async def _send(msg):
        messages.append(msg)

    await resp.send_asgi(_send, request)

    start = messages[0]
    assert start["status"] == 206
    body = b"".join(m.get("body", b"") for m in messages if m["type"] == "http.response.body")
    assert body == b"123"
