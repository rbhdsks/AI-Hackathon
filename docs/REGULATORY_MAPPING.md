# US, UK, and European regulatory linkage

This is a planning map, not legal advice or a compliance claim. Classification depends on intended use, claims, deployment context, model behavior, and local interpretation. The current package is a synthetic research prototype and must not be used for patient care.

## Cross-market control map

| Control area | United States | United Kingdom | European Union | Product implication |
|---|---|---|---|---|
| Health-data protection | HIPAA Security Rule where a covered entity/business associate relationship applies | UK GDPR special-category health data and Data Protection Act context | GDPR special-category health data | Minimize identifiers, encrypt, control access, log access, define retention and processor roles |
| Clinical decision software | FDA Clinical Decision Support Software guidance and device-law analysis | MHRA software/AI as a medical device guidance | MDR/IVDR software qualification and MDCG classification guidance | Freeze intended use, avoid diagnostic claims, maintain human review, determine device status before pilot |
| AI governance | FDA quality and transparency expectations depend on classification | MHRA programme plus clinical-safety and data-protection obligations | EU AI Act risk framework may interact with MDR/IVDR | Maintain risk management, model/version records, data governance, monitoring, incident process, and human oversight |
| Health IT clinical safety | Organization-specific governance | DCB0129 for manufacturers and DCB0160 for deploying organizations in NHS use | National deployment requirements plus MDR/AI Act where applicable | Create a hazard log, clinical safety case, accountable officers, deployment acceptance criteria, and change control |
| Cyber assurance | HIPAA safeguards plus sector and contractual controls | NHS Data Security and Protection Toolkit where applicable | GDPR security plus device cybersecurity guidance | SSO, least privilege, encryption, backup, vulnerability management, audit, recovery tests |

## Intended-use wording for the prototype

Acceptable prototype wording:

> A clinician-controlled operational coordination aid that recommends review order for synthetic emergency-department scenarios, shows uncertainty and missing information, and allows override.

Avoid:

- diagnosing disease;
- guaranteeing clinical outcomes;
- autonomously making treatment decisions;
- claiming regulatory approval;
- using the synthetic benchmark as clinical validation.

## Evidence required before a real pilot

1. Final intended-use and user population statement.
2. Jurisdiction-specific classification opinion.
3. Clinical risk management file and hazard log.
4. Requirements-to-test traceability.
5. Human-factors and alarm-fatigue evaluation.
6. Dataset provenance, subgroup analysis, calibration, and drift plan.
7. Security architecture, threat model, penetration test, recovery exercise, and supplier review.
8. Privacy impact assessment, lawful basis analysis, minimization, retention, and data-subject workflow.
9. Hospital integration, downtime, manual fallback, and incident playbooks.
10. Shadow-mode protocol with independent clinical oversight and pre-agreed stop criteria.

## Primary sources

- US HHS HIPAA Security Rule: https://www.hhs.gov/hipaa/for-professionals/security/laws-regulations/index.html
- US FDA Clinical Decision Support Software guidance: https://www.fda.gov/regulatory-information/search-fda-guidance-documents/clinical-decision-support-software
- UK MHRA software and AI as a medical device: https://www.gov.uk/government/publications/software-and-artificial-intelligence-ai-as-a-medical-device/software-and-artificial-intelligence-ai-as-a-medical-device
- UK ICO special-category data guidance: https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/lawful-basis/special-category-data/what-is-special-category-data/
- NHS England digital clinical safety assurance: https://www.england.nhs.uk/long-read/digital-clinical-safety-assurance/
- NHS Data Security and Protection Toolkit: https://www.dsptoolkit.nhs.uk/
- European Commission medical-device guidance: https://health.ec.europa.eu/medical-devices-sector/new-regulations/guidance-mdcg-endorsed-documents-and-other-guidance_en
- MDCG software qualification/classification update: https://health.ec.europa.eu/latest-updates/update-mdcg-2019-11-rev1-qualification-and-classification-software-regulation-eu-2017745-and-2025-06-17_en
- EU AI Act framework: https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai
