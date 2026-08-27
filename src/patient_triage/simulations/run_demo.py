"""Generate a complete normal, deterioration, surge, and failure demo report."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from patient_triage.config import Settings
from patient_triage.data.generator import (
    deteriorated_vitals,
    generate_normal_scenario,
    generate_surge_scenario,
)
from patient_triage.data.repository import InMemoryPatientRepository
from patient_triage.domain.queue import OverrideRequest
from patient_triage.evaluation.metrics import evaluate_snapshot
from patient_triage.services.triage import TriageService
from patient_triage.storage.sqlite_audit import SQLiteAuditStore


def build_demo_report(now: datetime) -> dict[str, object]:
    settings = Settings(
        database_path=Path(":memory:"),
        bootstrap_demo_data=False,
    )
    audit_store = SQLiteAuditStore(settings.database_path)
    service = TriageService(
        settings=settings,
        repository=InMemoryPatientRepository(),
        audit_store=audit_store,
    )
    try:
        normal = generate_normal_scenario(now)
        service.load_scenario(normal, scenario_name="normal")
        initial = service.rank_queue(now=now)

        target = service.repository.get("SYN-015")
        service.update_vitals(
            target.patient_id,
            deteriorated_vitals(target, now),
            now=now,
        )
        after_deterioration = service.rank_queue(now=now)

        overridden = service.override_queue(
            OverrideRequest(
                patient_id="SYN-011",
                target_position=5,
                clinician_id="demo_nurse_01",
                reason="Ambiguous symptoms require earlier face-to-face reassessment",
            ),
            now=now,
        )

        surge = generate_surge_scenario(now)
        service.load_scenario(surge, scenario_name="surge")
        surge_snapshot = service.rank_queue(now=now)
        failure_snapshot = service.rank_queue(now=now, simulate_model_failure=True)

        return {
            "generated_at": now.isoformat(),
            "prototype_warning": "Synthetic demonstration only; not for clinical use.",
            "normal": {
                "metrics": evaluate_snapshot(initial, normal).model_dump(mode="json"),
                "top_five": [
                    entry.model_dump(mode="json") for entry in initial.entries[:5]
                ],
            },
            "deterioration": {
                "patient_id": "SYN-015",
                "new_position": next(
                    entry.position
                    for entry in after_deterioration.entries
                    if entry.patient_id == "SYN-015"
                ),
                "state": next(
                    entry.state.value
                    for entry in after_deterioration.entries
                    if entry.patient_id == "SYN-015"
                ),
            },
            "override": {
                "patient_id": "SYN-011",
                "position": next(
                    entry.position
                    for entry in overridden.entries
                    if entry.patient_id == "SYN-011"
                ),
                "audit_chain_valid": audit_store.verify_chain(),
            },
            "surge": {
                "metrics": evaluate_snapshot(surge_snapshot, surge).model_dump(
                    mode="json"
                ),
                "mode": surge_snapshot.mode.value,
                "queue_pressure": surge_snapshot.queue_pressure,
            },
            "model_failure": {
                "status": failure_snapshot.model_status,
                "warnings": failure_snapshot.warnings,
                "all_entries_stale": all(
                    entry.is_stale for entry in failure_snapshot.entries
                ),
            },
        }
    finally:
        audit_store.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Optional JSON output path")
    arguments = parser.parse_args()
    report = build_demo_report(datetime.now(UTC))
    rendered = json.dumps(report, indent=2)
    if arguments.output:
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        arguments.output.write_text(rendered + "\n", encoding="utf-8")
        print(f"Wrote demo report to {arguments.output}")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
