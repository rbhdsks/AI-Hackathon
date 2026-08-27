# Branding and UI system

## Source asset

The supplied PatientTriage.ai logo is preserved unchanged at `assets/branding/patienttriage-logo.png` and is used in the dashboard, report, deck, and video.

## Palette

| Token | Hex | Use |
|---|---|---|
| Navy | `#062B54` | Primary text, sidebar, clinical authority |
| Blue | `#0878E8` | Primary actions and charts |
| Cyan | `#10BFE0` | Live data accents |
| Teal | `#10B8A6` | Coordination and positive context |
| Green | `#16A34A` | Empty/available bed |
| Amber | `#F59E0B` | Urgent |
| Orange | `#F97316` | Emergent |
| Red | `#EF233C` | Critical and safety warning |
| Slate | `#718096` | Non-urgent/neutral |

Color is never the only cue: every bed also displays an ID, every row includes acuity text, and alerts contain written reasons.

## 18-bed interaction

- Six columns by three rows, grouped by configured zone.
- Green means available; occupied beds use acuity colors.
- Hover shows bed, zone, patient ID, waiting time, and monitoring state.
- Click/select opens the bed detail; a select box is retained as a keyboard-friendly fallback.
- The nurse and doctor can move between bed-wise and patient-wise perspectives.
- Administration sees capacity and occupancy, not full patient records.

## Design guardrails

- Clinical warnings use plain language and remain visible.
- The prototype and non-ERP scope banners appear above every role view.
- Confidence and missing information accompany recommendations.
- Buttons correspond to permitted actions only.
- The dashboard uses current Streamlit `width="stretch"` APIs rather than deprecated width flags.
