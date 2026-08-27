"""HTTP API for the synthetic PatientTriage.ai prototype."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, Header, Query, Request, status
from fastapi.responses import JSONResponse

from patient_triage.api.schemas import (
    AuditVerificationResponse,
    HealthResponse,
    ScenarioResponse,
)
from patient_triage.config import Settings
from patient_triage.data.generator import (
    deteriorated_vitals,
    generate_normal_scenario,
    generate_scenario,
)
from patient_triage.data.repository import InMemoryPatientRepository
from patient_triage.domain.audit import AuditEvent
from patient_triage.domain.enums import (
    CoordinationDomain,
    PatientStatus,
    Permission,
    QueueMode,
    StaffRole,
)
from patient_triage.domain.errors import (
    CoordinationTaskNotFoundError,
    DuplicatePatientError,
    InvalidOverrideError,
    InvalidTimelineError,
    PatientNotFoundError,
    PermissionDeniedError,
)
from patient_triage.domain.hospital import AccessControlMatrix, HospitalProfile
from patient_triage.domain.operations import (
    BedBoard,
    CoordinationTask,
    TaskAcknowledgement,
)
from patient_triage.domain.patient import Patient, VitalSigns
from patient_triage.domain.queue import OverrideRequest, QueueSnapshot
from patient_triage.evaluation.baselines import BaselineBenchmarkReport
from patient_triage.services.triage import TriageService
from patient_triage.storage.sqlite_audit import SQLiteAuditStore


def create_app(settings: Settings | None = None) -> FastAPI:
    runtime_settings = settings or Settings.from_env()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        audit_store = SQLiteAuditStore(runtime_settings.database_path)
        repository = InMemoryPatientRepository()
        service = TriageService(
            settings=runtime_settings,
            repository=repository,
            audit_store=audit_store,
        )
        if runtime_settings.bootstrap_demo_data:
            now = datetime.now(UTC)
            service.load_scenario(generate_normal_scenario(now), scenario_name="normal")
        app.state.triage_service = service
        app.state.audit_store = audit_store
        try:
            yield
        finally:
            audit_store.close()

    application = FastAPI(
        title=runtime_settings.app_name,
        version="0.3.0",
        description=(
            "Safety-constrained, CDM-based emergency queue and capacity coordination "
            "using synthetic data only. This is not an ERP, diagnostic system, or "
            "clinically validated medical device."
        ),
        lifespan=lifespan,
    )

    def get_service(request: Request) -> TriageService:
        return request.app.state.triage_service

    Service = Annotated[TriageService, Depends(get_service)]

    def get_role(
        x_demo_role: Annotated[
            StaffRole,
            Header(
                alias="X-Demo-Role",
                description="Prototype role selector; not production authentication.",
            ),
        ] = StaffRole.DOCTOR,
    ) -> StaffRole:
        return x_demo_role

    Role = Annotated[StaffRole, Depends(get_role)]

    @application.exception_handler(PatientNotFoundError)
    async def patient_not_found_handler(
        _request: Request, exc: PatientNotFoundError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(exc)}
        )

    @application.exception_handler(DuplicatePatientError)
    async def duplicate_patient_handler(
        _request: Request, exc: DuplicatePatientError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT, content={"detail": str(exc)}
        )

    @application.exception_handler(InvalidTimelineError)
    async def invalid_timeline_handler(
        _request: Request, exc: InvalidTimelineError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content={"detail": str(exc)}
        )

    @application.exception_handler(InvalidOverrideError)
    async def invalid_override_handler(
        _request: Request, exc: InvalidOverrideError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content={"detail": str(exc)}
        )

    @application.exception_handler(PermissionDeniedError)
    async def permission_denied_handler(
        _request: Request, exc: PermissionDeniedError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN, content={"detail": str(exc)}
        )

    @application.exception_handler(CoordinationTaskNotFoundError)
    async def coordination_task_not_found_handler(
        _request: Request, exc: CoordinationTaskNotFoundError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(exc)}
        )

    @application.get("/health", response_model=HealthResponse, tags=["system"])
    def health() -> HealthResponse:
        return HealthResponse(
            status="ok",
            app=runtime_settings.app_name,
            model_version=runtime_settings.model_version,
            prototype_only=True,
        )

    @application.get(
        "/v1/access",
        response_model=AccessControlMatrix,
        tags=["access"],
    )
    def access_matrix(service: Service) -> AccessControlMatrix:
        return service.access_matrix

    @application.get(
        "/v1/infrastructure",
        response_model=HospitalProfile,
        tags=["operations"],
    )
    def infrastructure(service: Service, role: Role) -> HospitalProfile:
        service.access.require(role, Permission.FACILITY_READ)
        return service.hospital_profile

    @application.get("/v1/patients", response_model=list[Patient], tags=["patients"])
    def list_patients(service: Service, role: Role) -> list[Patient]:
        service.access.require(role, Permission.PATIENT_READ)
        return service.list_patients()

    @application.post(
        "/v1/patients",
        response_model=Patient,
        status_code=status.HTTP_201_CREATED,
        tags=["patients"],
    )
    def create_patient(patient: Patient, service: Service, role: Role) -> Patient:
        service.access.require(role, Permission.INTAKE_WRITE)
        return service.intake(patient)

    @application.put(
        "/v1/patients/{patient_id}/vitals",
        response_model=Patient,
        tags=["patients"],
    )
    def update_patient_vitals(
        patient_id: str,
        vitals: VitalSigns,
        service: Service,
        role: Role,
        actor_id: Annotated[str, Query(min_length=2, max_length=64)] = "demo-clinician",
    ) -> Patient:
        service.access.require(role, Permission.VITALS_WRITE)
        return service.update_vitals(patient_id, vitals, actor_id=actor_id)

    @application.patch(
        "/v1/patients/{patient_id}/status",
        response_model=Patient,
        tags=["patients"],
    )
    def update_patient_status(
        patient_id: str,
        patient_status: PatientStatus,
        service: Service,
        role: Role,
    ) -> Patient:
        service.access.require(role, Permission.DISPOSITION_WRITE)
        return service.set_status(patient_id, patient_status)

    @application.get("/v1/queue", response_model=QueueSnapshot, tags=["queue"])
    def get_queue(
        service: Service,
        role: Role,
        mode: QueueMode | None = None,
        simulate_model_failure: bool = False,
    ) -> QueueSnapshot:
        service.access.require(role, Permission.QUEUE_READ)
        return service.rank_queue(
            mode=mode, simulate_model_failure=simulate_model_failure
        )

    @application.post(
        "/v1/queue/overrides", response_model=QueueSnapshot, tags=["queue"]
    )
    def override_queue(
        override: OverrideRequest, service: Service, role: Role
    ) -> QueueSnapshot:
        service.access.require(role, Permission.OVERRIDE_WRITE)
        return service.override_queue(override)

    @application.get(
        "/v1/beds",
        response_model=BedBoard,
        tags=["operations"],
    )
    def bed_board(
        service: Service,
        role: Role,
        simulate_model_failure: bool = False,
    ) -> BedBoard:
        service.access.require(role, Permission.BED_READ)
        return service.bed_board(simulate_model_failure=simulate_model_failure)

    @application.get(
        "/v1/evaluation/baselines",
        response_model=BaselineBenchmarkReport,
        tags=["evaluation"],
    )
    def baseline_benchmark(
        service: Service,
        role: Role,
    ) -> BaselineBenchmarkReport:
        service.access.require(role, Permission.ANALYTICS_READ)
        return service.baseline_report()

    @application.get(
        "/v1/coordination/{domain}",
        response_model=list[CoordinationTask],
        tags=["coordination"],
    )
    def coordination_tasks(
        domain: CoordinationDomain,
        service: Service,
        role: Role,
    ) -> list[CoordinationTask]:
        required = (
            Permission.PHARMACY_READ
            if domain is CoordinationDomain.PHARMACY
            else Permission.BLOOD_BANK_READ
        )
        service.access.require(role, required)
        return service.coordination_tasks(domain)

    @application.post(
        "/v1/coordination/{domain}/{task_id}/acknowledge",
        response_model=CoordinationTask,
        tags=["coordination"],
    )
    def acknowledge_coordination_task(
        domain: CoordinationDomain,
        task_id: str,
        acknowledgement: TaskAcknowledgement,
        service: Service,
        role: Role,
    ) -> CoordinationTask:
        required = (
            Permission.PHARMACY_ACKNOWLEDGE
            if domain is CoordinationDomain.PHARMACY
            else Permission.BLOOD_BANK_ACKNOWLEDGE
        )
        service.access.require(role, required)
        return service.acknowledge_coordination_task(
            domain,
            task_id,
            acknowledgement.actor_id,
        )

    @application.post(
        "/v1/simulations/{scenario}",
        response_model=ScenarioResponse,
        tags=["simulations"],
    )
    def load_simulation(
        scenario: Literal["normal", "surge"], service: Service, role: Role
    ) -> ScenarioResponse:
        service.access.require(role, Permission.SCENARIO_WRITE)
        now = datetime.now(UTC)
        patients = generate_scenario(scenario, now)
        service.load_scenario(patients, scenario_name=scenario)
        return ScenarioResponse(scenario=scenario, patient_count=len(patients))

    @application.post(
        "/v1/simulations/deteriorate/{patient_id}",
        response_model=Patient,
        tags=["simulations"],
    )
    def simulate_deterioration(
        patient_id: str, service: Service, role: Role
    ) -> Patient:
        service.access.require(role, Permission.VITALS_WRITE)
        now = datetime.now(UTC)
        patient = service.repository.get(patient_id)
        return service.update_vitals(
            patient_id,
            deteriorated_vitals(patient, now),
            actor_id="demo-simulator",
            now=now,
        )

    @application.get("/v1/audit", response_model=list[AuditEvent], tags=["audit"])
    def list_audit_events(
        service: Service,
        role: Role,
        limit: Annotated[int, Query(ge=1, le=1000)] = 100,
    ) -> list[AuditEvent]:
        service.access.require(role, Permission.AUDIT_READ)
        return service.audit_store.list_events(limit)

    @application.get(
        "/v1/audit/verify",
        response_model=AuditVerificationResponse,
        tags=["audit"],
    )
    def verify_audit_chain(service: Service, role: Role) -> AuditVerificationResponse:
        service.access.require(role, Permission.AUDIT_READ)
        return AuditVerificationResponse(valid=service.audit_store.verify_chain())

    return application


app = create_app()


def run() -> None:
    import uvicorn

    uvicorn.run(
        "patient_triage.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )
