"""Generate reproducible baseline and scalability evidence files."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import UTC, datetime
from pathlib import Path

from patient_triage.data.generator import generate_scenario
from patient_triage.domain.hospital import load_hospital_profile
from patient_triage.evaluation.baselines import compare_baselines
from patient_triage.evaluation.scalability import benchmark_scalability
from patient_triage.services.ranking import RankingService


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def generate(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    benchmark_clock = datetime(2026, 8, 25, 12, 0, tzinfo=UTC)
    profile = load_hospital_profile(Path("configs/district_hospital.json"))
    ranker = RankingService()
    baseline_payload: dict[str, object] = {
        "generated_at": datetime.now(UTC).isoformat(),
        "benchmark_clock": benchmark_clock.isoformat(),
        "profile_id": profile.profile_id,
        "scenarios": {},
    }
    baseline_rows: list[dict[str, object]] = []
    for scenario in ("normal", "surge"):
        patients = generate_scenario(scenario, benchmark_clock)
        snapshot = ranker.rank(patients, now=benchmark_clock)
        report = compare_baselines(patients, snapshot, profile)
        baseline_payload["scenarios"][scenario] = report.model_dump(mode="json")
        baseline_rows.extend(
            {"scenario": scenario, **result.model_dump(mode="json")}
            for result in report.results
        )
    (output_dir / "baseline_benchmark.json").write_text(
        json.dumps(baseline_payload, indent=2), encoding="utf-8"
    )
    _write_csv(output_dir / "baseline_benchmark.csv", baseline_rows)

    templates = generate_scenario("surge", benchmark_clock)
    scalability = benchmark_scalability(templates, now=benchmark_clock)
    (output_dir / "scalability_benchmark.json").write_text(
        scalability.model_dump_json(indent=2), encoding="utf-8"
    )
    _write_csv(
        output_dir / "scalability_benchmark.csv",
        [point.model_dump(mode="json") for point in scalability.points],
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("reports"))
    args = parser.parse_args()
    generate(args.output)


if __name__ == "__main__":
    main()
