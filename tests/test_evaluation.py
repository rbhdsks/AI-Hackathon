from __future__ import annotations

from patient_triage.domain.enums import (
    AcuityLevel,
    ConfidenceLevel,
    QueueMode,
    QueueState,
)
from patient_triage.domain.queue import QueueEntry, QueueSnapshot
from patient_triage.evaluation.metrics import evaluate_snapshot
from patient_triage.services.ranking import RankingService


def test_empty_evaluation(now):
    snapshot = RankingService().rank([], now=now)
    report = evaluate_snapshot(snapshot, [])
    assert report.patient_count == 0
    assert report.explanation_coverage == 1
    assert report.high_risk_detection_rate is None


def test_evaluation_counts_under_over_and_critical_miss(patient_factory, now):
    patients = [
        patient_factory("SYN-A", expected=AcuityLevel.CRITICAL),
        patient_factory("SYN-B", expected=AcuityLevel.URGENT),
        patient_factory("SYN-C", expected=AcuityLevel.NON_URGENT),
    ]

    def entry(position, patient_id, acuity, reasons):
        return QueueEntry(
            position=position,
            patient_id=patient_id,
            acuity=acuity,
            acuity_label=acuity.label,
            safety_floor=AcuityLevel.NON_URGENT,
            confidence=ConfidenceLevel.LOW
            if patient_id == "SYN-B"
            else ConfidenceLevel.HIGH,
            confidence_score=0.4 if patient_id == "SYN-B" else 1,
            wait_minutes=position * 10,
            state=QueueState.REASSESSMENT_DUE
            if patient_id == "SYN-B"
            else QueueState.STABLE,
            reasons=reasons,
            alerts=["reassessment threshold"] if patient_id == "SYN-B" else [],
            recommended_action="review",
        )

    snapshot = QueueSnapshot(
        generated_at=now,
        mode=QueueMode.NORMAL,
        model_status="ready",
        model_version="test",
        patient_count=3,
        queue_pressure=0.15,
        entries=[
            entry(1, "SYN-A", AcuityLevel.URGENT, ["reason"]),
            entry(2, "SYN-B", AcuityLevel.URGENT, []),
            entry(3, "SYN-C", AcuityLevel.LESS_URGENT, ["reason"]),
        ],
    )
    report = evaluate_snapshot(snapshot, patients)
    assert report.critical_missed == 1
    assert report.under_triage_count == 1
    assert report.over_triage_count == 1
    assert report.low_confidence_count == 1
    assert report.reassessment_alert_count == 1
    assert report.explanation_coverage == 0.6667
    assert report.mean_wait_minutes == 20


def test_unlabelled_patient_is_excluded(patient_factory, now):
    patient = patient_factory(expected=None)
    snapshot = RankingService().rank([patient], now=now)
    assert evaluate_snapshot(snapshot, [patient]).labelled_patient_count == 0
