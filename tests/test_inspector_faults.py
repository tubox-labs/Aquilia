from aquilia.inspector.faults import (
    INSPECTOR_DOMAIN,
    InspectorConfigFault,
    InspectorReplayFault,
)


def test_inspector_faults():
    f1 = InspectorConfigFault("CONFIG_ERROR", "bad config value")
    assert f1.domain == INSPECTOR_DOMAIN
    assert f1.code == "CONFIG_ERROR"
    assert f1.message == "bad config value"

    f2 = InspectorReplayFault("REPLAY_ERROR", "replay failed")
    assert f2.domain == INSPECTOR_DOMAIN
    assert f2.code == "REPLAY_ERROR"
    assert f2.message == "replay failed"
