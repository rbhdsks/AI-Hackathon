from __future__ import annotations

from patient_triage.simulations.run_demo import build_demo_report


def test_complete_demo_report(now):
    report = build_demo_report(now)
    assert report["normal"]["metrics"]["patient_count"] == 20
    assert report["normal"]["metrics"]["critical_missed"] == 0
    assert report["deterioration"]["state"] in {
        "deteriorating",
        "critical_escalation",
    }
    assert report["override"]["position"] == 5
    assert report["override"]["audit_chain_valid"] is True
    assert report["surge"]["mode"] == "surge"
    assert report["model_failure"]["status"] == "fallback"
    assert report["model_failure"]["all_entries_stale"] is True
