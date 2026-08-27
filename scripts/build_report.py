"""Build the branded technical and business evidence report."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    Image,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "pdf" / "PatientTriage_AI_Technical_and_Business_Report.pdf"
TMP = ROOT / "tmp" / "pdfs"
LOGO = ROOT / "assets" / "branding" / "patienttriage-logo.png"

NAVY = colors.HexColor("#062B54")
BLUE = colors.HexColor("#0878E8")
CYAN = colors.HexColor("#10BFE0")
TEAL = colors.HexColor("#10B8A6")
GREEN = colors.HexColor("#16A34A")
AMBER = colors.HexColor("#F59E0B")
ORANGE = colors.HexColor("#F97316")
RED = colors.HexColor("#EF233C")
INK = colors.HexColor("#132238")
MUTED = colors.HexColor("#5F7085")
PALE = colors.HexColor("#F4F8FC")
LINE = colors.HexColor("#D7E4EF")


def _register_fonts() -> tuple[str, str]:
    regular = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    bold = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
    if regular.exists() and bold.exists():
        pdfmetrics.registerFont(TTFont("DejaVu", regular))
        pdfmetrics.registerFont(TTFont("DejaVu-Bold", bold))
        return "DejaVu", "DejaVu-Bold"
    return "Helvetica", "Helvetica-Bold"


FONT, FONT_BOLD = _register_fonts()


def _styles() -> dict[str, ParagraphStyle]:
    sample = getSampleStyleSheet()
    return {
        "cover_title": ParagraphStyle(
            "CoverTitle",
            parent=sample["Title"],
            fontName=FONT_BOLD,
            fontSize=28,
            leading=34,
            textColor=NAVY,
            alignment=TA_LEFT,
            spaceAfter=12,
        ),
        "cover_sub": ParagraphStyle(
            "CoverSub",
            parent=sample["Normal"],
            fontName=FONT,
            fontSize=13,
            leading=19,
            textColor=MUTED,
        ),
        "h1": ParagraphStyle(
            "H1",
            parent=sample["Heading1"],
            fontName=FONT_BOLD,
            fontSize=21,
            leading=27,
            textColor=NAVY,
            spaceBefore=3,
            spaceAfter=10,
        ),
        "h2": ParagraphStyle(
            "H2",
            parent=sample["Heading2"],
            fontName=FONT_BOLD,
            fontSize=13.5,
            leading=18,
            textColor=BLUE,
            spaceBefore=9,
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "Body",
            parent=sample["BodyText"],
            fontName=FONT,
            fontSize=9.3,
            leading=14.2,
            textColor=INK,
            spaceAfter=6,
        ),
        "small": ParagraphStyle(
            "Small",
            parent=sample["BodyText"],
            fontName=FONT,
            fontSize=7.6,
            leading=10.5,
            textColor=MUTED,
        ),
        "callout": ParagraphStyle(
            "Callout",
            parent=sample["BodyText"],
            fontName=FONT_BOLD,
            fontSize=11.5,
            leading=17,
            textColor=NAVY,
            alignment=TA_CENTER,
        ),
        "table": ParagraphStyle(
            "Table",
            parent=sample["BodyText"],
            fontName=FONT,
            fontSize=7.2,
            leading=9.5,
            textColor=INK,
        ),
        "table_head": ParagraphStyle(
            "TableHead",
            parent=sample["BodyText"],
            fontName=FONT_BOLD,
            fontSize=7.4,
            leading=9.5,
            textColor=colors.white,
        ),
    }


S = _styles()


def P(text: str, style: str = "body") -> Paragraph:
    return Paragraph(text, S[style])


def bullet(text: str) -> Paragraph:
    return Paragraph(f"- {text}", S["body"])


def callout(text: str, color: colors.Color = TEAL) -> Table:
    table = Table([[P(text, "callout")]], colWidths=[174 * mm])
    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    colors.Color(color.red, color.green, color.blue, alpha=0.10),
                ),
                ("BOX", (0, 0), (-1, -1), 1, color),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    return table


def table(
    headers: list[str],
    rows: list[list[object]],
    widths: list[float] | None = None,
) -> Table:
    data = [[P(str(item), "table_head") for item in headers]]
    data.extend([[P(str(item), "table") for item in row] for row in rows])
    item = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    item.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("GRID", (0, 0), (-1, -1), 0.35, LINE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PALE]),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return item


def section(title: str, number: str) -> list[object]:
    return [
        P(f"{number}  {title}", "h1"),
        HRFlowable(width="100%", thickness=1.4, color=CYAN, spaceAfter=9),
    ]


def _make_charts() -> dict[str, Path]:
    TMP.mkdir(parents=True, exist_ok=True)
    baseline_rows = list(
        csv.DictReader((ROOT / "reports" / "baseline_benchmark.csv").open())
    )
    normal = [row for row in baseline_rows if row["scenario"] == "normal"]
    names = [
        row["display_name"].replace("PatientTriage.ai", "PatientTriage")
        for row in normal
    ]
    delay = [float(row["safety_weighted_delay"]) for row in normal]
    completed = [int(row["completed_within_120_minutes"]) for row in normal]
    palette = ["#0878E8"] * 5 + ["#10B8A6"]
    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.1))
    axes[0].barh(names[::-1], delay[::-1], color=palette[::-1])
    axes[0].set_title(
        "Safety-weighted delay (lower is better)", color="#062B54", weight="bold"
    )
    axes[0].grid(axis="x", alpha=0.2)
    axes[1].barh(names[::-1], completed[::-1], color=palette[::-1])
    axes[1].set_title("Completed by 120 minutes", color="#062B54", weight="bold")
    axes[1].grid(axis="x", alpha=0.2)
    for axis in axes:
        axis.spines[["top", "right", "left"]].set_visible(False)
        axis.tick_params(labelsize=8)
    fig.tight_layout()
    baseline_path = TMP / "baseline.png"
    fig.savefig(baseline_path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    scale_rows = list(
        csv.DictReader((ROOT / "reports" / "scalability_benchmark.csv").open())
    )
    counts = [int(row["patient_count"]) for row in scale_rows]
    means = [float(row["mean_latency_ms"]) for row in scale_rows]
    p95 = [float(row["p95_latency_ms"]) for row in scale_rows]
    fig, axis = plt.subplots(figsize=(8.7, 3.8))
    axis.plot(counts, means, marker="o", linewidth=2.8, color="#0878E8", label="Mean")
    axis.plot(counts, p95, marker="o", linewidth=2.8, color="#10B8A6", label="P95")
    axis.fill_between(counts, means, p95, color="#10BFE0", alpha=0.12)
    axis.set_xlabel("Patients in queue")
    axis.set_ylabel("Rank latency (ms)")
    axis.set_title("Local in-process ranking latency", color="#062B54", weight="bold")
    axis.grid(alpha=0.22)
    axis.legend(frameon=False)
    axis.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    scale_path = TMP / "scale.png"
    fig.savefig(scale_path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    cost = json.loads((ROOT / "configs" / "cost_assumptions.json").read_text())
    ranges = cost["monthly_cloud_ranges_usd"]
    labels = [item["stage"].replace("_", " ").title() for item in ranges]
    low = [item["low"] for item in ranges]
    high = [item["high"] for item in ranges]
    fig, axis = plt.subplots(figsize=(9.2, 4.1))
    y = list(range(len(labels)))
    axis.barh(y, high, color="#DDF4FA", label="High")
    axis.barh(y, low, color="#0878E8", label="Low")
    axis.set_yticks(y, labels)
    axis.set_xlabel("Illustrative monthly USD")
    axis.set_title("Cloud planning ranges, not a quote", color="#062B54", weight="bold")
    axis.spines[["top", "right", "left"]].set_visible(False)
    axis.grid(axis="x", alpha=0.2)
    axis.legend(frameon=False)
    fig.tight_layout()
    cost_path = TMP / "cost.png"
    fig.savefig(cost_path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return {"baseline": baseline_path, "scale": scale_path, "cost": cost_path}


class ReportDoc(BaseDocTemplate):
    def __init__(self, filename: Path) -> None:
        super().__init__(
            str(filename),
            pagesize=A4,
            leftMargin=18 * mm,
            rightMargin=18 * mm,
            topMargin=19 * mm,
            bottomMargin=18 * mm,
            title="PatientTriage.ai Technical and Business Report",
            author="Team ETINIMTSAL",
        )
        frame = Frame(
            self.leftMargin,
            self.bottomMargin,
            self.width,
            self.height,
            id="body",
        )
        self.addPageTemplates(
            [PageTemplate(id="report", frames=[frame], onPage=self._page)]
        )

    def _page(self, canvas, doc) -> None:
        canvas.saveState()
        width, height = A4
        canvas.setFillColor(NAVY)
        canvas.rect(0, height - 9 * mm, width, 9 * mm, fill=1, stroke=0)
        canvas.setFont(FONT, 7)
        canvas.setFillColor(MUTED)
        canvas.drawString(
            18 * mm,
            10 * mm,
            "PatientTriage.ai | Synthetic prototype | Not for patient care",
        )
        canvas.drawRightString(width - 18 * mm, 10 * mm, f"Page {doc.page}")
        canvas.restoreState()


def build() -> Path:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    charts = _make_charts()
    story: list[object] = []

    story.extend(
        [
            Spacer(1, 18 * mm),
            Image(str(LOGO), width=174 * mm, height=98.5 * mm),
            Spacer(1, 5 * mm),
            P(
                "Technical, Architecture, Evidence, Business, and Regulatory Report",
                "cover_title",
            ),
            P(
                "Phase 2 hackathon package | Version 0.3.0 | District emergency-department simulation | 25 August 2026",
                "cover_sub",
            ),
            Spacer(1, 8 * mm),
            callout(
                "Safety-constrained dynamic queue coordination - not an ERP, diagnosis system, or replacement for clinical judgement.",
                TEAL,
            ),
            Spacer(1, 10 * mm),
            P(
                "Prepared for evaluation with synthetic patients only. All capacity, staffing, cost, and performance values are illustrative or machine-specific and must be replaced or independently validated before any pilot.",
                "small",
            ),
            PageBreak(),
        ]
    )

    story += section("Executive decision summary", "01")
    story += [
        callout(
            "Build PatientTriage.ai as a focused emergency coordination layer: safety rules first, CDM context second, uncertainty always visible, and clinicians always in control.",
            BLUE,
        ),
        Spacer(1, 5 * mm),
        P(
            "The upgraded solution is a complete, testable district-ED demonstration. It shows an 18-bed operational map, patient-wise queue, five role views, deterioration and surge behavior, minimum-necessary pharmacy/blood readiness, six scheduling baselines, scalability evidence, and audited override. The BTL ranker has been replaced by a feature-conditioned CDM.",
        ),
        P("The evidence supports three claims:"),
        bullet(
            "The software behaves as specified in synthetic scenarios, including edge and denial paths."
        ),
        bullet(
            "Safety-first ordering reduces safety-weighted delay relative to arrival- or service-time-only baselines in the supplied snapshot."
        ),
        bullet(
            "The main innovation is dynamic, uncertainty-aware, governable coordination - not a claim of clinical superiority."
        ),
        P("Decisions:"),
        bullet("Keep the product outside ERP scope."),
        bullet(
            "Do not add blockchain to the MVP; retain the hash-chain audit and revisit only for a multi-organization consortium."
        ),
        bullet(
            "Proceed next to a governed 12-week shadow-pilot design, not live autonomous use."
        ),
    ]

    story += section("Problem, users, and product boundary", "02")
    story += [
        P(
            "Emergency queues change after initial triage. New cases arrive, observations become stale, patients deteriorate, wait-related risk grows, and surge pressure competes with fairness. A static score cannot represent this changing operating state."
        ),
        P("The product coordinates four decisions:"),
        table(
            ["Decision", "User", "Output", "Explicit exclusion"],
            [
                [
                    "Who needs review next?",
                    "Nurse/doctor",
                    "Safe dynamic queue",
                    "No diagnosis or treatment",
                ],
                [
                    "What is happening across 18 spaces?",
                    "Nurse/doctor/admin",
                    "Operational projection",
                    "No bed-master authority",
                ],
                [
                    "What support readiness is needed?",
                    "Pharmacy/blood bank",
                    "Minimum signal + acknowledgement",
                    "No inventory/order/dispensing",
                ],
                [
                    "Is the process controlled?",
                    "Doctor/admin",
                    "Audit, override, benchmark",
                    "No compliance claim",
                ],
            ],
            [37 * mm, 28 * mm, 54 * mm, 55 * mm],
        ),
        Spacer(1, 4 * mm),
        callout(
            "Non-ERP boundary: no billing, procurement, stock ledger, dispensing, cross-match management, payroll, ADT source of truth, or authoritative bed management.",
            ORANGE,
        ),
    ]

    story += section("District-hospital simulation", "03")
    story += [
        P(
            "The active configuration represents an illustrative district-level hospital so the demo has concrete capacity, shift, and staffing constraints. It is a simulation fixture, not a standard."
        ),
        table(
            ["Parameter", "Value", "Parameter", "Value"],
            [
                ["Catchment", "500,000", "Hospital beds", "200"],
                ["ED spaces", "18", "Treatment teams", "4"],
                ["Shift", "08:00-20:00", "Normal / surge arrivals", "20 / 60"],
                [
                    "Zones",
                    "3 resus, 9 acute, 6 observation",
                    "Clinical staff",
                    "3 physicians, 4 residents, 14 nurses",
                ],
            ],
            [36 * mm, 51 * mm, 41 * mm, 46 * mm],
        ),
        P("Localization gates:"),
        bullet("Replace capacity and roster with approved hospital data."),
        bullet(
            "Fit arrival distributions and reassessment intervals to local evidence."
        ),
        bullet(
            "Map authoritative bed and observation identifiers through governed integration."
        ),
        bullet("Have clinical leadership approve every rule and escalation path."),
    ]

    story += section("Role dashboards and least privilege", "04")
    story += [
        table(
            ["Role", "Reads", "Writes", "Dashboard emphasis"],
            [
                [
                    "Nurse",
                    "Facility, patients, queue, beds",
                    "Intake, vitals, bed workflow",
                    "Bed-wise + patient-wise",
                ],
                [
                    "Doctor",
                    "Queue, beds, readiness, audit",
                    "Vitals, override, disposition",
                    "Clinical control",
                ],
                [
                    "Pharmacy",
                    "Facility, pharmacy readiness",
                    "Acknowledge",
                    "Minimum necessary",
                ],
                [
                    "Administration",
                    "Facility, beds, analytics, audit",
                    "Scenario control",
                    "Capacity + evidence",
                ],
                [
                    "Blood bank",
                    "Facility, blood readiness",
                    "Acknowledge",
                    "Minimum necessary",
                ],
            ],
            [26 * mm, 48 * mm, 45 * mm, 55 * mm],
        ),
        P(
            "The dashboard's role header is a demonstration of authorization boundaries, not authentication. Production needs hospital SSO/OIDC, identity proofing, session policy, device/network controls, least privilege, and periodic access review."
        ),
    ]

    story += section("18-bed and patient-wise experience", "05")
    story += [
        P(
            "The bed board renders six columns by three rows. Available spaces are green; occupied spaces use text plus critical red, emergent orange, urgent amber, less-urgent blue, or non-urgent slate. Select a bed to open its zone, patient ID, queue position, wait, acuity, and monitoring state."
        ),
        table(
            ["Color", "Meaning", "Secondary cue"],
            [
                ["Green", "Available", "Bed ID + available text"],
                ["Red", "Critical", "Acuity and critical-escalation text"],
                ["Orange", "Emergent", "Acuity text"],
                ["Amber", "Urgent", "Acuity text"],
                ["Blue", "Less urgent", "Acuity text"],
                ["Slate", "Non-urgent", "Acuity text"],
            ],
            [32 * mm, 58 * mm, 84 * mm],
        ),
        callout(
            "The bed board is a stable operational read model. It does not allocate, transfer, admit, discharge, or replace the hospital's bed system.",
            TEAL,
        ),
    ]

    story += section("System architecture and data flow", "06")
    story += [
        table(
            ["Layer", "Current component", "Production adapter"],
            [
                [
                    "Experience",
                    "Streamlit role dashboard",
                    "Accessible clinical web app",
                ],
                [
                    "API",
                    "FastAPI + Pydantic",
                    "Gateway, OIDC, rate limit, policy enforcement",
                ],
                [
                    "Decision",
                    "Rules + urgency + CDM + confidence",
                    "Versioned stateless service",
                ],
                [
                    "Operations",
                    "Bed/readiness projection",
                    "Event-driven integration read models",
                ],
                [
                    "Patients",
                    "Thread-safe in-memory repository",
                    "Governed transactional/FHIR adapter",
                ],
                [
                    "Audit",
                    "Hash-chained SQLite",
                    "Managed append-only store + immutable archive",
                ],
            ],
            [32 * mm, 60 * mm, 82 * mm],
        ),
        P("Core request path:"),
        bullet("Validate role and input schema."),
        bullet("Read the current synthetic waiting set."),
        bullet(
            "Apply safety, patient-level urgency, contextual utility, monitoring, and confidence."
        ),
        bullet("Apply valid clinician overrides and write the event chain."),
        bullet("Return a typed immutable snapshot with reasons and warnings."),
    ]

    story += section("CDM, safety, uncertainty, and failure", "07")
    story += [
        P(
            "The CDM uses seven bounded features: physiology, symptoms, pain, waiting, deterioration, uncertainty, and age-group vulnerability. It adds patient-to-waiting-set interactions to patient-only utility."
        ),
        callout(
            "Safety is lexicographic: final acuity first, CDM utility only inside the same acuity, then arrival time and deterministic ID.",
            RED,
        ),
        P("Safe failure path:"),
        bullet(
            "Recompute safety floors and patient-level urgency for current patients."
        ),
        bullet("Retain new arrivals rather than replaying a stale list."),
        bullet(
            "Use last-known-good order only as a within-acuity tie-break where possible."
        ),
        bullet("Mark all affected recommendations stale and low confidence."),
        bullet("Request manual reassessment and keep critical alerts visible."),
    ]

    story += section("Baseline evaluation", "08")
    story += [
        Image(str(charts["baseline"]), width=174 * mm, height=64 * mm),
        P(
            "Normal 20-patient scenario, four non-preemptive treatment teams, 120-minute horizon. PatientTriage.ai ties acuity priority on safety-weighted delay because safety-first order dominates this static snapshot. SJF-like completes more cases in the horizon but delays critical work."
        ),
        table(
            ["Policy", "What it optimizes", "Observed trade-off"],
            [
                ["FCFS", "Arrival fairness", "Critical mean added wait 110.5 min"],
                [
                    "Acuity",
                    "Clinical severity",
                    "Lowest safety delay; lower throughput",
                ],
                ["SJF-like", "Short jobs", "15 completed; critical delay 115 min"],
                ["Waiting", "Anti-starvation", "Same order as FCFS in this fixture"],
                ["Acuity + wait", "Mixed objective", "Middle safety/throughput result"],
                [
                    "PatientTriage",
                    "Safety + context + monitoring",
                    "Static tie plus dynamic governance features",
                ],
            ],
            [31 * mm, 53 * mm, 90 * mm],
        ),
        P(
            "This is operational evidence, not clinical validation. The strongest defensible claim is a complete dynamic and governable workflow, not universal numerical superiority."
        ),
    ]

    story += section("Scalability and production path", "09")
    story += [
        Image(str(charts["scale"]), width=174 * mm, height=76 * mm),
        table(
            ["Patients", "Mean", "P95", "Scope"],
            [
                ["20", "0.711 ms", "1.036 ms", "Normal demo"],
                ["60", "1.580 ms", "1.803 ms", "3x surge"],
                ["180", "4.745 ms", "5.394 ms", "Scale probe"],
            ],
            [28 * mm, 31 * mm, 31 * mm, 84 * mm],
        ),
        P(
            "These are local in-process measurements after warm-up and exclude network, persistence, identity, concurrent users, and telemetry. Production evolution: stateless replicas, managed PostgreSQL, durable event ingestion, centralized immutable logs, OIDC, secrets, observability, backups, and tested recovery."
        ),
    ]

    story += section("Security, privacy, and audit", "10")
    story += [
        P("Prototype protections:"),
        bullet(
            "Synthetic identifiers only; no names, addresses, phone numbers, or government IDs."
        ),
        bullet(
            "Pydantic validation for ranges, formats, and timezone-aware timelines."
        ),
        bullet("Least-privilege API permissions by role."),
        bullet("Mandatory override reason and versioned audit events."),
        bullet("Hash chain detects event modification."),
        P("Production minimums:"),
        bullet(
            "Hospital SSO/OIDC, MFA where appropriate, short sessions, and access review."
        ),
        bullet(
            "Encryption, key management, retention/deletion policy, backup, and recovery exercises."
        ),
        bullet(
            "Threat modeling, dependency/vulnerability management, penetration testing, and incident response."
        ),
        bullet(
            "Provenance, idempotency, source/ingestion timestamps, and site-specific data minimization."
        ),
    ]

    story += section("Regulatory planning map", "11")
    story += [
        table(
            ["Market", "Primary linkage", "Engineering consequence"],
            [
                [
                    "US",
                    "HIPAA Security Rule where applicable; FDA CDS guidance and classification analysis",
                    "Safeguards, intended-use control, human review, device determination",
                ],
                [
                    "UK",
                    "UK GDPR health data; MHRA SaMD; NHS DCB0129/DCB0160; DSPT",
                    "Privacy impact, clinical safety case, deployment acceptance, cyber assurance",
                ],
                [
                    "EU",
                    "GDPR; MDR/MDCG software classification; EU AI Act risk framework",
                    "Qualification/classification, risk management, data governance, oversight, monitoring",
                ],
            ],
            [23 * mm, 73 * mm, 78 * mm],
        ),
        callout(
            "Regulatory classification follows intended use, claims, users, and deployment. The current package is a synthetic research prototype and makes no compliance or approval claim.",
            RED,
        ),
        P(
            "Before a real pilot: classification opinion, hazard log, requirements traceability, human-factors study, data provenance/subgroup evaluation, security evidence, privacy impact assessment, downtime procedure, and independent shadow-mode protocol."
        ),
    ]

    story += section("Blockchain and consensus", "12")
    story += [
        callout("Decision: no blockchain in the MVP.", ORANGE),
        P(
            "The ranking and bedside workflow do not benefit from a ledger. The current hash chain is suitable for a single-hospital prototype. Consider a permissioned ledger only when independent institutions must share audit anchors and cannot accept one operator. Never put directly identifying health data on-chain."
        ),
        table(
            ["Option", "Fault model", "Fit"],
            [
                [
                    "Hash chain",
                    "Detects rewriting when monitored/anchored",
                    "Recommended now",
                ],
                [
                    "Fabric Raft",
                    "Crash-fault tolerant",
                    "Trusted consortium with known members",
                ],
                [
                    "Fabric SmartBFT",
                    "Byzantine-fault tolerant",
                    "Multi-owner threat model; added overhead",
                ],
                [
                    "Public PoW/PoS",
                    "Open adversarial membership",
                    "Reject for privacy, governance, cost, latency",
                ],
            ],
            [35 * mm, 66 * mm, 73 * mm],
        ),
    ]

    story += section("Business proposal and pilot", "13")
    story += [
        P(
            "Target buyers are district/state hospitals, hospital networks, emergency clinical leadership, and quality/safety teams. The commercial path is a fixed discovery and shadow pilot, followed only after evidence gates by an annual site subscription and optional managed support."
        ),
        table(
            ["Weeks", "Work", "Exit evidence"],
            [
                [
                    "1-2",
                    "Workflow, intended use, hazards, local parameters",
                    "Signed scope and safety owner",
                ],
                [
                    "3-5",
                    "Identity, interface, environment, localization",
                    "Authorization and integration evidence",
                ],
                ["6-8", "Silent shadow operation", "No effect on live care"],
                [
                    "9-10",
                    "Human factors, load, downtime, security",
                    "Exercises passed; findings triaged",
                ],
                ["11-12", "Independent evaluation and go/no-go", "Governance decision"],
            ],
            [20 * mm, 77 * mm, 77 * mm],
        ),
        P(
            "Stop criteria include unsafe ranking, stale-data blindness, excessive false alerts, identity failure, or inability to recover to manual workflow. Success measures include high-risk review delay, overdue reassessment, alert acknowledgement, overrides, latency, recovery, usability, and subgroup/missing-data behavior."
        ),
    ]

    story += section("Techno-economics", "14")
    story += [
        Image(str(charts["cost"]), width=174 * mm, height=74 * mm),
        P(
            "Illustrative cloud ranges use USD 1 = INR 96 on 25 August 2026. A small shadow pilot is planned at $180-$650 per month; a single-site high-availability production case at $900-$2,800. Use a current regional cloud calculator before procurement."
        ),
        table(
            ["Pilot workstream", "INR lakh range"],
            [
                ["Clinical safety and governance", "5-12"],
                ["Product and human factors", "3-6"],
                ["Backend, identity, integration", "8-16"],
                ["Security and compliance", "4-10"],
                ["Verification and validation", "4-8"],
                ["Training/change/contingency", "4-10"],
                ["Total one-time pilot delivery", "28-62"],
            ],
            [120 * mm, 54 * mm],
        ),
        P(
            "Ranges exclude taxes, clinical devices, EHR vendor/interface fees, legal advice, migration, and 24x7 staffing. They are not a quote, budget approval, savings estimate, or ROI promise."
        ),
    ]

    story += section("SWOT and strategic response", "15")
    story += [
        table(
            ["Strengths", "Weaknesses"],
            [
                [
                    "Safety floors, dynamic context, override, failure fallback",
                    "Illustrative model; no clinical validation",
                ],
                [
                    "Five least-privilege views and clear non-ERP scope",
                    "Prototype state and demo identity are process-local",
                ],
                [
                    "Reproducible baselines, scale data, and tests",
                    "Synthetic labels cannot prove efficacy/fairness",
                ],
            ],
            [87 * mm, 87 * mm],
        ),
        Spacer(1, 4 * mm),
        table(
            ["Opportunities", "Threats"],
            [
                [
                    "Governed district-hospital shadow pilot",
                    "Regulatory scope expansion and liability",
                ],
                [
                    "FHIR/EHR adapter without replacing source systems",
                    "Automation bias, alert fatigue, poor data quality",
                ],
                [
                    "Multi-site operational learning",
                    "Cyberattack, downtime, vendor/integration lock-in",
                ],
            ],
            [87 * mm, 87 * mm],
        ),
        P(
            "Strategic response: keep scope narrow, run shadow mode first, publish limitations, require clinician control, localize parameters through governance, and treat integration, security, clinical validation, and human factors as first-class product work."
        ),
    ]

    story += section("Verification and edge cases", "16")
    story += [
        callout(
            "159 automated tests passed with 96.19% coverage at the implementation checkpoint.",
            GREEN,
        ),
        P("The suite covers:"),
        bullet(
            "Empty, single, tied, and large synthetic queues; probability normalization and numerical stability."
        ),
        bullet(
            "Safety floors, pediatric/geriatric boundaries, zero history, ambiguity, missing/stale data, future/out-of-order times."
        ),
        bullet(
            "Deterioration, normal and 3x surge, model failure, new arrivals during fallback, and override safety conflicts."
        ),
        bullet(
            "Hash integrity and tamper detection, role denial paths, malformed hospital profiles, and API validation."
        ),
        bullet(
            "Empty/normal/surge bed boards, pharmacy/blood acknowledgement, all six baselines, and scale validation."
        ),
        P(
            "The final package also runs Ruff, formatting check, dependency check, wheel build, API smoke tests, Streamlit runtime checks, PDF/PPTX rendering inspection, and archive verification."
        ),
    ]

    story += section("Limitations and next decision", "17")
    story += [
        bullet(
            "Thresholds and coefficients are illustrative and not clinically learned or approved."
        ),
        bullet(
            "Confidence is a transparent data-quality heuristic, not outcome probability."
        ),
        bullet("Synthetic expected labels are not medical ground truth."),
        bullet("The benchmark is non-preemptive and uses illustrative service times."),
        bullet(
            "No live EHR, device, lab, pharmacy, blood-bank, ADT, or identity integration is included."
        ),
        bullet(
            "Passing software tests does not establish clinical safety, fairness, effectiveness, or compliance."
        ),
        Spacer(1, 5 * mm),
        callout(
            "Recommended next decision: approve a scoped, independently governed shadow-pilot design - not live clinical deployment.",
            BLUE,
        ),
    ]

    story += section("Primary references", "18")
    references = [
        "Indian Public Health Standards portal - https://iphs.mohfw.gov.in/",
        "MoHFW major trauma standard treatment guidance - https://clinicalestablishments.mohfw.gov.in/sites/default/files/standard-treatment-guidelines/9451.pdf",
        "NHS England model emergency department - https://www.england.nhs.uk/long-read/the-model-emergency-department-high-performing-urgent-and-emergency-care-pathways/",
        "US HHS HIPAA Security Rule - https://www.hhs.gov/hipaa/for-professionals/security/laws-regulations/index.html",
        "US FDA Clinical Decision Support Software - https://www.fda.gov/regulatory-information/search-fda-guidance-documents/clinical-decision-support-software",
        "UK MHRA software and AI as a medical device - https://www.gov.uk/government/publications/software-and-artificial-intelligence-ai-as-a-medical-device/software-and-artificial-intelligence-ai-as-a-medical-device",
        "UK ICO special-category data - https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/lawful-basis/special-category-data/what-is-special-category-data/",
        "NHS digital clinical safety assurance - https://www.england.nhs.uk/long-read/digital-clinical-safety-assurance/",
        "European Commission medical-device guidance - https://health.ec.europa.eu/medical-devices-sector/new-regulations/guidance-mdcg-endorsed-documents-and-other-guidance_en",
        "EU AI Act risk framework - https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai",
        "Hyperledger Fabric ordering and BFT documentation - https://hyperledger-fabric.readthedocs.io/",
        "AWS Fargate, RDS PostgreSQL, ElastiCache, and CloudWatch pricing - https://aws.amazon.com/pricing/",
        "RBI reference-rate data - https://rbi.org.in/Scripts/BS_NSDPDisplay.aspx?param=4",
    ]
    story.extend(bullet(item) for item in references)
    story += [
        Spacer(1, 6 * mm),
        P(
            "This report is a technical and business planning artifact. It is not legal, medical, financial, or procurement advice.",
            "small",
        ),
    ]

    ReportDoc(OUTPUT).build(story)
    return OUTPUT


if __name__ == "__main__":
    print(build())
