from __future__ import annotations

from dataclasses import dataclass

from aquilia.di import ClassProvider, Container, ValueProvider


@dataclass(frozen=True)
class BillingSettings:
    currency: str


class InvoiceFormatter:
    def __init__(self, settings: BillingSettings):
        self.settings = settings

    def format_total(self, cents: int) -> str:
        return f"{self.settings.currency} {cents / 100:.2f}"


async def run() -> dict:
    container = Container(scope="app")
    container.register(ValueProvider(BillingSettings(currency="USD"), token=BillingSettings, scope="app"))
    container.register(ClassProvider(InvoiceFormatter, scope="request"))

    request_scope = container.create_request_scope()
    formatter = await request_scope.resolve_async(InvoiceFormatter)
    total = formatter.format_total(1299)
    await request_scope.shutdown()
    await container.shutdown()
    return {"formatted_total": total, "scope": "request"}
