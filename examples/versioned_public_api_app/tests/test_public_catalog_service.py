from examples.versioned_public_api_app.modules.publicapi.controllers import PublicCatalogController
from examples.versioned_public_api_app.modules.publicapi.services import PublicCatalogService


def test_header_version_changes_payload_shape():
    service = PublicCatalogService()

    v1 = service.catalog_payload()
    v2 = service.catalog_payload("2.0")

    assert v1["version"] == "v1.0"
    assert "inventory" not in v1["items"][0]
    assert v2["version"] == "v2.0"
    assert v2["items"][0]["inventory"]["available"] == 12


def test_controller_methods_have_version_metadata():
    metadata = PublicCatalogController.catalog.__version_metadata__
    assert metadata["versions"] == ["1.0", "2.0"]
    assert PublicCatalogController.health.__version_metadata__["neutral"] is True
