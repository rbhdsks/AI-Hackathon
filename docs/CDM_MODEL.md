# Context-Dependent Model

## Why CDM replaces BTL

BTL gives each item one latent score and uses score differences for pairwise probability. That is useful when item strength is assumed to be stable. The Phase 2 story requires a patient's relative priority to react to the current waiting set. A Context-Dependent Model includes explicit interactions with that set.

This implementation has no BTL compatibility layer. The model class is `FeatureContextDependentModel` in `src/patient_triage/models/cdm.py`.

## Model

For the seven-dimensional feature vector \(x_i\),

\[
b_i=\alpha+\beta^\top x_i
\]

is the patient-only base utility. For more than one waiting patient,

\[
c_i(S)=x_i^\top W\left(\frac{1}{|S|-1}\sum_{j\ne i}x_j\right)
\]

is the context effect. The total utility is

\[
U_i(S)=b_i+c_i(S).
\]

The contextual choice probability is a stable softmax:

\[
P(i\mid S)=\frac{\exp(U_i(S)-U_{\max})}{\sum_k\exp(U_k(S)-U_{\max})}.
\]

Subtracting \(U_{\max}\) changes neither probability nor ordering and prevents overflow.

## Features

Every input is bounded to \([0,1]\):

| Feature | Meaning |
|---|---|
| `physiology_risk` | Deviation of recorded vitals from illustrative age-aware ranges |
| `symptom_risk` | Maximum transparent weight among standardized symptom categories |
| `pain` | Recorded 0–10 pain divided by ten |
| `waiting` | Waiting time relative to normal or surge scale |
| `deterioration` | Increase from previous to current physiology risk |
| `uncertainty` | Missing measurements, zero history, ambiguity, and missing pain |
| `vulnerability` | Pediatric/geriatric age-group adjustment |

Expected synthetic acuity and scenario tags are excluded.

## Interaction matrix

The non-zero prototype interactions are deliberately visible:

| Patient feature | Queue-context feature | Purpose in the demo |
|---|---|---|
| physiology | physiology | Reflect the surrounding physiology profile |
| physiology | waiting | Connect physiological concern with queue burden |
| symptom | physiology | Let symptom concern respond to surrounding physiology |
| waiting | waiting | Increase distinction among long-waiting patients during backlog |
| deterioration | physiology | Emphasize a worsening patient within the current severity context |
| uncertainty | physiology | Bias toward review when evidence is incomplete in a risky context |
| vulnerability | symptom | Activate age-aware context interaction |

These are software-demonstration coefficients, not fitted or clinically approved parameters.

## Safety constraint

CDM output is not the first sort key. Final ordering is:

```text
acuity level
then descending CDM utility
then arrival time
then patient identifier
```

Safety rules and the patient-level urgency model determine acuity. Therefore a high contextual utility cannot move a lower-acuity patient above a critical safety-floor patient.

## Edge behavior

| Input | Behavior |
|---|---|
| Empty matrix | Four empty arrays |
| One patient | Zero context effect and probability 1 |
| Identical patients | Equal probabilities; later tie-break is deterministic |
| Non-finite value | Reject with `ValueError` and activate service fallback |
| Wrong feature dimension | Reject with `ValueError` |
| Very large finite utilities | Stable softmax remains finite |

## Training path

This prototype uses inspected fixed coefficients so the mechanism is easy to explain. A later research version could estimate \(\beta\) and \(W\) from governance-approved historical clinician choices using regularized maximum likelihood. It would need train/validation separation, temporal evaluation, subgroup analysis, calibration, distribution-shift monitoring, versioned data lineage, and independent clinical validation.
