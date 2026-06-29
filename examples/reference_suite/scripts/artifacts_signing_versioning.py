from __future__ import annotations

from types import SimpleNamespace

from aquilia.artifacts import ArtifactBuilder, ArtifactReader, MemoryArtifactStore
from aquilia.signing import Signer
from aquilia.signing import dumps as signing_dumps
from aquilia.signing import loads as signing_loads
from aquilia.versioning import ApiVersion, HeaderResolver, URLPathResolver


async def run() -> dict:
    artifact = (
        ArtifactBuilder("catalog-routes", kind="route", version="1.0.0")
        .set_payload({"routes": [{"method": "GET", "path": "/catalog/products"}]})
        .tag("env", "test")
        .set_metadata(owner="platform")
        .build()
    )
    store = MemoryArtifactStore()
    digest = store.save(artifact)
    reader = ArtifactReader(store)
    loaded = reader.load_or_fail("catalog-routes", version="1.0.0")

    secret = "reference-suite-secret-key-32-bytes-minimum"
    signer = Signer(secret=secret, salt="examples")
    signed_value = signer.sign("deploy")
    structured_token = signing_dumps({"artifact": loaded.name, "digest": digest}, secret=secret, salt="examples")
    structured_payload = signing_loads(structured_token, secret=secret, salt="examples")

    header_request = SimpleNamespace(headers={"x-api-version": "2.1"}, path="/catalog/products")
    path_request = SimpleNamespace(headers={}, path="/v2/catalog/products")
    return {
        "artifact_verified": reader.verify(loaded),
        "artifact_names": reader.names(),
        "unsigned": signer.unsign(signed_value),
        "signed_digest": structured_payload["digest"],
        "version": ApiVersion.parse("v2.1").to_dict()["display"],
        "header_version": HeaderResolver().resolve(header_request),
        "path_version": URLPathResolver().resolve(path_request),
    }
