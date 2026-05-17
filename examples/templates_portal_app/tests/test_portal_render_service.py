import pytest

from examples.templates_portal_app.modules.portal.services import PortalRenderService


@pytest.mark.asyncio
async def test_template_dashboard_renders_context():
    service = PortalRenderService()
    html = await service.render_dashboard({"name": "Acme", "balance": 1200.5, "alerts": ["Invoice due"]})

    assert "Aquilia Portal - Acme" in html
    assert "$1,200.50" in html
    assert "Invoice due" in html


@pytest.mark.asyncio
async def test_template_streaming_yields_bytes():
    service = PortalRenderService()
    chunks = await service.render_chunks({"name": "Acme", "balance": 1, "alerts": []})
    assert b"Acme" in b"".join(chunks)
