from examples.artifacts_release_app.modules.releases.services import ReleaseArtifactService


def test_release_artifact_is_signed_and_inspectable():
    service = ReleaseArtifactService()
    release = service.create_release("web-config", "1.0.0", {"environment": "staging", "replicas": 2})
    inspected = service.inspect_release("web-config", release["token"])

    assert release["verified"] is True
    assert inspected["qualified_name"] == "web-config:1.0.0"
    assert inspected["tags"]["environment"] == "staging"


def test_release_promotion_preserves_provenance_chain():
    service = ReleaseArtifactService()
    release = service.create_release("web-config", "1.0.0", {"environment": "staging"})
    promoted = service.promote("web-config", "1.0.0", "1.0.1", "production")

    assert promoted["derived_from"] == release["digest"]
    assert promoted["environment"] == "production"
