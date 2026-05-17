from __future__ import annotations

from pathlib import Path
from typing import Any

from aquilia.templates import TemplateEngine, TemplateLoader


class PortalRenderService:
    def __init__(self, template_root: str | Path | None = None) -> None:
        root = Path(template_root) if template_root is not None else Path(__file__).resolve().parents[2] / "templates"
        self.engine = TemplateEngine(
            TemplateLoader([str(root)]),
            sandbox=True,
            globals={"product_name": "Aquilia Portal"},
            filters={"currency": lambda value: f"${value:,.2f}"},
        )

    async def render_dashboard(self, account: dict[str, Any]) -> str:
        return await self.engine.render("dashboard.html", {"account": account})

    async def render_chunks(self, account: dict[str, Any]) -> list[bytes]:
        return [chunk async for chunk in self.engine.stream("dashboard.html", {"account": account})]
