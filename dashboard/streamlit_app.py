"""Role-specific PatientTriage.ai dashboard for synthetic demonstrations."""

from __future__ import annotations

import os
from typing import Any

import httpx2
import pandas as pd
import streamlit as st

from dashboard.charts import (
    baseline_chart,
    bed_board_chart,
    occupancy_gauge,
    queue_chart,
)
from dashboard.client import APIClient
from dashboard.theme import apply_brand_theme, render_product_header

st.set_page_config(
    page_title="PatientTriage.ai · District ED",
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


def _frame(rows: list[dict[str, Any]]) -> pd.DataFrame:
    return pd.DataFrame(rows) if rows else pd.DataFrame()


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


def _render_bed_board(
    client: APIClient,
    *,
    allow_deterioration: bool,
    model_failure: bool = False,
) -> dict[str, Any]:
    board = client.beds(model_failure=model_failure)
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
    with right:
        if selected["patient_id"] and allow_deterioration:
            st.info(
                "The bed view is an operational projection. Reassessment updates the "
                "patient view and may change queue position."
            )
            if st.button(
                "Simulate deterioration",
                key=f"deteriorate-{selected['patient_id']}",
                type="primary",
            ):
                client.deteriorate(selected["patient_id"])
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


def _render_queue(snapshot: dict[str, Any]) -> None:
    entries = snapshot["entries"]
    metrics = st.columns(5)
    metrics[0].metric("Waiting", snapshot["patient_count"])
    metrics[1].metric("Mode", snapshot["mode"].title())
    metrics[2].metric("Queue pressure", f"{snapshot['queue_pressure']:.1f}x")
    metrics[3].metric("Model", snapshot["model_status"].title())
    metrics[4].metric(
        "Low confidence", sum(item["confidence"] == "low" for item in entries)
    )
    for warning in snapshot["warnings"]:
        st.error(warning)
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
    if entries and snapshot["model_status"] == "ready":
        st.plotly_chart(queue_chart(entries), width="stretch")


def _render_patient_detail(client: APIClient, snapshot: dict[str, Any]) -> None:
    entries = snapshot["entries"]
    if not entries:
        st.info("No patients are currently waiting.")
        return
    selected_id = st.selectbox("Patient", [item["patient_id"] for item in entries])
    selected = next(item for item in entries if item["patient_id"] == selected_id)
    columns = st.columns(4)
    columns[0].metric("Queue position", selected["position"])
    acuity = selected["acuity_label"].replace("_", " ").title()
    columns[1].metric("Acuity", acuity)
    columns[2].metric("Confidence", selected["confidence"].title())
    columns[3].metric("State", selected["state"].replace("_", " ").title())
    st.subheader("Why this position")
    for reason in selected["reasons"]:
        st.write(f"- {reason}")
    if selected["missing_information"]:
        st.warning("Missing: " + ", ".join(selected["missing_information"]))
    st.info("Recommended action: " + selected["recommended_action"])
    if st.button("Simulate patient deterioration", type="primary"):
        client.deteriorate(selected_id)
        st.rerun()


def _render_override(client: APIClient, snapshot: dict[str, Any]) -> None:
    entries = snapshot["entries"]
    if not entries:
        st.info("No queue is available to override.")
        return
    with st.form("override_form"):
        patient_id = st.selectbox(
            "Patient to move", [item["patient_id"] for item in entries]
        )
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
        st.success("Override recorded in the tamper-evident audit chain.")
        st.rerun()


def _render_coordination(client: APIClient, domain: str, actor_id: str) -> None:
    tasks = client.coordination(domain)
    label = "Pharmacy" if domain == "pharmacy" else "Blood bank"
    st.caption(
        f"{label} receives minimum-necessary readiness signals only. This is not an "
        "inventory, ordering, cross-match, or dispensing module."
    )
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
                right.success(f"Acknowledged\n\n{task['acknowledged_by']}")
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
    st.warning(profile["assumption_notice"])
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

render_product_header(ROLE_LABELS[role])

try:
    if role == "nurse":
        model_failure = st.sidebar.toggle("Simulate CDM failure", value=False)
        snapshot = client.queue(model_failure=model_failure)
        bed_tab, patient_tab, queue_tab = st.tabs(
            ["Bed-wise view", "Patient-wise view", "Live queue"]
        )
        with bed_tab:
            _render_bed_board(
                client,
                allow_deterioration=True,
                model_failure=model_failure,
            )
        with patient_tab:
            _render_patient_detail(client, snapshot)
        with queue_tab:
            _render_queue(snapshot)

    elif role == "doctor":
        model_failure = st.sidebar.toggle("Simulate CDM failure", value=False)
        snapshot = client.queue(model_failure=model_failure)
        queue_tab, beds_tab, patient_tab, override_tab, support_tab, audit_tab = (
            st.tabs(
                ["Live queue", "Bed map", "Patient", "Override", "Readiness", "Audit"]
            )
        )
        with queue_tab:
            _render_queue(snapshot)
        with beds_tab:
            _render_bed_board(
                client,
                allow_deterioration=True,
                model_failure=model_failure,
            )
        with patient_tab:
            _render_patient_detail(client, snapshot)
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
            st.dataframe(
                _frame(client.audit(limit=100)), hide_index=True, width="stretch"
            )

    elif role == "pharmacy":
        _render_coordination(client, "pharmacy", "demo_pharmacist_01")

    elif role == "blood_bank":
        _render_coordination(client, "blood_bank", "demo_bloodbank_01")

    else:
        st.sidebar.subheader("Scenario control")
        normal_col, surge_col = st.sidebar.columns(2)
        if normal_col.button("20 patients", width="stretch"):
            client.load_scenario("normal")
            st.rerun()
        if surge_col.button("3x surge", width="stretch"):
            client.load_scenario("surge")
            st.rerun()
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
            st.plotly_chart(baseline_chart(report["results"]), width="stretch")
            st.dataframe(_frame(report["results"]), hide_index=True, width="stretch")
            st.info(report["interpretation"])
            st.caption(report["limitation"])
        with audit_tab:
            verification = client.verify_audit()
            validity = "Valid" if verification["valid"] else "Invalid"
            st.metric("Tamper-evident hash chain", validity)
            st.dataframe(
                _frame(client.audit(limit=100)), hide_index=True, width="stretch"
            )
except httpx2.HTTPStatusError as exc:
    detail = exc.response.json().get("detail", str(exc))
    st.error(f"Action is unavailable for this role: {detail}")
except httpx2.HTTPError as exc:
    st.error(f"API action failed: {exc}")

st.caption(
    f"API {health['status']} · Model {health['model_version']} · Version 0.3.0 · Prototype only"
)
