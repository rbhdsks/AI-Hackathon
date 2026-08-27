"""Create a stable, synthetic 18-bed emergency-department projection."""

from __future__ import annotations

from patient_triage.domain.enums import BedStatus
from patient_triage.domain.hospital import HospitalProfile
from patient_triage.domain.operations import BedBoard, BedSlot, WaitingForBed
from patient_triage.domain.queue import QueueEntry, QueueSnapshot


def _zone_labels(profile: HospitalProfile) -> list[str]:
    labels: list[str] = []
    for zone in profile.zones:
        labels.extend([zone.name] * zone.bed_count)
    return labels


def build_bed_board(
    snapshot: QueueSnapshot,
    profile: HospitalProfile,
) -> BedBoard:
    """Project queue patients onto care spaces without claiming bed-master authority."""

    stable_entries = sorted(snapshot.entries, key=lambda item: item.patient_id)
    assigned = stable_entries[: profile.ed_beds]
    waiting = sorted(
        stable_entries[profile.ed_beds :],
        key=lambda item: item.position,
    )
    entry_by_bed = {index: entry for index, entry in enumerate(assigned)}
    beds: list[BedSlot] = []
    for index, zone in enumerate(_zone_labels(profile)):
        entry: QueueEntry | None = entry_by_bed.get(index)
        if entry is None:
            beds.append(
                BedSlot(
                    bed_id=f"ED-{index + 1:02d}",
                    zone=zone,
                    status=BedStatus.EMPTY,
                )
            )
        else:
            beds.append(
                BedSlot(
                    bed_id=f"ED-{index + 1:02d}",
                    zone=zone,
                    status=BedStatus.OCCUPIED,
                    patient_id=entry.patient_id,
                    queue_position=entry.position,
                    acuity_label=entry.acuity_label,
                    wait_minutes=entry.wait_minutes,
                    state=entry.state.value,
                )
            )
    occupied = len(assigned)
    return BedBoard(
        generated_at=snapshot.generated_at,
        profile_id=profile.profile_id,
        total_beds=profile.ed_beds,
        occupied_beds=occupied,
        empty_beds=profile.ed_beds - occupied,
        waiting_for_bed=len(waiting),
        occupancy_percent=round(100 * occupied / profile.ed_beds, 1),
        beds=beds,
        waiting_patients=[
            WaitingForBed(
                patient_id=entry.patient_id,
                queue_position=entry.position,
                acuity_label=entry.acuity_label,
                wait_minutes=entry.wait_minutes,
                state=entry.state.value,
            )
            for entry in waiting
        ],
        projection_notice=(
            "Synthetic operational projection only; this is not a source-of-truth "
            "bed-management or hospital ERP module."
        ),
    )
