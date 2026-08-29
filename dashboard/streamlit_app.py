"""Role-specific PatientTriage.ai dashboard for synthetic demonstrations."""

from __future__ import annotations

import os
from typing import Any

import httpx2
import pandas as pd
import streamlit as st

from dashboard.charts import (
    ACUITY_COLORS,
    baseline_chart,
    bed_board_chart,
    occupancy_gauge,
    queue_chart,
)
from dashboard.client import APIClient
from dashboard.theme import (
    AMBER,
    BLUE,
    GRAY,
    ORANGE,
    RED,
    TEAL,
    apply_brand_theme,
    badge_html,
    render_header,
)

st.set_page_config(
    page_title="PatientTriage.ai · Etinimtsal Hospital ED",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_brand_theme()

ROLE_LABELS = {
    "nurse": "Triage nurse",
    "doctor": "Emergency doctor",
    "pharmacy": "Emergency pharmacy",
    "administration": "Hospital administration",
    "blood_bank": "Blood bank",
}

# Queue/monitoring states that mean "this patient needs a human to look now",
# mapped to a short headline and a badge color, ordered most to least severe.
_ATTENTION_STATES: dict[str, tuple[str, str]] = {
    "critical_escalation": ("Critical escalation", RED),
    "deteriorating": ("Deterioration detected", ORANGE),
    "reassessment_due": ("Reassessment overdue", AMBER),
    "stale_information": ("Vitals stale", AMBER),
    "manual_review": ("Manual review needed", BLUE),
}
_ATTENTION_ORDER = {
    "critical_escalation": 0,
    "deteriorating": 1,
    "reassessment_due": 2,
    "stale_information": 2,
    "manual_review": 3,
    "low_confidence": 4,
}
_STATE_LABELS: dict[str, tuple[str, str]] = {
    **_ATTENTION_STATES,
    "stable": ("Stable", TEAL),
}


def _frame(rows: list[dict[str, Any]]) -> pd.DataFrame:
    return pd.DataFrame(rows) if rows else pd.DataFrame()


def _state_badge(state: str) -> str:
    label, color = _STATE_LABELS.get(state, (state.replace("_", " ").title(), GRAY))
    return badge_html(label, color)


def _acuity_badge(acuity_label: str) -> str:
    color = ACUITY_COLORS.get(acuity_label, GRAY)
    return badge_html(acuity_label.replace("_", " ").title(), color)


def _confidence_badge(confidence: str) -> str:
    color = {"low": AMBER, "medium": BLUE, "high": TEAL}.get(confidence, GRAY)
    return badge_html(confidence.title(), color)


def _selected_bed_id(event: Any) -> str | None:
    if event is None:
        return None
    try:
        points = event.selection.points
    except AttributeError:
        points = event.get("selection", {}).get("points", [])
    if not points:
        return None
    customdata = points[0].get("customdata", [])
    return str(customdata[0]) if customdata else None


def _attention_items(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for entry in entries:
        state = entry["state"]
        if state in _ATTENTION_STATES:
            headline, color = _ATTENTION_STATES[state]
            reason_key = state
        elif entry["confidence"] == "low" and entry["missing_information"]:
            headline, color = "Low confidence · missing data", AMBER
            reason_key = "low_confidence"
        else:
            continue
        items.append(
            {
                "patient_id": entry["patient_id"],
                "position": entry["position"],
                "headline": headline,
                "color": color,
                "detail": entry["recommended_action"],
                "order": _ATTENTION_ORDER.get(reason_key, 5),
            }
        )
    items.sort(key=lambda item: (item["order"], item["position"]))
    return items


def _render_attention_panel(entries: list[dict[str, Any]]) -> None:
    items = _attention_items(entries)
    st.subheader("Attention required")
    if not items:
        st.success("No exceptions. All patients are within safe monitoring windows.")
        return
    for item in items:
        st.markdown(
            f"""
            <div class="pt-attention-card">
              <span class="pt-attention-head">#{item['position']} {item['patient_id']}
              &nbsp;{badge_html(item['headline'], item['color'])}</span>
              <div class="pt-attention-sub">Recommended: {item['detail']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _movement_labels(entries: list[dict[str, Any]]) -> dict[str, str]:
    previous = st.session_state.get("prev_positions", {})
    labels: dict[str, str] = {}
    for entry in entries:
        prev = previous.get(entry["patient_id"])
        if prev is not None and prev != entry["position"]:
            arrow = "↑" if entry["position"] < prev else "↓"
            labels[entry["patient_id"]] = f"{arrow} Moved from #{prev}"
    return labels


def _remember_positions(entries: list[dict[str, Any]]) -> None:
    st.session_state["prev_positions"] = {
        entry["patient_id"]: entry["position"] for entry in entries
    }


def _limited_mode_banner(model_status: str, warnings: list[str]) -> None:
    if model_status == "ready" and not warnings:
        return
    st.markdown(
        """
        <div class="pt-limited-mode">
          <b>LIMITED MODE</b> &mdash; Context-based ranking is temporarily unavailable.
          Safety rules and urgency scoring remain active. Affected patients require
          clinician review.
        </div>
        """,
        unsafe_allow_html=True,
    )
    if warnings:
        with st.expander("Details"):
            for warning in warnings:
                st.write(f"- {warning}")


def _render_bed_board(
    client: APIClient,
    *,
    allow_deterioration: bool,
    allow_discharge: bool = False,
    model_failure: bool = False,
    queue_entries: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    board = client.beds(model_failure=model_failure)
    entries_by_patient = {item["patient_id"]: item for item in (queue_entries or [])}
    metrics = st.columns(4)
    metrics[0].metric("Occupied", f"{board['occupied_beds']}/{board['total_beds']}")
    metrics[1].metric("Available", board["empty_beds"])
    metrics[2].metric("Waiting for bed", board["waiting_for_bed"])
    metrics[3].metric("Occupancy", f"{board['occupancy_percent']:.1f}%")
    event = st.plotly_chart(
        bed_board_chart(board["beds"]),
        width="stretch",
        on_select="rerun",
        selection_mode="points",
        key="selectable-bed-board",
    )
    selected_from_chart = _selected_bed_id(event)
    bed_ids = [item["bed_id"] for item in board["beds"]]
    if selected_from_chart in bed_ids:
        st.session_state["selected_bed_id"] = selected_from_chart
    selected_state = st.session_state.get("selected_bed_id", bed_ids[0])
    selected_id = st.selectbox(
        "Bed detail",
        bed_ids,
        index=bed_ids.index(selected_state) if selected_state in bed_ids else 0,
    )
    selected = next(item for item in board["beds"] if item["bed_id"] == selected_id)
    left, right = st.columns([1, 2])
    with left:
        st.subheader(selected["bed_id"])
        st.write(f"**Zone:** {selected['zone']}")
        st.write(f"**Status:** {selected['status'].title()}")
        if selected["patient_id"]:
            st.write(f"**Patient:** {selected['patient_id']}")
            acuity = selected["acuity_label"].replace("_", " ").title()
            st.write(f"**Acuity:** {acuity}")
            st.write(f"**Queue position:** {selected['queue_position']}")
            st.write(f"**Wait:** {selected['wait_minutes']:.0f} min")
            queue_entry = entries_by_patient.get(selected["patient_id"])
            if queue_entry:
                st.markdown(
                    f"**Monitoring state:** {_state_badge(queue_entry['state'])}",
                    unsafe_allow_html=True,
                )
                if queue_entry["reasons"]:
                    st.write(f"**Latest change:** {queue_entry['reasons'][0]}")
                st.write(f"**Recommended action:** {queue_entry['recommended_action']}")
    with right:
        if selected["patient_id"] and (allow_deterioration or allow_discharge):
            st.info(
                "The bed view is an operational projection. Discharging or "
                "reassessing this patient updates the queue and may pull the next "
                "waiting patient into an open bed."
            )
            action_col1, action_col2 = st.columns(2)
            if allow_deterioration and action_col1.button(
                "Simulate deterioration",
                key=f"deteriorate-{selected['patient_id']}",
                type="primary",
            ):
                client.deteriorate(selected["patient_id"])
                st.rerun()
            if allow_discharge and action_col2.button(
                "Discharge patient",
                key=f"discharge-bed-{selected['patient_id']}",
                type="primary",
            ):
                client.discharge(selected["patient_id"])
                st.rerun()
        elif not selected["patient_id"]:
            st.success("Available care space in this synthetic projection.")
    if board["waiting_patients"]:
        st.subheader("Waiting for a care space")
        st.dataframe(
            _frame(board["waiting_patients"]), hide_index=True, width="stretch"
        )
    st.caption(board["projection_notice"])
    return board


def _render_queue(snapshot: dict[str, Any], *, show_attention: bool = True) -> None:
    entries = snapshot["entries"]
    _limited_mode_banner(snapshot["model_status"], snapshot["warnings"])
    metrics = st.columns(5)
    metrics[0].metric("Waiting", snapshot["patient_count"])
    metrics[1].metric("Mode", snapshot["mode"].title())
    metrics[2].metric("Queue pressure", f"{snapshot['queue_pressure']:.1f}x")
    metrics[3].metric("Model", snapshot["model_status"].title())
    metrics[4].metric(
        "Low confidence", sum(item["confidence"] == "low" for item in entries)
    )

    if show_attention:
        _render_attention_panel(entries)

    st.subheader("Live priority queue")
    movement = _movement_labels(entries)
    if not entries:
        st.info("No patients are currently waiting.")
    for item in sorted(entries, key=lambda e: e["position"]):
        move_label = movement.get(item["patient_id"])
        reason = item["reasons"][0] if item["reasons"] else item["recommended_action"]
        badges = " ".join(
            [
                _acuity_badge(item["acuity_label"]),
                _confidence_badge(item["confidence"]),
                _state_badge(item["state"]),
            ]
        )
        move_html = f'<span class="pt-movement">{move_label}</span>' if move_label else ""
        st.markdown(
            f"""
            <div class="pt-queue-row">
              <b>#{item['position']} {item['patient_id']}</b> &nbsp;{badges}
              &nbsp;{move_html}
              <div class="pt-queue-reason">{reason} &middot; Wait {item['wait_minutes']:.0f} min</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    _remember_positions(entries)

    if entries:
        with st.expander("Model detail (advanced)"):
            rows = [
                {
                    "Position": item["position"],
                    "Patient": item["patient_id"],
                    "Acuity": item["acuity_label"].replace("_", " ").title(),
                    "Confidence": item["confidence"].title(),
                    "Wait (min)": item["wait_minutes"],
                    "State": item["state"].replace("_", " ").title(),
                    "Context effect": item["context_effect"],
                    "Action": item["recommended_action"],
                }
                for item in entries
            ]
            st.dataframe(_frame(rows), hide_index=True, width="stretch")
            if snapshot["model_status"] == "ready":
                st.plotly_chart(queue_chart(entries), width="stretch")


def _render_patient_detail(
    client: APIClient, snapshot: dict[str, Any], *, allow_discharge: bool = False
) -> None:
    entries = snapshot["entries"]
    if not entries:
        st.info("No patients are currently waiting.")
        return
    selected_id = st.selectbox("Patient", [item["patient_id"] for item in entries])
    selected = next(item for item in entries if item["patient_id"] == selected_id)

    st.markdown(
        f"### {selected['patient_id']} &nbsp;{_acuity_badge(selected['acuity_label'])}",
        unsafe_allow_html=True,
    )
    columns = st.columns(3)
    columns[0].metric("Queue position", selected["position"])
    columns[1].markdown(
        f"**Confidence**<br>{_confidence_badge(selected['confidence'])}",
        unsafe_allow_html=True,
    )
    columns[2].markdown(
        f"**Monitoring status**<br>{_state_badge(selected['state'])}",
        unsafe_allow_html=True,
    )

    st.info("Recommended action: " + selected["recommended_action"])
    st.subheader("Prioritized because")
    for reason in selected["reasons"]:
        st.write(f"- {reason}")
    if selected["missing_information"]:
        st.warning("Missing information: " + ", ".join(selected["missing_information"]))

    action_col1, action_col2 = st.columns(2)
    if action_col1.button("Simulate patient deterioration", type="primary"):
        client.deteriorate(selected_id)
        st.rerun()
    if allow_discharge and action_col2.button(
        "Discharge patient", key=f"discharge-detail-{selected_id}", type="primary"
    ):
        client.discharge(selected_id)
        st.rerun()


def _render_override(client: APIClient, snapshot: dict[str, Any]) -> None:
    entries = snapshot["entries"]
    if not entries:
        st.info("No queue is available to override.")
        return
    summary = st.session_state.get("last_override_summary")
    if summary:
        st.markdown(
            f"""
            <div class="pt-safety-status">
              <b>OVERRIDE RECORDED</b><br>
              AI recommendation: position #{summary['ai_position']}<br>
              Clinician decision: position #{summary['clinician_position']}<br>
              Reason: {summary['reason'] or '&mdash;'}<br>
              Timestamp: {summary['timestamp']}<br>
              Audit reference: {summary['audit_ref']}
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Dismiss"):
            del st.session_state["last_override_summary"]
            st.rerun()

    patient_id = st.selectbox(
        "Patient", [item["patient_id"] for item in entries], key="override_patient"
    )
    selected = next(item for item in entries if item["patient_id"] == patient_id)
    reasons = "; ".join(selected["reasons"][:2]) or selected["recommended_action"]
    st.markdown(
        f"""
        <div class="pt-recommendation">
          <b>PatientTriage.ai recommendation</b><br>
          Current position #{selected['position']} &nbsp;{_acuity_badge(selected['acuity_label'])}<br>
          <span class="pt-queue-reason">{reasons}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    show_form = st.session_state.get("show_override_form", False)
    accept_col, override_col = st.columns(2)
    if accept_col.button("Accept recommendation", width="stretch"):
        st.session_state["show_override_form"] = False
        st.info("No change made. The AI-recommended position stands.")
        show_form = False
    if override_col.button("Override position", width="stretch", type="primary"):
        st.session_state["show_override_form"] = True
        show_form = True

    if show_form:
        with st.form("override_form"):
            target_position = st.number_input(
                "Target position", min_value=1, max_value=len(entries), value=1
            )
            clinician_id = st.text_input("Clinician ID", value="demo_doctor_01")
            reason = st.text_area(
                "Clinical or operational reason",
                placeholder="Explain the judgement that supersedes the recommendation.",
            )
            submitted = st.form_submit_button("Apply and audit override", type="primary")
        if submitted:
            client.override(
                patient_id=patient_id,
                target_position=int(target_position),
                clinician_id=clinician_id,
                reason=reason,
            )
            latest = client.audit(limit=1)
            audit_ref = latest[0] if latest else {}
            st.session_state["show_override_form"] = False
            st.session_state["last_override_summary"] = {
                "ai_position": selected["position"],
                "clinician_position": int(target_position),
                "reason": reason,
                "timestamp": audit_ref.get("occurred_at", "—"),
                "audit_ref": audit_ref.get("event_id", "—"),
            }
            st.rerun()


def _render_coordination(client: APIClient, domain: str, actor_id: str) -> None:
    tasks = client.coordination(domain)
    label = "Pharmacy" if domain == "pharmacy" else "Blood bank"
    st.caption(
        f"{label} receives minimum-necessary readiness signals only. This is not an "
        "inventory, ordering, cross-match, or dispensing module."
    )
    st.subheader("Action required")
    if not tasks:
        st.success("No current readiness signals.")
        return
    for task in tasks:
        with st.container(border=True):
            left, middle, right = st.columns([1.1, 3.5, 1.3])
            left.metric("Priority", task["priority"])
            middle.markdown(f"**{task['patient_id']} · {task['summary']}**")
            middle.caption(task["reason"])
            if task["status"] == "acknowledged":
                right.markdown(
                    f"**ACKNOWLEDGED**<br><span class='pt-queue-reason'>{task['acknowledged_by']}</span>",
                    unsafe_allow_html=True,
                )
            elif right.button("Acknowledge", key=task["task_id"], type="primary"):
                client.acknowledge(
                    domain=domain,
                    task_id=task["task_id"],
                    actor_id=actor_id,
                )
                st.rerun()


def _render_infrastructure(profile: dict[str, Any]) -> None:
    metrics = st.columns(5)
    metrics[0].metric("Hospital level", profile["hospital_level"].title())
    metrics[1].metric("Catchment", f"{profile['catchment_population']:,}")
    metrics[2].metric("Hospital beds", profile["total_hospital_beds"])
    metrics[3].metric("ED beds", profile["ed_beds"])
    metrics[4].metric("Treatment teams", profile["treatment_teams"])
    st.caption(profile["assumption_notice"])
    shift, staffing = st.columns([1, 2])
    with shift:
        st.subheader("Simulation window")
        st.write(f"**Shift:** {profile['shift']['label']}")
        st.write(f"**Start:** {profile['shift']['start_time']}")
        st.write(f"**End:** {profile['shift']['end_time']}")
        st.write(f"**Normal arrivals:** {profile['normal_shift_arrivals']}")
        st.write(f"**3x surge arrivals:** {profile['surge_shift_arrivals']}")
    with staffing:
        st.subheader("Illustrative shift staffing")
        staff_rows = [
            {"Role": key.replace("_", " ").title(), "Count": value}
            for key, value in profile["staffing"].items()
        ]
        st.dataframe(_frame(staff_rows), hide_index=True, width="stretch")


_REASSESSMENT_STATES = {
    "reassessment_due",
    "stale_information",
    "deteriorating",
    "critical_escalation",
}


def _admin_status_strip(board: dict[str, Any]) -> None:
    reassessments_due = sum(
        1
        for bed in board["beds"]
        if bed.get("state") in _REASSESSMENT_STATES
    ) + sum(
        1
        for patient in board["waiting_patients"]
        if patient.get("state") in _REASSESSMENT_STATES
    )
    surge_active = st.session_state.get("scenario_mode") == "surge"
    metrics = st.columns(5)
    metrics[0].metric("ED occupancy", f"{board['occupied_beds']}/{board['total_beds']}")
    metrics[1].metric("Available beds", board["empty_beds"])
    metrics[2].metric("Waiting patients", board["waiting_for_bed"])
    metrics[3].metric("Reassessments due", reassessments_due)
    metrics[4].metric("Surge status", "3x surge" if surge_active else "Normal")
    if surge_active:
        st.markdown(
            f"""
            <div class="pt-surge-banner">
              <b>SURGE MODE ACTIVE</b> &mdash; occupancy {board['occupancy_percent']:.0f}%,
              {board['waiting_for_bed']} waiting, {reassessments_due} reassessments due.
              Safety floors remain unchanged during surge conditions.
            </div>
            """,
            unsafe_allow_html=True,
        )


default_api = os.getenv("PATIENT_TRIAGE_API_URL", "http://localhost:8000")
api_url = st.sidebar.text_input("API URL", value=default_api)
selected_role_label = st.sidebar.selectbox(
    "Dashboard role",
    list(ROLE_LABELS.values()),
)
role = next(
    value for value, label in ROLE_LABELS.items() if label == selected_role_label
)
client = APIClient(api_url, role=role)

try:
    health = client.health()
    access = client.access()
    profile = client.infrastructure()
except httpx2.HTTPError as exc:
    st.error(f"Cannot connect to the API at {api_url}: {exc}")
    st.stop()

policy = next(item for item in access["roles"] if item["role"] == role)
st.sidebar.caption(policy["description"])
with st.sidebar.expander("Prototype permissions"):
    st.write("**Read**")
    st.code("\n".join(policy["read_permissions"]) or "None")
    st.write("**Write**")
    st.code("\n".join(policy["write_permissions"]) or "None")
    st.caption(access["prototype_notice"])

render_header(ROLE_LABELS[role])

try:
    if role == "nurse":
        model_failure = st.sidebar.toggle("Simulate CDM failure", value=False)
        snapshot = client.queue(model_failure=model_failure)
        queue_tab, bed_tab, patient_tab = st.tabs(
            ["Attention / queue", "Bed-wise view", "Patient-wise view"]
        )
        with queue_tab:
            _render_queue(snapshot)
        with bed_tab:
            _render_bed_board(
                client,
                allow_deterioration=True,
                model_failure=model_failure,
                queue_entries=snapshot["entries"],
            )
        with patient_tab:
            _render_patient_detail(client, snapshot)

    elif role == "doctor":
        model_failure = st.sidebar.toggle("Simulate CDM failure", value=False)
        snapshot = client.queue(model_failure=model_failure)
        queue_tab, patient_tab, beds_tab, override_tab, support_tab, audit_tab = (
            st.tabs(
                ["Queue", "Patient", "Bed map", "Override", "Readiness", "Audit"]
            )
        )
        with queue_tab:
            _render_queue(snapshot)
        with patient_tab:
            _render_patient_detail(client, snapshot, allow_discharge=True)
        with beds_tab:
            _render_bed_board(
                client,
                allow_deterioration=True,
                allow_discharge=True,
                model_failure=model_failure,
                queue_entries=snapshot["entries"],
            )
        with override_tab:
            _render_override(client, snapshot)
        with support_tab:
            pharmacy_tab, blood_tab = st.tabs(["Pharmacy", "Blood bank"])
            with pharmacy_tab:
                _render_coordination(client, "pharmacy", "demo_doctor_01")
            with blood_tab:
                _render_coordination(client, "blood_bank", "demo_doctor_01")
        with audit_tab:
            verification = client.verify_audit()
            validity = "Valid" if verification["valid"] else "Invalid"
            st.metric("Tamper-evident hash chain", validity)
            events = client.audit(limit=100)
            rows = [
                {
                    "Time": e["occurred_at"],
                    "Action": e["event_type"].replace("_", " ").title(),
                    "Actor": e["actor_id"],
                    "Patient": e["patient_id"] or "—",
                    "Model": e["model_version"],
                }
                for e in events
            ]
            st.dataframe(_frame(rows), hide_index=True, width="stretch")
            with st.expander("Hash chain detail"):
                st.dataframe(_frame(events), hide_index=True, width="stretch")

    elif role == "pharmacy":
        _render_coordination(client, "pharmacy", "demo_pharmacist_01")

    elif role == "blood_bank":
        _render_coordination(client, "blood_bank", "demo_bloodbank_01")

    else:
        st.sidebar.subheader("Scenario control")
        normal_col, surge_col = st.sidebar.columns(2)
        if normal_col.button("20 patients", width="stretch"):
            client.load_scenario("normal")
            st.session_state["scenario_mode"] = "normal"
            st.rerun()
        if surge_col.button("3x surge", width="stretch"):
            client.load_scenario("surge")
            st.session_state["scenario_mode"] = "surge"
            st.rerun()

        status_board = client.beds()
        _admin_status_strip(status_board)

        infra_tab, capacity_tab, evaluation_tab, audit_tab = st.tabs(
            ["Infrastructure", "Capacity", "Policy evaluation", "Audit"]
        )
        with infra_tab:
            _render_infrastructure(profile)
        with capacity_tab:
            board = _render_bed_board(client, allow_deterioration=False)
            st.plotly_chart(
                occupancy_gauge(board["occupancy_percent"]), width="stretch"
            )
        with evaluation_tab:
            report = client.baselines()
            st.caption(
                "PatientTriage.ai combines protected safety floors, dynamic queue "
                "adaptation, continuous monitoring, uncertainty visibility, and "
                "fail-safe behavior. This evidence is a simulation, not a claim of "
                "universal superiority."
            )
            st.plotly_chart(baseline_chart(report["results"]), width="stretch")
            st.dataframe(_frame(report["results"]), hide_index=True, width="stretch")
            st.info(report["interpretation"])
            st.caption(report["limitation"])
        with audit_tab:
            verification = client.verify_audit()
            validity = "Valid" if verification["valid"] else "Invalid"
            st.metric("Tamper-evident hash chain", validity)
            events = client.audit(limit=100)
            rows = [
                {
                    "Time": e["occurred_at"],
                    "Action": e["event_type"].replace("_", " ").title(),
                    "Actor": e["actor_id"],
                    "Patient": e["patient_id"] or "—",
                    "Model": e["model_version"],
                }
                for e in events
            ]
            st.dataframe(_frame(rows), hide_index=True, width="stretch")
            with st.expander("Hash chain detail"):
                st.dataframe(_frame(events), hide_index=True, width="stretch")
except httpx2.HTTPStatusError as exc:
    detail = exc.response.json().get("detail", str(exc))
    st.error(f"Action is unavailable for this role: {detail}")
except httpx2.HTTPError as exc:
    st.error(f"API action failed: {exc}")

st.caption(
    f"API {health['status']} · Model {health['model_version']} · Version 0.3.0 · Prototype only"
)
