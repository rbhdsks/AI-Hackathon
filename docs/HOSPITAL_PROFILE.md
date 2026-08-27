# District hospital simulation profile

## Purpose

The prototype needs a concrete operating context, but it must not imply that one staffing pattern fits every district hospital. The active profile is therefore a configurable simulation fixture in `configs/district_hospital.json`, not a normative standard.

## Active assumptions

| Parameter | Demonstration value |
|---|---:|
| Hospital level | District |
| Catchment population | 500,000 |
| Total hospital beds | 200 |
| Emergency-department care spaces | 18 |
| Treatment teams | 4 |
| Normal shift arrivals | 20 |
| Surge shift arrivals | 60 |
| Simulation start | 08:00 |
| Simulation end | 20:00 |

### Emergency zones

| Zone | Care spaces |
|---|---:|
| Resuscitation | 3 |
| Acute care | 9 |
| Observation | 6 |

### Illustrative shift staffing

| Role | Count |
|---|---:|
| Emergency physicians | 3 |
| Resident doctors | 4 |
| Triage nurses | 2 |
| Staff nurses | 12 |
| Pharmacists | 1 |
| Blood-bank technicians | 1 |
| Administrators | 1 |

## How to localize it

Before any shadow pilot, a hospital owner must replace the values using its approved bed register, roster, historical arrival distribution, treatment-area layout, escalation policies, and locally agreed reassessment intervals. Changes to zone capacity are validated so their sum remains equal to the configured emergency capacity.

The infrastructure model is deliberately separated from the ranking model. It can therefore represent a ward, district, state, or regional site without changing the safety rules or API contract.

## Reference context

The Indian Public Health Standards portal provides a national framework for public-facility planning, while emergency operations still require locally approved procedures. NHS England's model emergency department is also used as a process-design reference for around-the-clock flow, initial assessment, demand-capacity planning, and digital support; it is not treated as an Indian staffing standard.

Sources:

- https://iphs.mohfw.gov.in/
- https://www.england.nhs.uk/long-read/the-model-emergency-department-high-performing-urgent-and-emergency-care-pathways/
- https://clinicalestablishments.mohfw.gov.in/sites/default/files/standard-treatment-guidelines/9451.pdf
