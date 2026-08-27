"""Accessible, brand-aligned Plotly helpers for the dashboard."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.graph_objects import Figure

from dashboard.theme import AMBER, BLUE, CYAN, GREEN, NAVY, ORANGE, RED, TEAL

ACUITY_COLORS = {
    "critical": RED,
    "emergent": ORANGE,
    "urgent": AMBER,
    "less_urgent": BLUE,
    "non_urgent": "#718096",
    "empty": GREEN,
}


def _base_layout(figure: Figure, *, title: str) -> Figure:
    figure.update_layout(
        title={"text": title, "font": {"color": NAVY, "size": 20}},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,.96)",
        font={"family": "Arial, sans-serif", "color": NAVY},
        margin={"l": 28, "r": 20, "t": 64, "b": 34},
        legend_title_text="",
    )
    return figure


def queue_chart(entries: list[dict[str, object]]) -> Figure:
    frame = pd.DataFrame(entries)
    if frame.empty:
        return Figure()
    frame["patient"] = frame["patient_id"].astype(str)
    frame["context_effect_display"] = frame["context_effect"].fillna(0.0)
    frame = frame.sort_values("position", ascending=False)
    figure = go.Figure(
        go.Bar(
            x=frame["cdm_utility"],
            y=frame["patient"],
            orientation="h",
            marker_color=[ACUITY_COLORS[item] for item in frame["acuity_label"]],
            customdata=frame[
                ["position", "confidence", "state", "context_effect_display"]
            ],
            hovertemplate=(
                "<b>%{y}</b><br>Utility %{x:.2f}<br>Position %{customdata[0]}"
                "<br>Confidence %{customdata[1]}<br>State %{customdata[2]}"
                "<br>Context effect %{customdata[3]:+.2f}<extra></extra>"
            ),
        )
    )
    figure.update_xaxes(title="Context-dependent utility", gridcolor="#E6EEF5")
    figure.update_yaxes(title="")
    return _base_layout(figure, title="Dynamic queue utility")


def bed_board_chart(beds: list[dict[str, object]]) -> Figure:
    frame = pd.DataFrame(beds)
    if frame.empty:
        return Figure()
    frame["column"] = [index % 6 + 1 for index in range(len(frame))]
    frame["row"] = [3 - index // 6 for index in range(len(frame))]
    frame["display_state"] = frame["acuity_label"].fillna("empty")
    frame["patient_display"] = frame["patient_id"].fillna("Available")
    frame["wait_display"] = frame["wait_minutes"].fillna(0.0)
    figure = go.Figure()
    for state in [
        "critical",
        "emergent",
        "urgent",
        "less_urgent",
        "non_urgent",
        "empty",
    ]:
        subset = frame[frame["display_state"] == state]
        if subset.empty:
            continue
        figure.add_trace(
            go.Scatter(
                x=subset["column"],
                y=subset["row"],
                mode="markers+text",
                name=state.replace("_", " ").title(),
                marker={
                    "symbol": "square",
                    "size": 58,
                    "color": ACUITY_COLORS[state],
                    "line": {"width": 3, "color": "white"},
                },
                text=subset["bed_id"],
                textposition="middle center",
                textfont={"color": "white", "size": 11, "family": "Arial Black"},
                customdata=subset[
                    ["bed_id", "zone", "patient_display", "wait_display", "state"]
                ],
                hovertemplate=(
                    "<b>%{customdata[0]}</b> · %{customdata[1]}"
                    "<br>%{customdata[2]}<br>Wait %{customdata[3]:.0f} min"
                    "<br>State %{customdata[4]}<extra></extra>"
                ),
            )
        )
    figure.update_xaxes(visible=False, range=[0.4, 6.6])
    figure.update_yaxes(visible=False, range=[0.4, 3.6], scaleanchor="x")
    figure.update_layout(height=480, clickmode="event+select")
    return _base_layout(figure, title="18-bed emergency department · select a bed")


def baseline_chart(results: list[dict[str, object]]) -> Figure:
    frame = pd.DataFrame(results)
    if frame.empty:
        return Figure()
    colors = [
        TEAL if name == "PatientTriage.ai" else BLUE for name in frame["display_name"]
    ]
    figure = go.Figure(
        go.Bar(
            x=frame["display_name"],
            y=frame["safety_weighted_delay"],
            marker_color=colors,
            customdata=frame[
                [
                    "mean_additional_wait_minutes",
                    "p95_additional_wait_minutes",
                    "starvation_count",
                    "completed_within_120_minutes",
                ]
            ],
            hovertemplate=(
                "<b>%{x}</b><br>Safety-weighted delay %{y:.1f}"
                "<br>Mean added wait %{customdata[0]:.1f} min"
                "<br>P95 added wait %{customdata[1]:.1f} min"
                "<br>Starvation count %{customdata[2]}"
                "<br>Completed in horizon %{customdata[3]}<extra></extra>"
            ),
        )
    )
    figure.update_xaxes(title="", tickangle=-20)
    figure.update_yaxes(title="Lower is safer in this simulation", gridcolor="#E6EEF5")
    return _base_layout(figure, title="Queue-policy baseline comparison")


def occupancy_gauge(occupancy_percent: float) -> Figure:
    figure = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=occupancy_percent,
            number={"suffix": "%", "font": {"color": NAVY}},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": CYAN},
                "steps": [
                    {"range": [0, 70], "color": "#DCFCE7"},
                    {"range": [70, 90], "color": "#FEF3C7"},
                    {"range": [90, 100], "color": "#FFE4E6"},
                ],
                "threshold": {"line": {"color": RED, "width": 4}, "value": 90},
            },
        )
    )
    figure.update_layout(height=260)
    return _base_layout(figure, title="ED occupancy")
