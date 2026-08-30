from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

from patient_triage.simulations.generate_reports import main


def test_generate_reports_creates_evidence_files(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """The report command should create all expected evidence files."""

    # generate_reports.py expects to run from the project root because
    # the hospital configuration is stored under configs/.
    project_root = Path(__file__).resolve().parents[1]
    monkeypatch.chdir(project_root)

    # Simulate the command:
    # patient-triage-reports --output <temporary-directory>
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "patient-triage-reports",
            "--output",
            str(tmp_path),
        ],
    )

    main()

    expected_files = {
        "baseline_benchmark.csv",
        "baseline_benchmark.json",
        "scalability_benchmark.csv",
        "scalability_benchmark.json",
    }

    generated_files = {
        path.name
        for path in tmp_path.iterdir()
        if path.is_file()
    }

    assert generated_files == expected_files

    # Confirm that two scenarios and six strategies produced 12 rows.
    with (tmp_path / "baseline_benchmark.csv").open(
        newline="",
        encoding="utf-8",
    ) as handle:
        baseline_rows = list(csv.DictReader(handle))

    assert len(baseline_rows) == 12

    assert {
        row["scenario"]
        for row in baseline_rows
    } == {"normal", "surge"}

    assert {
        row["strategy"]
        for row in baseline_rows
    } == {
        "fcfs",
        "acuity_priority",
        "sjf_like",
        "waiting_time_priority",
        "acuity_plus_waiting",
        "patienttriage_ai",
    }

    # Confirm the expected scalability queue sizes.
    scalability_report = json.loads(
        (
            tmp_path / "scalability_benchmark.json"
        ).read_text(encoding="utf-8")
    )

    assert [
        point["patient_count"]
        for point in scalability_report["points"]
    ] == [20, 60, 180]