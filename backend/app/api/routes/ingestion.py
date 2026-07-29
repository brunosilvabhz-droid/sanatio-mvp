import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.core.database import get_db
from app.models.alert import Alert
from app.models.clinical import Atendimento, ExecucaoIntegracao, MovimentacaoLeito, Paciente, SnapshotAtendimento
from app.models.hospital_integration import HospitalIntegration
from app.models.monitoring_run import MonitoringRun
from app.models.patient_bed_movement import PatientBedMovement
from app.models.patient_monitoring_snapshot import PatientMonitoringSnapshot
from app.models.setting import Setting
from app.schemas.hospital_integration import HospitalIntegrationCreate, HospitalIntegrationRead, IngestPayload

router = APIRouter(tags=["Integracao hospitalar"])


@router.get("/hospital-integrations", response_model=list[HospitalIntegrationRead], dependencies=[Depends(require_admin)])
def list_integrations(db: Session = Depends(get_db)) -> list[HospitalIntegration]:
    return list(db.scalars(select(HospitalIntegration).order_by(HospitalIntegration.created_at.desc())))


@router.post("/hospital-integrations", response_model=HospitalIntegrationRead, dependencies=[Depends(require_admin)])
def create_integration(payload: HospitalIntegrationCreate, db: Session = Depends(get_db)) -> HospitalIntegration:
    existing = db.scalar(select(HospitalIntegration).where(HospitalIntegration.hospital_name == payload.hospital_name))
    if existing:
        raise HTTPException(status_code=409, detail="Hospital ja cadastrado")
    integration = HospitalIntegration(hospital_name=payload.hospital_name, token=None, active=True)
    db.add(integration)
    db.commit()
    db.refresh(integration)
    return integration


@router.post("/hospital-integrations/{integration_id}/token", response_model=HospitalIntegrationRead, dependencies=[Depends(require_admin)])
def generate_integration_token(integration_id: int, db: Session = Depends(get_db)) -> HospitalIntegration:
    integration = db.get(HospitalIntegration, integration_id)
    if not integration:
        raise HTTPException(status_code=404, detail="Hospital nao encontrado")
    integration.token = secrets.token_urlsafe(32)
    integration.active = True
    db.commit()
    db.refresh(integration)
    return integration


def _threshold(db: Session, key: str, default: int) -> int:
    setting = db.scalar(select(Setting).where(Setting.key == key))
    try:
        return int(setting.value) if setting and setting.value is not None else default
    except ValueError:
        return default


def _get_or_create_patient(db: Session, cd_paciente: str) -> Paciente:
    patient = db.scalar(select(Paciente).where(Paciente.id_origem_paciente == cd_paciente))
    if patient:
        return patient
    patient = Paciente(id_origem_paciente=cd_paciente)
    db.add(patient)
    db.flush()
    return patient


def _upsert_attendance(db: Session, item) -> Atendimento:
    patient = _get_or_create_patient(db, item.cd_paciente)
    attendance = db.scalar(select(Atendimento).where(Atendimento.id_origem_atendimento == item.cd_atendimento))
    if not attendance:
        attendance = Atendimento(
            paciente_id=patient.id,
            id_origem_atendimento=item.cd_atendimento,
        )
        db.add(attendance)
    attendance.ativo = item.active
    attendance.unidade_atual = item.unit
    attendance.leito_atual = item.bed
    attendance.data_hora_entrada = item.admitted_at
    attendance.data_hora_saida = item.discharged_at
    db.flush()
    return attendance


@router.post("/ingest/snapshots")
def ingest_snapshots(
    payload: IngestPayload,
    x_sanatio_token: str | None = Header(default=None, alias="X-Sanatio-Token"),
    db: Session = Depends(get_db),
) -> dict:
    integration = db.scalar(select(HospitalIntegration).where(HospitalIntegration.token == x_sanatio_token, HospitalIntegration.active.is_(True)))
    if not integration:
        raise HTTPException(status_code=401, detail="Token hospitalar invalido")

    antimicrobial_days = _threshold(db, "alerts.threshold.antimicrobial_days", 7)
    invasive_device_days = _threshold(db, "alerts.threshold.invasive_device_days", 7)
    hospital_stay_days = _threshold(db, "alerts.threshold.hospital_stay_days", 10)

    started_at = datetime.now(timezone.utc)
    monitoring_run = MonitoringRun(status="RUNNING", started_at=started_at)
    db.add(monitoring_run)
    integration_run = ExecucaoIntegracao(
        hospital_integracao_id=integration.id,
        status="EM_EXECUCAO",
        data_hora_inicio=started_at,
    )
    db.add(integration_run)
    db.flush()

    created_alerts = 0
    for item in payload.patients:
        attendance = _upsert_attendance(db, item)
        db.add(
            SnapshotAtendimento(
                atendimento_id=attendance.id,
                execucao_integracao_id=integration_run.id,
                status_risco=item.risk_status,
                dias_internacao=item.days_in_hospital,
                possui_cultura_positiva=item.has_positive_culture,
                maior_dias_antimicrobiano=item.max_antimicrobial_days,
                maior_dias_dispositivo_invasivo=item.max_invasive_device_days,
                possui_isolamento_ativo=item.has_active_isolation,
                data_hora_coleta=started_at,
            )
        )
        db.add(PatientMonitoringSnapshot(**item.model_dump(), monitoring_run_id=monitoring_run.id))
        reasons = []
        if item.risk_status == "alto":
            reasons.append("risco alto")
        if item.has_positive_culture:
            reasons.append("cultura positiva")
        if item.max_antimicrobial_days >= antimicrobial_days:
            reasons.append(f"antimicrobiano por {item.max_antimicrobial_days} dias")
        if item.max_invasive_device_days >= invasive_device_days:
            reasons.append(f"procedimento invasivo por {item.max_invasive_device_days} dias")
        if item.days_in_hospital >= hospital_stay_days:
            reasons.append(f"{item.days_in_hospital} dias de internacao")
        if not reasons:
            continue
        existing = db.scalar(
            select(Alert).where(
                Alert.cd_atendimento == item.cd_atendimento,
                Alert.status.in_(["ABERTO", "EM_ANALISE"]),
                Alert.source == "client_ingestion",
            )
        )
        if existing:
            continue
        db.add(
            Alert(
                cd_atendimento=item.cd_atendimento,
                cd_paciente=item.cd_paciente,
                unit=item.unit,
                rule_id=None,
                alert_type="INGESTED_RISK",
                severity="ALTA" if item.risk_status == "alto" else "MEDIA",
                title="Alerta recebido do hospital",
                description="Motivos: " + ", ".join(reasons),
                recommendation="Avaliar paciente e registrar evolucao/intervencao quando necessario.",
                status="ABERTO",
                source="client_ingestion",
            )
        )
        created_alerts += 1

    created_movements = 0
    for movement in payload.bed_movements:
        attendance = db.scalar(select(Atendimento).where(Atendimento.id_origem_atendimento == movement.cd_atendimento))
        if not attendance:
            patient = _get_or_create_patient(db, movement.cd_paciente)
            attendance = Atendimento(paciente_id=patient.id, id_origem_atendimento=movement.cd_atendimento, ativo=True)
            db.add(attendance)
            db.flush()
        new_movement_exists = db.scalar(
            select(MovimentacaoLeito).where(
                MovimentacaoLeito.atendimento_id == attendance.id,
                MovimentacaoLeito.data_hora_movimentacao == movement.moved_at,
                MovimentacaoLeito.leito_destino == movement.to_bed,
            )
        )
        if not new_movement_exists:
            db.add(
                MovimentacaoLeito(
                    atendimento_id=attendance.id,
                    unidade_origem=movement.from_unit,
                    leito_origem=movement.from_bed,
                    unidade_destino=movement.to_unit,
                    leito_destino=movement.to_bed,
                    data_hora_movimentacao=movement.moved_at,
                )
            )
        exists = db.scalar(
            select(PatientBedMovement).where(
                PatientBedMovement.cd_atendimento == movement.cd_atendimento,
                PatientBedMovement.moved_at == movement.moved_at,
                PatientBedMovement.to_bed == movement.to_bed,
            )
        )
        if exists:
            continue
        db.add(PatientBedMovement(**movement.model_dump()))
        created_movements += 1

    finished_at = datetime.now(timezone.utc)
    monitoring_run.status = "SUCCESS"
    monitoring_run.patients_processed = len(payload.patients)
    monitoring_run.alerts_created = created_alerts
    monitoring_run.finished_at = finished_at
    monitoring_run.duration_ms = int((finished_at - started_at).total_seconds() * 1000)
    integration_run.status = "SUCESSO"
    integration_run.total_pacientes_recebidos = len({item.cd_paciente for item in payload.patients})
    integration_run.total_snapshots_recebidos = len(payload.patients)
    integration_run.total_movimentacoes_recebidas = created_movements
    integration_run.total_alertas_gerados = created_alerts
    integration_run.data_hora_fim = finished_at
    db.commit()
    return {
        "hospital": integration.hospital_name,
        "run_id": monitoring_run.id,
        "integration_run_id": integration_run.id,
        "snapshots_received": len(payload.patients),
        "bed_movements_received": created_movements,
        "alerts_created": created_alerts,
    }
