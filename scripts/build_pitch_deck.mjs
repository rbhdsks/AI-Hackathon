import fs from "node:fs/promises";

const artifactToolPath = `${process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES}/@oai/artifact-tool/dist/artifact_tool.mjs`;
const { Presentation, PresentationFile } = await import(artifactToolPath);

const ROOT = new URL("..", import.meta.url).pathname.replace(/\/$/, "");
const OUT = `${ROOT}/output/presentation`;
const TMP = `${ROOT}/tmp/presentation`;
const LOGO = `${ROOT}/assets/branding/patienttriage-logo.png`;

const C = {
  navy: "#062B54",
  blue: "#0878E8",
  cyan: "#10BFE0",
  teal: "#10B8A6",
  green: "#16A34A",
  amber: "#F59E0B",
  orange: "#F97316",
  red: "#EF233C",
  ink: "#132238",
  muted: "#5F7085",
  pale: "#F4F8FC",
  line: "#D7E4EF",
  white: "#FFFFFF",
  slate: "#718096",
};

function addText(slide, text, position, style = {}, name) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    name,
    position,
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  shape.text = text;
  shape.text.style = {
    fontFamily: "Aptos",
    fontSize: 20,
    color: C.ink,
    ...style,
  };
  return shape;
}

function addBox(slide, position, fill = C.white, line = C.line, radius = "rounded-xl", name) {
  return slide.shapes.add({
    geometry: "roundRect",
    name,
    position,
    fill,
    line: { style: "solid", fill: line, width: 1 },
    borderRadius: radius,
  });
}

function addRule(slide, left, top, width, fill = C.cyan, height = 3) {
  return slide.shapes.add({
    geometry: "rect",
    position: { left, top, width, height },
    fill,
    line: { style: "solid", fill, width: 0 },
  });
}

function header(slide, title, eyebrow, section) {
  slide.background.fill = C.white;
  addText(slide, eyebrow.toUpperCase(), { left: 72, top: 42, width: 650, height: 24 }, {
    fontSize: 13, bold: true, color: C.blue, letterSpacing: 1.6,
  }, "eyebrow");
  addText(slide, title, { left: 72, top: 78, width: 1110, height: 60 }, {
    fontSize: 36, bold: true, color: C.navy,
  }, "slide-title");
  addRule(slide, 72, 145, 1136, C.cyan, 3);
  addText(slide, section, { left: 1120, top: 46, width: 88, height: 20 }, {
    fontSize: 12, bold: true, color: C.muted, alignment: "right",
  }, "section-number");
}

function footer(slide) {
  addText(slide, "PatientTriage.ai  |  Synthetic prototype  |  Not for patient care", {
    left: 72, top: 680, width: 750, height: 18,
  }, { fontSize: 11, color: C.muted }, "footer");
}

function notes(slide, body, sources = []) {
  const sourceBlock = sources.length
    ? `\n\n[Sources]\n${sources.map((item) => `- ${item}`).join("\n")}\n[/Sources]`
    : "";
  slide.speakerNotes.textFrame.setText(`${body}${sourceBlock}`);
  slide.speakerNotes.setVisible(true);
}

async function imageBytes(path) {
  const bytes = await fs.readFile(path);
  return bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
}

function metric(slide, value, label, left, top, color = C.blue) {
  addBox(slide, { left, top, width: 190, height: 118 }, C.pale, C.line, "rounded-xl");
  addText(slide, value, { left: left + 16, top: top + 18, width: 158, height: 45 }, {
    fontSize: 30, bold: true, color, alignment: "center",
  });
  addText(slide, label, { left: left + 12, top: top + 72, width: 166, height: 28 }, {
    fontSize: 15, color: C.muted, alignment: "center",
  });
}

function stage(slide, number, title, copy, left, top, color) {
  slide.shapes.add({
    geometry: "ellipse",
    position: { left, top, width: 62, height: 62 },
    fill: color,
    line: { style: "solid", fill: color, width: 0 },
  });
  addText(slide, String(number), { left, top: top + 10, width: 62, height: 38 }, {
    fontSize: 24, bold: true, color: C.white, alignment: "center",
  });
  addText(slide, title, { left: left + 78, top: top - 2, width: 235, height: 30 }, {
    fontSize: 20, bold: true, color: C.navy,
  });
  addText(slide, copy, { left: left + 78, top: top + 31, width: 260, height: 58 }, {
    fontSize: 15, color: C.muted,
  });
}

async function main() {
  await fs.mkdir(OUT, { recursive: true });
  await fs.mkdir(TMP, { recursive: true });
  const logo = await imageBytes(LOGO);
  const deck = Presentation.create({ slideSize: { width: 1280, height: 720 } });

  // 1 - Cover
  {
    const slide = deck.slides.add();
    slide.background.fill = C.white;
    slide.shapes.add({
      geometry: "rect",
      position: { left: 0, top: 0, width: 1280, height: 24 },
      fill: C.navy,
      line: { style: "solid", fill: C.navy, width: 0 },
    });
    slide.images.add({
      blob: logo,
      contentType: "image/png",
      alt: "PatientTriage.ai logo",
      fit: "contain",
      position: { left: 78, top: 72, width: 520, height: 292 },
    });
    addText(slide, "A safer dynamic queue for the district emergency department", {
      left: 660, top: 104, width: 500, height: 220,
    }, { fontSize: 40, bold: true, color: C.navy }, "cover-title");
    addText(slide, "Safety floors. Context-aware ranking. Visible uncertainty. Clinician control.", {
      left: 660, top: 348, width: 500, height: 72,
    }, { fontSize: 22, color: C.muted }, "cover-subtitle");
    addBox(slide, { left: 660, top: 446, width: 500, height: 92 }, "#EAFBF8", C.teal, "rounded-xl");
    addText(slide, "Focused scope: emergency coordination, not an ERP or autonomous clinical system.", {
      left: 688, top: 467, width: 444, height: 52,
    }, { fontSize: 20, bold: true, color: C.navy, alignment: "center" });
    addText(slide, "Phase 2 hackathon package  |  Version 0.3.0  |  25 August 2026", {
      left: 660, top: 582, width: 500, height: 24,
    }, { fontSize: 15, color: C.blue });
    footer(slide);
    notes(slide, "Open with the narrow positioning. State that all patients and hospital parameters are synthetic. The decision requested at the end is approval to design a shadow pilot, not live use.");
  }

  // 2 - Problem
  {
    const slide = deck.slides.add();
    header(slide, "The emergency queue changes after initial triage", "The problem", "02");
    const steps = [
      ["Arrival order", "is not clinical urgency", C.slate],
      ["Acuity alone", "can ignore time and uncertainty", C.orange],
      ["Waiting time", "can conflict with a new emergency", C.amber],
      ["Static scores", "miss deterioration and stale data", C.red],
    ];
    steps.forEach(([a, b, color], i) => {
      const top = 188 + i * 103;
      slide.shapes.add({
        geometry: "ellipse",
        position: { left: 88, top, width: 58, height: 58 },
        fill: color,
        line: { style: "solid", fill: color, width: 0 },
      });
      addText(slide, String(i + 1), { left: 88, top: top + 10, width: 58, height: 36 }, {
        fontSize: 22, bold: true, color: C.white, alignment: "center",
      });
      addText(slide, a, { left: 168, top: top - 3, width: 275, height: 34 }, {
        fontSize: 23, bold: true, color: C.navy,
      });
      addText(slide, b, { left: 168, top: top + 32, width: 320, height: 30 }, {
        fontSize: 17, color: C.muted,
      });
    });
    addBox(slide, { left: 585, top: 192, width: 555, height: 384 }, C.pale, C.line, "rounded-2xl");
    addText(slide, "The operational question", { left: 625, top: 224, width: 470, height: 32 }, {
      fontSize: 18, bold: true, color: C.blue, alignment: "center",
    });
    addText(slide, "Who needs review next - and what changed since we last looked?", {
      left: 635, top: 286, width: 450, height: 124,
    }, { fontSize: 34, bold: true, color: C.navy, alignment: "center" });
    addText(slide, "The answer must include evidence, confidence, missing information, and a safe human action.", {
      left: 640, top: 442, width: 440, height: 72,
    }, { fontSize: 19, color: C.muted, alignment: "center" });
    footer(slide);
    notes(slide, "Explain why no scalar policy wins every objective. The product goal is coordination under change, not a one-time severity score.", [
      "https://www.england.nhs.uk/long-read/the-model-emergency-department-high-performing-urgent-and-emergency-care-pathways/",
      "https://clinicalestablishments.mohfw.gov.in/sites/default/files/standard-treatment-guidelines/9451.pdf",
    ]);
  }

  // 3 - Product boundary
  {
    const slide = deck.slides.add();
    header(slide, "A narrow product boundary is a safety feature", "What we are building", "03");
    addBox(slide, { left: 86, top: 188, width: 500, height: 400 }, "#EAFBF8", C.teal, "rounded-2xl");
    addText(slide, "PatientTriage.ai coordinates", { left: 126, top: 220, width: 420, height: 38 }, {
      fontSize: 25, bold: true, color: C.navy,
    });
    [
      "Review order and reassessment",
      "Bed-wise and patient-wise visibility",
      "Uncertainty and deterioration",
      "Support-readiness signals",
      "Override and audit evidence",
    ].forEach((item, i) => {
      addText(slide, `+  ${item}`, { left: 130, top: 286 + i * 52, width: 410, height: 30 }, {
        fontSize: 19, bold: i === 0, color: C.ink,
      });
    });
    addBox(slide, { left: 670, top: 188, width: 500, height: 400 }, "#FFF1F3", C.red, "rounded-2xl");
    addText(slide, "PatientTriage.ai does not replace", { left: 710, top: 220, width: 420, height: 38 }, {
      fontSize: 25, bold: true, color: C.navy,
    });
    [
      "Clinical judgement or diagnosis",
      "EHR / hospital information system",
      "Bed-master or ADT authority",
      "Pharmacy / blood inventory",
      "Billing, procurement, payroll, ERP",
    ].forEach((item, i) => {
      addText(slide, `-  ${item}`, { left: 714, top: 286 + i * 52, width: 410, height: 30 }, {
        fontSize: 19, bold: i === 0, color: C.ink,
      });
    });
    footer(slide);
    notes(slide, "Use this slide to answer the 'ERP software banauna khojya haina' concern directly. The narrow boundary keeps the demo credible and makes role permissions understandable.");
  }

  // 4 - District constraints
  {
    const slide = deck.slides.add();
    header(slide, "Concrete district constraints make the simulation believable", "Operating context", "04");
    metric(slide, "500k", "Illustrative catchment", 84, 190, C.blue);
    metric(slide, "200", "Hospital beds", 292, 190, C.navy);
    metric(slide, "18", "ED care spaces", 500, 190, C.teal);
    metric(slide, "4", "Treatment teams", 708, 190, C.orange);
    metric(slide, "20 / 60", "Normal / 3x surge", 916, 190, C.red);
    addText(slide, "Day demonstration shift", { left: 96, top: 358, width: 330, height: 34 }, {
      fontSize: 24, bold: true, color: C.navy,
    });
    addText(slide, "08:00 start  ->  20:00 end", { left: 96, top: 402, width: 330, height: 30 }, {
      fontSize: 20, color: C.blue,
    });
    addText(slide, "Illustrative clinical staffing", { left: 470, top: 358, width: 360, height: 34 }, {
      fontSize: 24, bold: true, color: C.navy,
    });
    addText(slide, "3 physicians  |  4 residents\n2 triage nurses  |  12 staff nurses", {
      left: 470, top: 402, width: 360, height: 72,
    }, { fontSize: 19, color: C.ink });
    addText(slide, "18 spaces by zone", { left: 878, top: 358, width: 300, height: 34 }, {
      fontSize: 24, bold: true, color: C.navy,
    });
    addText(slide, "3 resuscitation\n9 acute care\n6 observation", {
      left: 878, top: 402, width: 300, height: 92,
    }, { fontSize: 19, color: C.ink });
    addBox(slide, { left: 84, top: 536, width: 1094, height: 76 }, "#FFF8E7", C.amber, "rounded-xl");
    addText(slide, "Every value is configurable and illustrative. Replace it with locally approved capacity, roster, arrivals, and escalation policy before a pilot.", {
      left: 112, top: 556, width: 1038, height: 42,
    }, { fontSize: 18, bold: true, color: C.navy, alignment: "center" });
    footer(slide);
    notes(slide, "Do not present these values as an IPHS staffing standard. They are explicit simulation assumptions chosen to make the hackathon story concrete.", [
      "https://iphs.mohfw.gov.in/",
      "Local source: configs/district_hospital.json",
    ]);
  }

  // 5 - Roles
  {
    const slide = deck.slides.add();
    header(slide, "Five users see only the information needed for their job", "Role design", "05");
    const roles = [
      ["N", "Nurse", "Beds + patients + queue", "Intake / vitals", C.teal],
      ["D", "Doctor", "Queue + readiness + audit", "Override / disposition", C.blue],
      ["P", "Pharmacy", "Medication readiness", "Acknowledge only", C.orange],
      ["A", "Administration", "Capacity + analytics", "Scenario control", C.navy],
      ["B", "Blood bank", "Transfusion readiness", "Acknowledge only", C.red],
    ];
    roles.forEach(([letter, role, read, write, color], i) => {
      const left = 78 + i * 236;
      addBox(slide, { left, top: 190, width: 210, height: 380 }, C.white, C.line, "rounded-2xl");
      slide.shapes.add({
        geometry: "ellipse",
        position: { left: left + 65, top: 220, width: 80, height: 80 },
        fill: color,
        line: { style: "solid", fill: color, width: 0 },
      });
      addText(slide, letter, { left: left + 65, top: 235, width: 80, height: 48 }, {
        fontSize: 30, bold: true, color: C.white, alignment: "center",
      });
      addText(slide, role, { left: left + 18, top: 324, width: 174, height: 32 }, {
        fontSize: 22, bold: true, color: C.navy, alignment: "center",
      });
      addText(slide, "READ", { left: left + 24, top: 382, width: 162, height: 22 }, {
        fontSize: 12, bold: true, color: C.muted, alignment: "center",
      });
      addText(slide, read, { left: left + 20, top: 410, width: 170, height: 54 }, {
        fontSize: 16, color: C.ink, alignment: "center",
      });
      addText(slide, "WRITE", { left: left + 24, top: 478, width: 162, height: 22 }, {
        fontSize: 12, bold: true, color: C.muted, alignment: "center",
      });
      addText(slide, write, { left: left + 20, top: 506, width: 170, height: 44 }, {
        fontSize: 16, color: C.ink, alignment: "center",
      });
    });
    addText(slide, "Demo role header today  ->  hospital SSO/OIDC and governed access reviews for production", {
      left: 150, top: 606, width: 980, height: 28,
    }, { fontSize: 18, bold: true, color: C.blue, alignment: "center" });
    footer(slide);
    notes(slide, "Emphasize least privilege. Pharmacy and blood bank cannot see the full queue or patient record. Administration sees de-identified operations, not clinical charts.", ["Local source: configs/rbac.json"]);
  }

  // 6 - Architecture
  {
    const slide = deck.slides.add();
    header(slide, "Safety decides the floor; context refines the order", "Decision architecture", "06");
    const nodes = [
      ["1", "Validated intake", "Ranges, timestamps, missingness", 86, 205, C.navy],
      ["2", "Safety floor", "Explicit red flags cannot be downgraded", 365, 205, C.red],
      ["3", "Urgency + CDM", "Patient signal plus waiting-set context", 644, 205, C.blue],
      ["4", "Monitor + confidence", "Deterioration, stale data, uncertainty", 923, 205, C.teal],
    ];
    nodes.forEach(([num, title, copy, left, top, color], i) => {
      addBox(slide, { left, top, width: 240, height: 190 }, C.white, color, "rounded-2xl");
      slide.shapes.add({
        geometry: "ellipse",
        position: { left: left + 20, top: top + 18, width: 48, height: 48 },
        fill: color,
        line: { style: "solid", fill: color, width: 0 },
      });
      addText(slide, num, { left: left + 20, top: top + 26, width: 48, height: 30 }, {
        fontSize: 18, bold: true, color: C.white, alignment: "center",
      });
      addText(slide, title, { left: left + 24, top: top + 86, width: 192, height: 36 }, {
        fontSize: 21, bold: true, color: C.navy, alignment: "center",
      });
      addText(slide, copy, { left: left + 24, top: top + 132, width: 192, height: 48 }, {
        fontSize: 15, color: C.muted, alignment: "center",
      });
      if (i < nodes.length - 1) {
        addText(slide, "->", { left: left + 244, top: top + 72, width: 36, height: 36 }, {
          fontSize: 28, bold: true, color: C.cyan, alignment: "center",
        });
      }
    });
    addBox(slide, { left: 190, top: 455, width: 900, height: 118 }, C.pale, C.line, "rounded-xl");
    addText(slide, "Final order", { left: 224, top: 477, width: 180, height: 34 }, {
      fontSize: 22, bold: true, color: C.navy,
    });
    addText(slide, "Acuity  ->  CDM utility inside acuity  ->  arrival time  ->  deterministic ID", {
      left: 420, top: 474, width: 630, height: 42,
    }, { fontSize: 21, bold: true, color: C.blue, alignment: "center" });
    addText(slide, "Override remains available and every reason is appended to the tamper-evident audit chain.", {
      left: 250, top: 530, width: 780, height: 28,
    }, { fontSize: 17, color: C.muted, alignment: "center" });
    footer(slide);
    notes(slide, "Explain the key invariant: a context effect can never move a patient across a hard safety floor. This is the technical answer to under-triage risk.", [
      "Local source: docs/LOW_LEVEL_DESIGN.md",
      "Local source: docs/CDM_MODEL.md",
    ]);
  }

  // 7 - Bed board
  {
    const slide = deck.slides.add();
    header(slide, "The 18-bed board makes emergency state visible at a glance", "Nurse experience", "07");
    const states = [
      [C.red, "P01"], [C.red, "P03"], [C.orange, "P07"], [C.amber, "P11"], [C.blue, "P14"], [C.green, "EMPTY"],
      [C.orange, "P05"], [C.amber, "P09"], [C.amber, "P12"], [C.blue, "P16"], [C.slate, "P18"], [C.green, "EMPTY"],
      [C.red, "P04"], [C.orange, "P08"], [C.amber, "P13"], [C.blue, "P17"], [C.slate, "P20"], [C.green, "EMPTY"],
    ];
    states.forEach(([color, patient], index) => {
      const col = index % 6;
      const row = Math.floor(index / 6);
      const left = 152 + col * 158;
      const top = 194 + row * 116;
      addBox(slide, { left, top, width: 136, height: 92 }, color, C.white, "rounded-xl");
      addText(slide, `ED-${String(index + 1).padStart(2, "0")}`, {
        left: left + 10, top: top + 12, width: 116, height: 25,
      }, { fontSize: 16, bold: true, color: C.white, alignment: "center" });
      addText(slide, patient, { left: left + 10, top: top + 48, width: 116, height: 25 }, {
        fontSize: 15, color: C.white, alignment: "center" });
    });
    ["RESUS", "ACUTE", "OBSERVATION"].forEach((label, i) => {
      addText(slide, label, { left: 72, top: 226 + i * 116, width: 72, height: 24 }, {
        fontSize: 13, bold: true, color: C.muted, alignment: "right",
      });
    });
    const legend = [[C.green, "Available"], [C.red, "Critical"], [C.orange, "Emergent"], [C.amber, "Urgent"], [C.blue, "Less urgent"], [C.slate, "Non-urgent"]];
    legend.forEach(([color, label], i) => {
      const left = 142 + i * 170;
      slide.shapes.add({
        geometry: "ellipse", position: { left, top: 566, width: 20, height: 20 }, fill: color,
        line: { style: "solid", fill: color, width: 0 },
      });
      addText(slide, label, { left: left + 28, top: 564, width: 135, height: 24 }, {
        fontSize: 14, color: C.ink,
      });
    });
    addText(slide, "Select a bed for patient detail; switch to patient-wise view for explanations and missing information.", {
      left: 150, top: 617, width: 980, height: 28,
    }, { fontSize: 18, bold: true, color: C.navy, alignment: "center" });
    footer(slide);
    notes(slide, "This is a visual reconstruction of the implemented board, not a screenshot. Point out that color is never the only cue and that the board is an operational projection, not a bed-master.", ["Local source: dashboard/charts.py", "Local source: configs/district_hospital.json"]);
  }

  // 8 - Dynamic story
  {
    const slide = deck.slides.add();
    header(slide, "One demo proves the queue is alive", "Prototype story", "08");
    stage(slide, 1, "Initial queue", "20 synthetic cases with uncertainty and red flags", 78, 196, C.blue);
    stage(slide, 2, "Deterioration", "New observations move a waiting patient upward", 452, 196, C.red);
    stage(slide, 3, "Override", "Doctor moves a patient with a mandatory reason", 826, 196, C.orange);
    stage(slide, 4, "3x surge", "60 patients change pressure and reassessment burden", 78, 414, C.navy);
    stage(slide, 5, "Model failure", "Rules remain active; rows become stale and manual", 452, 414, C.slate);
    stage(slide, 6, "Audit proof", "Verify the hash chain and model version", 826, 414, C.teal);
    addText(slide, "Same patients. New context. New order. Every change is visible.", {
      left: 220, top: 606, width: 840, height: 34,
    }, { fontSize: 23, bold: true, color: C.navy, alignment: "center" });
    footer(slide);
    notes(slide, "Walk through the sequence quickly. The strongest demo moments are the deterioration re-rank, the doctor override, and the visible fallback during simulated CDM failure.", ["Local source: docs/PROTOTYPE_VIDEO_SCRIPT.md"]);
  }

  // 9 - Baselines
  {
    const slide = deck.slides.add();
    header(slide, "The benchmark exposes trade-offs instead of forcing a fake win", "Evidence", "09");
    const categories = ["FCFS", "Acuity", "SJF-like", "Waiting", "Acuity + wait", "PatientTriage"];
    slide.charts.add("bar", {
      position: { left: 78, top: 186, width: 700, height: 390 },
      categories,
      series: [{ name: "Safety-weighted delay", values: [935.5, 690.5, 938.4, 935.5, 795.3, 690.5], fill: C.blue }],
      hasLegend: false,
      dataLabels: { showValue: true, position: "outEnd" },
      yAxis: { majorGridlines: { style: "solid", fill: C.line, width: 1 }, title: "Lower is safer" },
      xAxis: { title: "Normal 20-patient snapshot" },
    });
    addBox(slide, { left: 820, top: 190, width: 370, height: 390 }, C.pale, C.line, "rounded-2xl");
    addText(slide, "What the result means", { left: 855, top: 224, width: 300, height: 38 }, {
      fontSize: 24, bold: true, color: C.navy, alignment: "center",
    });
    addText(slide, "PatientTriage ties acuity priority on this static safety metric.", {
      left: 860, top: 292, width: 290, height: 74,
    }, { fontSize: 21, bold: true, color: C.teal, alignment: "center" });
    addText(slide, "SJF-like completes more short jobs but delays critical care. FCFS protects arrival order, not urgency.", {
      left: 858, top: 392, width: 294, height: 92,
    }, { fontSize: 18, color: C.ink, alignment: "center" });
    addText(slide, "The differentiator is dynamic monitoring, uncertainty, fail-safe operation, permissions, and audited override.", {
      left: 852, top: 500, width: 306, height: 62,
    }, { fontSize: 17, bold: true, color: C.blue, alignment: "center" });
    footer(slide);
    notes(slide, "Be transparent: the proposed method does not win every metric. Its static ordering ties acuity priority in this fixture; its value appears in the dynamic and governance capabilities the baselines do not include.", ["Local source: reports/baseline_benchmark.csv", "Local source: docs/BENCHMARK_REPORT.md"]);
  }

  // 10 - Scale
  {
    const slide = deck.slides.add();
    header(slide, "Measured latency supports a staged path to scale", "Scalability", "10");
    slide.charts.add("line", {
      position: { left: 78, top: 184, width: 610, height: 360 },
      categories: ["20", "60", "180"],
      series: [
        { name: "Mean ms", values: [0.711, 1.58, 4.745], fill: C.blue },
        { name: "P95 ms", values: [1.036, 1.803, 5.394], fill: C.teal },
      ],
      hasLegend: true,
      legend: { position: "bottom" },
      yAxis: { majorGridlines: { style: "solid", fill: C.line, width: 1 }, title: "Rank latency (ms)" },
      xAxis: { title: "Patients in queue" },
    });
    const paths = [
      ["Hackathon", "FastAPI + Streamlit\nIn-memory + SQLite", C.slate],
      ["Shadow pilot", "Stateless API + Postgres\nOIDC + centralized audit", C.blue],
      ["Production", "Durable events + recovery\nObservability + security", C.teal],
      ["Multi-site", "Tenant isolation\nSite configs + regional controls", C.navy],
    ];
    paths.forEach(([title, copy, color], i) => {
      const top = 190 + i * 102;
      addBox(slide, { left: 752, top, width: 420, height: 82 }, C.white, color, "rounded-xl");
      addText(slide, title, { left: 778, top: top + 12, width: 150, height: 28 }, {
        fontSize: 19, bold: true, color: C.navy,
      });
      addText(slide, copy, { left: 940, top: top + 10, width: 205, height: 55 }, {
        fontSize: 15, color: C.muted,
      });
    });
    addBox(slide, { left: 118, top: 592, width: 1040, height: 50 }, "#FFF8E7", C.amber, "rounded-xl");
    addText(slide, "Microbenchmark only - network, database, identity, concurrency, and telemetry are excluded.", {
      left: 150, top: 604, width: 976, height: 26,
    }, { fontSize: 18, bold: true, color: C.navy, alignment: "center" });
    footer(slide);
    notes(slide, "Use the numbers as evidence of implementation efficiency, not a production SLO. Explain that production scale is gated by integration and safety architecture, not just model runtime.", ["Local source: reports/scalability_benchmark.csv", "Local source: docs/SCALABILITY_AND_COST.md"]);
  }

  // 11 - Governance
  {
    const slide = deck.slides.add();
    header(slide, "Governance choices reduce risk before any real pilot", "Regulation and trust", "11");
    const markets = [
      ["US", "HIPAA security\nFDA CDS analysis", C.blue],
      ["UK", "UK GDPR health data\nMHRA + DCB0129/0160", C.teal],
      ["EU", "GDPR + MDR/MDCG\nEU AI Act framework", C.navy],
    ];
    markets.forEach(([title, copy, color], i) => {
      const left = 84 + i * 380;
      addBox(slide, { left, top: 190, width: 340, height: 190 }, C.white, color, "rounded-2xl");
      addText(slide, title, { left: left + 24, top: 220, width: 292, height: 48 }, {
        fontSize: 34, bold: true, color, alignment: "center",
      });
      addText(slide, copy, { left: left + 30, top: 292, width: 280, height: 62 }, {
        fontSize: 19, color: C.ink, alignment: "center",
      });
    });
    addBox(slide, { left: 84, top: 432, width: 1100, height: 150 }, "#FFF8E7", C.orange, "rounded-2xl");
    addText(slide, "Blockchain decision", { left: 120, top: 464, width: 280, height: 38 }, {
      fontSize: 25, bold: true, color: C.navy,
    });
    addText(slide, "No blockchain in the MVP", { left: 420, top: 457, width: 340, height: 48 }, {
      fontSize: 29, bold: true, color: C.orange, alignment: "center",
    });
    addText(slide, "Keep the hash-chained audit. Revisit permissioned Raft or SmartBFT only for a real multi-institution trust problem - never store PHI on-chain.", {
      left: 790, top: 452, width: 350, height: 92,
    }, { fontSize: 16, color: C.ink, alignment: "center" });
    footer(slide);
    notes(slide, "This is a planning map, not a classification or compliance claim. The blockchain answer is deliberately conservative: add distributed consensus only if independent organizations truly need a shared audit anchor.", [
      "https://www.hhs.gov/hipaa/for-professionals/security/laws-regulations/index.html",
      "https://www.fda.gov/regulatory-information/search-fda-guidance-documents/clinical-decision-support-software",
      "https://www.england.nhs.uk/long-read/digital-clinical-safety-assurance/",
      "https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai",
      "https://hyperledger-fabric.readthedocs.io/en/latest/bft_configuration.html",
    ]);
  }

  // 12 - Pilot and costs
  {
    const slide = deck.slides.add();
    header(slide, "A 12-week shadow pilot converts a demo into evidence", "Business and economics", "12");
    const weeks = [
      ["1-2", "Scope + hazards", C.navy],
      ["3-5", "Identity + integration", C.blue],
      ["6-8", "Silent shadow", C.teal],
      ["9-10", "Human factors + load", C.orange],
      ["11-12", "Independent go / no-go", C.red],
    ];
    weeks.forEach(([wk, label, color], i) => {
      const left = 76 + i * 238;
      addBox(slide, { left, top: 188, width: 212, height: 134 }, C.white, color, "rounded-xl");
      addText(slide, `Weeks ${wk}`, { left: left + 16, top: 207, width: 180, height: 28 }, {
        fontSize: 17, bold: true, color,
      });
      addText(slide, label, { left: left + 16, top: 250, width: 180, height: 50 }, {
        fontSize: 20, bold: true, color: C.navy, alignment: "center",
      });
    });
    addBox(slide, { left: 92, top: 386, width: 510, height: 184 }, C.pale, C.line, "rounded-2xl");
    addText(slide, "Illustrative cloud", { left: 126, top: 418, width: 440, height: 34 }, {
      fontSize: 23, bold: true, color: C.navy, alignment: "center",
    });
    addText(slide, "$180-$650 / month", { left: 126, top: 474, width: 440, height: 46 }, {
      fontSize: 32, bold: true, color: C.blue, alignment: "center",
    });
    addText(slide, "Small single-hospital shadow environment", { left: 126, top: 528, width: 440, height: 24 }, {
      fontSize: 15, color: C.muted, alignment: "center",
    });
    addBox(slide, { left: 678, top: 386, width: 510, height: 184 }, "#EAFBF8", C.teal, "rounded-2xl");
    addText(slide, "Illustrative pilot delivery", { left: 712, top: 418, width: 440, height: 34 }, {
      fontSize: 23, bold: true, color: C.navy, alignment: "center",
    });
    addText(slide, "INR 28-62 lakh", { left: 712, top: 474, width: 440, height: 46 }, {
      fontSize: 32, bold: true, color: C.teal, alignment: "center",
    });
    addText(slide, "Clinical safety, product, integration, security, V&V, training", { left: 712, top: 528, width: 440, height: 28 }, {
      fontSize: 15, color: C.muted, alignment: "center",
    });
    addText(slide, "Ranges are planning assumptions, not a quote, savings promise, or ROI claim.", {
      left: 180, top: 606, width: 920, height: 26,
    }, { fontSize: 18, bold: true, color: C.orange, alignment: "center" });
    footer(slide);
    notes(slide, "The pilot is shadow-only and has explicit stop criteria. Costs are order-of-magnitude planning ranges and exclude EHR fees, devices, taxes, legal advice, migration, and 24x7 staffing.", [
      "https://aws.amazon.com/fargate/pricing/",
      "https://aws.amazon.com/rds/postgresql/pricing/",
      "https://aws.amazon.com/cloudwatch/pricing/",
      "https://rbi.org.in/Scripts/BS_NSDPDisplay.aspx?param=4",
      "Local source: configs/cost_assumptions.json",
    ]);
  }

  // 13 - Close
  {
    const slide = deck.slides.add();
    slide.background.fill = C.navy;
    slide.images.add({
      blob: logo,
      contentType: "image/png",
      alt: "PatientTriage.ai logo",
      fit: "contain",
      position: { left: 410, top: 46, width: 460, height: 252 },
    });
    addText(slide, "Approve the next evidence gate - not live deployment", {
      left: 170, top: 326, width: 940, height: 72,
    }, { fontSize: 40, bold: true, color: C.white, alignment: "center" }, "closing-title");
    addText(slide, "A scoped, independently governed district-hospital shadow-pilot design", {
      left: 250, top: 426, width: 780, height: 44,
    }, { fontSize: 24, color: C.cyan, alignment: "center" });
    const asks = ["Clinical safety owner", "Local data + workflow", "Integration sandbox", "Independent evaluation"];
    asks.forEach((item, i) => {
      const left = 126 + i * 270;
      addBox(slide, { left, top: 520, width: 238, height: 74 }, "#0B3B6D", C.blue, "rounded-xl");
      addText(slide, item, { left: left + 14, top: 540, width: 210, height: 34 }, {
        fontSize: 17, bold: true, color: C.white, alignment: "center",
      });
    });
    addText(slide, "Synthetic prototype  |  Not clinically validated  |  Clinician remains in control", {
      left: 270, top: 648, width: 740, height: 24,
    }, { fontSize: 14, color: "#B9D8F3", alignment: "center" });
    notes(slide, "Resolve the opening. Ask for permission and hospital partnership to design a shadow pilot with independent clinical, security, privacy, and human-factors governance. Do not ask for live deployment.");
  }

  for (const [index, slide] of deck.slides.items.entries()) {
    const stem = `slide-${String(index + 1).padStart(2, "0")}`;
    const png = await deck.export({ slide, format: "png", scale: 1 });
    await fs.writeFile(`${TMP}/${stem}.png`, new Uint8Array(await png.arrayBuffer()));
    const layout = await slide.export({ format: "layout" });
    await fs.writeFile(`${TMP}/${stem}.layout.json`, await layout.text());
  }
  const montage = await deck.export({ format: "webp", montage: true, scale: 1 });
  await fs.writeFile(`${TMP}/deck-montage.webp`, new Uint8Array(await montage.arrayBuffer()));
  const pptx = await PresentationFile.exportPptx(deck);
  await pptx.save(`${OUT}/PatientTriage_AI_Hackathon_Pitch.pptx`);
  console.log(`${OUT}/PatientTriage_AI_Hackathon_Pitch.pptx`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
