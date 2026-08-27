# Role-based dashboards and permissions

## Prototype identity boundary

The dashboard sends an `X-Demo-Role` header so judges can switch views. This demonstrates authorization boundaries only. It is not authentication. A production deployment requires hospital SSO or OIDC, verified identities, short sessions, device and network policy, least privilege, access reviews, and security-event monitoring.

## Permission matrix

| Capability | Nurse | Doctor | Pharmacy | Administration | Blood bank |
|---|:---:|:---:|:---:|:---:|:---:|
| Facility profile - read | Yes | Yes | Yes | Yes | Yes |
| Patient summary - read | Yes | Yes | No | No | No |
| Queue - read | Yes | Yes | No | No | No |
| 18-bed projection - read | Yes | Yes | No | Yes | No |
| Intake - write | Yes | Yes | No | No | No |
| Vitals/reassessment - write | Yes | Yes | No | No | No |
| Queue override - write | No | Yes | No | No | No |
| Disposition - write | No | Yes | No | No | No |
| Pharmacy readiness - read | No | Yes | Yes | No | No |
| Pharmacy readiness - acknowledge | No | No | Yes | No | No |
| Blood readiness - read | No | Yes | No | No | Yes |
| Blood readiness - acknowledge | No | No | No | No | Yes |
| De-identified analytics - read | No | No | No | Yes | No |
| Audit - read | No | Yes | No | Yes | No |
| Scenario control - write | No | No | No | Yes | No |

## Views

### Nurse

- Bed-wise and patient-wise views.
- Live queue, confidence, missing information, monitoring state, and recommended reassessment.
- Synthetic deterioration action.
- No override, audit, pharmacy, or blood-bank write access.

### Doctor

- Complete queue and bed view.
- Patient explanation and uncertainty.
- Clinician override with mandatory reason.
- Read-only readiness context and audit trail.
- Disposition API permission.

### Pharmacy

- Only medication-readiness signals needed for the current emergency queue.
- Can acknowledge a signal.
- Cannot see the full patient record or queue.

### Blood bank

- Only transfusion-readiness signals derived from severe bleeding, shock signals, or critical trauma.
- Can acknowledge a signal.
- Cannot see the full patient record or queue.

### Administration

- De-identified capacity, staffing, occupancy, simulation controls, baseline evaluation, and audit.
- Cannot see full patient records or make clinical queue changes.

## Explicit non-ERP boundary

The bed map is a read model projected from the current synthetic queue. It is not a bed master. Pharmacy and blood-bank views do not perform stock accounting, ordering, cross-matching, dispensing, procurement, invoicing, or billing. PatientTriage.ai coordinates emergency prioritization and readiness; it does not replace a hospital information system or ERP.
