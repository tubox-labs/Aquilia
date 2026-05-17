from __future__ import annotations

from dataclasses import dataclass

from aquilia.versioning import ApiVersion, VersionConfig, VersionStrategy


@dataclass(slots=True)
class FakeRequest:
    path: str = "/public/catalog"
    headers: dict[str, str] | None = None


class PublicCatalogService:
    def __init__(self) -> None:
        self.strategy = VersionStrategy(
            VersionConfig(
                strategy="header",
                versions=["1.0", "2.0"],
                default_version="1.0",
                header_name="X-API-Version",
                negotiation_mode="exact",
            )
        )

    def resolve_version(self, header_value: str | None = None, path: str = "/public/catalog") -> ApiVersion:
        headers = {"x-api-version": header_value} if header_value else {}
        return self.strategy.resolve(FakeRequest(path=path, headers=headers))

    def catalog_payload(self, header_value: str | None = None) -> dict:
        version = self.resolve_version(header_value)
        label = f"v{version.major}.{version.minor}"
        if version == "2.0":
            return {"version": label, "items": [{"sku": "sku-1", "name": "Desk", "inventory": {"available": 12}}]}
        return {"version": label, "items": [{"sku": "sku-1", "name": "Desk"}]}
