import secrets
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.core.database import get_db
from app.models.alert import Alert
from app.models.clinical import (
    AntimicrobianoAtendimento,
    Atendimento,
    CulturaAtendimento,
    ExecucaoIntegracao,
    IsolamentoAtendimento,
    MovimentacaoLeito,
    Paciente,
    ProcedimentoInvasivoAtendimento,
    ProdutoAntimicrobiano,
    SnapshotAtendimento,
    SolicitacaoExameAtendimento,
)
from app.models.hospital_integration import HospitalIntegration
from app.models.monitoring_run import MonitoringRun
from app.models.patient_bed_movement import PatientBedMovement
from app.models.patient_monitoring_snapshot import PatientMonitoringSnapshot
from app.models.setting import Setting
from app.schemas.hospital_integration import HospitalIntegrationCreate, HospitalIntegrationRead, IngestPayload
from app.services import alert_service, antimicrobial_audit_service
from app.services.antimicrobial_quantity import calculate_product_quantity

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
    if item.dt_nascimento:
        patient.data_nascimento = item.dt_nascimento.date()
    if item.tp_sexo:
        patient.sexo = item.tp_sexo
    attendance = db.scalar(select(Atendimento).where(Atendimento.id_origem_atendimento == item.cd_atendimento))
    if not attendance:
        attendance = Atendimento(
            paciente_id=patient.id,
            id_origem_atendimento=item.cd_atendimento,
        )
        db.add(attendance)
    attendance.ativo = item.active
    attendance.unidade_atual = item.unit
    attendance.codigo_unidade = item.cd_unidade
    attendance.leito_atual = item.bed
    attendance.codigo_leito = item.cd_leito
    attendance.codigo_prestador = item.cd_prestador
    attendance.nome_prestador = item.nm_prestador
    attendance.codigo_convenio = item.cd_convenio
    attendance.nome_convenio = item.nm_convenio
    attendance.data_hora_entrada = item.admitted_at
    attendance.data_hora_saida = item.discharged_at
    db.flush()
    return attendance


def _attendance_for_detail(db: Session, cd_paciente: str, cd_atendimento: str) -> Atendimento:
    attendance = db.scalar(select(Atendimento).where(Atendimento.id_origem_atendimento == cd_atendimento))
    if attendance:
        return attendance
    patient = _get_or_create_patient(db, cd_paciente)
    attendance = Atendimento(paciente_id=patient.id, id_origem_atendimento=cd_atendimento, ativo=True)
    db.add(attendance)
    db.flush()
    return attendance


def _is_active(value: str | None) -> bool:
    return str(value or "").upper() == "S"


def _active_until(value: str | None, end: datetime | None, reference: datetime | None = None) -> bool:
    if not _is_active(value):
        return False
    if not end:
        return True
    reference = reference or datetime.now(timezone.utc)
    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)
    return end > reference


def _antimicrobial_key(item) -> str:
    return str(item.ds_principio_ativo or "Principio ativo nao identificado").strip()


def _days_between(start: datetime | None, end: datetime | None = None, reference_date: date | None = None) -> int:
    if not start:
        return 0
    if end:
        final = end
    elif reference_date:
        final = datetime.combine(reference_date, datetime.min.time(), tzinfo=timezone.utc)
    else:
        final = datetime.now(timezone.utc)
    return max((final.date() - start.date()).days, 0)


def _end_details_at_discharge(payload: IngestPayload) -> None:
    discharge_by_attendance = {
        item.cd_atendimento: item.discharged_at
        for item in payload.patients
        if item.discharged_at
    }
    for items in (payload.antimicrobials, payload.invasive_procedures):
        for item in items:
            discharge = discharge_by_attendance.get(item.cd_atendimento)
            if not discharge or (item.dt_fim and item.dt_fim <= discharge):
                continue
            item.dt_fim = discharge
            item.sn_ativo = "N"
            days = _days_between(item.dt_inicio, discharge)
            if hasattr(item, "dias_uso"):
                item.dias_uso = days
            else:
                item.dias_permanencia = days


def _current_exposure_days(items: list, reference_date: date) -> int:
    exposed_days: set[date] = set()
    for item in items:
        if getattr(item, "dt_aplicacao", None):
            application_day = item.dt_aplicacao.date()
            if application_day <= reference_date:
                exposed_days.add(application_day)
            continue
        start = item.dt_inicio.date()
        end = (item.dt_fim.date() if item.dt_fim else reference_date)
        if end < start:
            continue
        cursor = start
        while cursor <= min(end, reference_date):
            exposed_days.add(cursor)
            cursor += timedelta(days=1)

    total = 0
    cursor = reference_date
    while cursor in exposed_days:
        total += 1
        cursor -= timedelta(days=1)
    return total


def _calculate_snapshot_from_details(
    *,
    item,
    antimicrobials: list,
    cultures: list,
    invasive_procedures: list,
    isolations: list,
    antimicrobial_days: int,
    invasive_device_days: int,
    hospital_stay_days: int,
    reference_date: date,
    historical: bool = False,
) -> dict:
    if historical:
        active_antimicrobials = [
            item for item in antimicrobials
            if item.dt_inicio.date() <= reference_date and (not item.dt_fim or item.dt_fim.date() > reference_date)
        ]
        active_invasive = [
            item for item in invasive_procedures
            if item.dt_inicio.date() <= reference_date and (not item.dt_fim or item.dt_fim.date() > reference_date)
        ]
        active_isolations = [
            item for item in isolations
            if item.dt_inicio.date() <= reference_date and (not item.dt_fim or item.dt_fim.date() > reference_date)
        ]
    else:
        reference_at = datetime.now(timezone.utc)
        antimicrobial_courses, _ = antimicrobial_audit_service.treatment_courses(
            [antimicrobial.model_dump() for antimicrobial in antimicrobials],
            now=reference_at,
        )
        active_antimicrobials = [course for course in antimicrobial_courses if _is_active(course.get("sn_ativo"))]
        active_invasive = [procedure for procedure in invasive_procedures if not procedure.dt_fim]
        active_isolations = [isolation for isolation in isolations if _active_until(isolation.sn_ativo, isolation.dt_fim, reference_at)]

    max_antimicrobial_days = max(
        [(_days_between(antimicrobial.dt_inicio, None, reference_date) if historical else int(antimicrobial.get("dias_uso") or 0)) for antimicrobial in active_antimicrobials]
        or [0]
    )
    max_invasive_device_days = max(
        [(_days_between(procedure.dt_inicio, None, reference_date) if historical else procedure.dias_permanencia or _days_between(procedure.dt_inicio, procedure.dt_fim)) for procedure in active_invasive]
        or [0]
    )
    discharge = item.discharged_at
    if historical and discharge and discharge.date() > reference_date:
        discharge = None
    days_in_hospital = _days_between(item.admitted_at, discharge, reference_date if historical else None)
    has_positive_culture = any(
        _is_active(culture.sn_positivo) and (not historical or culture.dt_coleta.date() <= reference_date)
        for culture in cultures
    )
    has_active_isolation = bool(active_isolations)

    high = (
        has_positive_culture
        or max_antimicrobial_days >= antimicrobial_days
        or max_invasive_device_days >= invasive_device_days
        or days_in_hospital >= hospital_stay_days
        or has_active_isolation
    )
    medium = max_antimicrobial_days >= 4 or days_in_hospital >= 7
    risk_status = "alto" if high else "medio" if medium else "baixo"

    return {
        "risk_status": risk_status,
        "days_in_hospital": days_in_hospital,
        "has_positive_culture": has_positive_culture,
        "max_antimicrobial_days": max_antimicrobial_days,
        "max_invasive_device_days": max_invasive_device_days,
        "has_active_isolation": has_active_isolation,
    }


def _risk_reasons(snapshot: dict, antimicrobial_days: int, invasive_device_days: int, hospital_stay_days: int) -> list[str]:
    reasons = []
    if snapshot["has_positive_culture"]:
        reasons.append("Cultura positiva")
    if snapshot["max_antimicrobial_days"] >= min(4, antimicrobial_days):
        reasons.append(f"Antimicrobiano por {snapshot['max_antimicrobial_days']} dias")
    if snapshot["max_invasive_device_days"] >= invasive_device_days:
        reasons.append(f"Procedimento invasivo por {snapshot['max_invasive_device_days']} dias")
    if snapshot["days_in_hospital"] >= min(7, hospital_stay_days):
        reasons.append(f"Internacao por {snapshot['days_in_hospital']} dias")
    if snapshot["has_active_isolation"]:
        reasons.append("Isolamento ativo")
    return reasons


def _scheme_change_events(items: list, reference_date: date, window_days: int) -> list[str]:
    window_start = reference_date - timedelta(days=window_days - 1)
    events: dict[date, set[str]] = defaultdict(set)
    for item in items:
        antimicrobial = _antimicrobial_key(item)
        start = item.dt_inicio.date()
        if window_start <= start <= reference_date:
            events[start].add(f"inicio de {antimicrobial}")
        if item.dt_fim:
            end = item.dt_fim.date()
            if window_start <= end <= reference_date:
                events[end].add(f"suspensao de {antimicrobial}")
    return [f"{day.strftime('%d/%m')}: {', '.join(sorted(changes))}" for day, changes in sorted(events.items())]


def _create_ingested_alert(
    db: Session,
    *,
    item,
    alert_type: str,
    title: str,
    description: str,
    recommendation: str,
    severity: str = "ALTA",
) -> bool:
    existing = db.scalar(
        select(Alert).where(
            Alert.cd_atendimento == item.cd_atendimento,
            Alert.alert_type == alert_type,
            Alert.status.in_(["ABERTO", "EM_ANALISE"]),
            Alert.source == "client_ingestion",
        )
    )
    if existing:
        return False
    alert = Alert(
            cd_atendimento=item.cd_atendimento,
            cd_paciente=item.cd_paciente,
            unit=item.unit,
            rule_id=None,
            alert_type=alert_type,
            severity=severity,
            title=title,
            description=description,
            recommendation=recommendation,
            status="ABERTO",
            source="client_ingestion",
        )
    db.add(alert)
    db.flush()
    alert_service.notify_alert_created(db, alert)
    return True


def _create_antimicrobial_alerts(
    db: Session,
    *,
    item,
    antimicrobials: list,
    same_antimicrobial_days: int,
    exposure_days: int,
    scheme_changes_count: int,
    scheme_changes_window_days: int,
    reference_date: date,
) -> int:
    created = 0
    reference_at = datetime.now(timezone.utc)
    courses, _ = antimicrobial_audit_service.treatment_courses(
        [antimicrobial.model_dump() for antimicrobial in antimicrobials],
        now=reference_at,
    )
    active_antimicrobials = [course for course in courses if _is_active(course.get("sn_ativo"))]

    prolonged_by_key: dict[str, int] = {}
    for antimicrobial in active_antimicrobials:
        key = str(antimicrobial.get("ds_principio_ativo") or antimicrobial.get("ds_antimicrobiano") or "Principio ativo nao identificado").strip()
        days = int(antimicrobial.get("dias_uso") or 0)
        prolonged_by_key[key] = max(prolonged_by_key.get(key, 0), days)

    prolonged = {name: days for name, days in prolonged_by_key.items() if days >= same_antimicrobial_days}
    if prolonged:
        details = "; ".join(f"{name} em uso continuo ha {days} dias" for name, days in sorted(prolonged.items()))
        if _create_ingested_alert(
            db,
            item=item,
            alert_type="ANTIMICROBIAL_SAME_PROLONGED",
            title="Alerta 1 - Mesmo antimicrobiano prolongado",
            description=f"{details}. Calculo por prescricao/principio ativo.",
            recommendation="Avaliar necessidade de manter, descalonar, suspender ou justificar a continuidade do mesmo antimicrobiano.",
            severity="MEDIA",
        ):
            created += 1

    current_exposure_days = _current_exposure_days(antimicrobials, reference_date)
    if current_exposure_days >= exposure_days:
        if _create_ingested_alert(
            db,
            item=item,
            alert_type="ANTIMICROBIAL_EXPOSURE_PROLONGED",
            title="Alerta 2 - Exposicao antimicrobiana prolongada",
            description=(
                f"Paciente recebendo algum antimicrobiano ha {current_exposure_days} dias consecutivos, "
                "mesmo com alteracoes de esquema. Calculo por dia de internacao com ao menos um antimicrobiano administrado."
            ),
            recommendation="Revisar exposicao global, indicacao atual, cultura, possibilidade de descalonamento e data prevista de termino.",
            severity="ALTA",
        ):
            created += 1

    scheme_events = _scheme_change_events(antimicrobials, reference_date, scheme_changes_window_days)
    if len(scheme_events) >= scheme_changes_count:
        if _create_ingested_alert(
            db,
            item=item,
            alert_type="ANTIMICROBIAL_FREQUENT_SCHEME_CHANGES",
            title="Alerta 3 - Trocas frequentes de esquema",
            description=(
                f"Paciente teve {len(scheme_events)} alteracoes de esquema antimicrobiano em {scheme_changes_window_days} dias. "
                f"Eventos considerados: {'; '.join(scheme_events)}."
            ),
            recommendation="Reavaliar hipotese infecciosa, resultados microbiologicos, foco infeccioso e estabilidade do plano terapeutico.",
            severity="ALTA",
        ):
            created += 1

    return created


@router.post("/ingest/snapshots")
def ingest_snapshots(
    payload: IngestPayload,
    x_sanatio_token: str | None = Header(default=None, alias="X-Sanatio-Token"),
    db: Session = Depends(get_db),
) -> dict:
    integration = db.scalar(select(HospitalIntegration).where(HospitalIntegration.token == x_sanatio_token, HospitalIntegration.active.is_(True)))
    if not integration:
        raise HTTPException(status_code=401, detail="Token hospitalar invalido")

    historical = payload.modo_carga == "HISTORICA"
    if historical:
        existing_run = db.scalar(
            select(ExecucaoIntegracao).where(
                ExecucaoIntegracao.hospital_integracao_id == integration.id,
                ExecucaoIntegracao.chave_lote == payload.chave_lote,
            )
        )
        if existing_run:
            return {
                "hospital": integration.hospital_name,
                "integration_run_id": existing_run.id,
                "modo_carga": existing_run.modo_carga,
                "chave_lote": existing_run.chave_lote,
                "duplicate": True,
                "snapshots_received": existing_run.total_snapshots_recebidos,
                "alerts_created": existing_run.total_alertas_gerados,
            }

    antimicrobial_days = _threshold(db, "alerts.threshold.antimicrobial_days", 7)
    same_antimicrobial_days = _threshold(db, "alerts.threshold.same_antimicrobial_days", antimicrobial_days)
    antimicrobial_exposure_days = _threshold(db, "alerts.threshold.antimicrobial_exposure_days", 14)
    antimicrobial_scheme_changes_count = _threshold(db, "alerts.threshold.antimicrobial_scheme_changes_count", 3)
    antimicrobial_scheme_changes_window_days = _threshold(db, "alerts.threshold.antimicrobial_scheme_changes_window_days", 7)
    invasive_device_days = _threshold(db, "alerts.threshold.invasive_device_days", 7)
    hospital_stay_days = _threshold(db, "alerts.threshold.hospital_stay_days", 10)

    started_at = datetime.now(timezone.utc)
    reference_at = payload.data_referencia or started_at
    if reference_at.tzinfo is None:
        reference_at = reference_at.replace(tzinfo=timezone.utc)
    _end_details_at_discharge(payload)
    monitoring_run = MonitoringRun(status="RUNNING", started_at=started_at)
    db.add(monitoring_run)
    integration_run = ExecucaoIntegracao(
        hospital_integracao_id=integration.id,
        status="EM_EXECUCAO",
        modo_carga=payload.modo_carga,
        chave_lote=payload.chave_lote,
        data_referencia=reference_at if historical else None,
        data_hora_inicio=started_at,
    )
    db.add(integration_run)
    db.flush()

    created_alerts = 0
    antimicrobials_by_attendance = defaultdict(list)
    for antimicrobial in payload.antimicrobials:
        antimicrobials_by_attendance[antimicrobial.cd_atendimento].append(antimicrobial)
    cultures_by_attendance = defaultdict(list)
    for culture in payload.cultures:
        cultures_by_attendance[culture.cd_atendimento].append(culture)
    invasive_by_attendance = defaultdict(list)
    for procedure in payload.invasive_procedures:
        invasive_by_attendance[procedure.cd_atendimento].append(procedure)
    isolations_by_attendance = defaultdict(list)
    for isolation in payload.isolations:
        isolations_by_attendance[isolation.cd_atendimento].append(isolation)

    for item in payload.patients:
        attendance = _upsert_attendance(db, item)
        calculated_snapshot = _calculate_snapshot_from_details(
            item=item,
            antimicrobials=antimicrobials_by_attendance.get(item.cd_atendimento, []),
            cultures=cultures_by_attendance.get(item.cd_atendimento, []),
            invasive_procedures=invasive_by_attendance.get(item.cd_atendimento, []),
            isolations=isolations_by_attendance.get(item.cd_atendimento, []),
            antimicrobial_days=antimicrobial_days,
            invasive_device_days=invasive_device_days,
            hospital_stay_days=hospital_stay_days,
            reference_date=reference_at.date(),
            historical=historical,
        )
        snapshot = None
        if historical:
            snapshot = db.scalar(
                select(SnapshotAtendimento).where(
                    SnapshotAtendimento.atendimento_id == attendance.id,
                    SnapshotAtendimento.data_hora_coleta == reference_at,
                )
            )
        if not snapshot:
            snapshot = SnapshotAtendimento(
                atendimento_id=attendance.id,
            )
            db.add(snapshot)
        snapshot.execucao_integracao_id = integration_run.id
        snapshot.status_risco = calculated_snapshot["risk_status"]
        snapshot.dias_internacao = calculated_snapshot["days_in_hospital"]
        snapshot.possui_cultura_positiva = calculated_snapshot["has_positive_culture"]
        snapshot.maior_dias_antimicrobiano = calculated_snapshot["max_antimicrobial_days"]
        snapshot.maior_dias_dispositivo_invasivo = calculated_snapshot["max_invasive_device_days"]
        snapshot.possui_isolamento_ativo = calculated_snapshot["has_active_isolation"]
        snapshot.data_hora_coleta = reference_at

        monitoring_snapshot = {
            key: value
            for key, value in item.model_dump().items()
            if key in PatientMonitoringSnapshot.__table__.columns
        }
        monitoring_snapshot.update(calculated_snapshot)
        operational_snapshot = None
        if historical:
            operational_snapshot = db.scalar(
                select(PatientMonitoringSnapshot).where(
                    PatientMonitoringSnapshot.cd_atendimento == item.cd_atendimento,
                    PatientMonitoringSnapshot.collected_at == reference_at,
                )
            )
        if operational_snapshot:
            for key, value in monitoring_snapshot.items():
                setattr(operational_snapshot, key, value)
            operational_snapshot.monitoring_run_id = monitoring_run.id
        else:
            db.add(PatientMonitoringSnapshot(
                **monitoring_snapshot,
                monitoring_run_id=monitoring_run.id,
                collected_at=reference_at,
            ))
        reasons = _risk_reasons(calculated_snapshot, antimicrobial_days, invasive_device_days, hospital_stay_days)
        if not historical:
            created_alerts += _create_antimicrobial_alerts(
                db,
                item=item,
                antimicrobials=antimicrobials_by_attendance.get(item.cd_atendimento, []),
                same_antimicrobial_days=same_antimicrobial_days,
                exposure_days=antimicrobial_exposure_days,
                scheme_changes_count=antimicrobial_scheme_changes_count,
                scheme_changes_window_days=antimicrobial_scheme_changes_window_days,
                reference_date=started_at.date(),
            )
        if historical:
            continue
        existing = db.scalar(
            select(Alert).where(
                Alert.cd_atendimento == item.cd_atendimento,
                Alert.alert_type == "INGESTED_RISK",
                Alert.status.in_(["ABERTO", "EM_ANALISE"]),
                Alert.source == "client_ingestion",
            )
        )
        if not reasons:
            if existing:
                existing.status = "RESOLVIDO"
                existing.resolved_at = started_at
                existing.description = "Resolvido automaticamente: fatores de risco nao estao mais presentes no snapshot atual."
            continue
        if existing:
            existing.severity = "ALTA" if calculated_snapshot["risk_status"] == "alto" else "MEDIA"
            existing.description = "Motivos: " + ", ".join(reasons)
            continue
        db.add(
            Alert(
                cd_atendimento=item.cd_atendimento,
                cd_paciente=item.cd_paciente,
                unit=item.unit,
                rule_id=None,
                alert_type="INGESTED_RISK",
                severity="ALTA" if calculated_snapshot["risk_status"] == "alto" else "MEDIA",
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

    antimicrobials_by_patient: dict[str, list[dict]] = {}
    for item in payload.antimicrobials:
        attendance = _attendance_for_detail(db, item.cd_paciente, item.cd_atendimento)
        antimicrobial = db.scalar(
            select(AntimicrobianoAtendimento).where(
                AntimicrobianoAtendimento.atendimento_id == attendance.id,
                AntimicrobianoAtendimento.id_origem_prescricao == item.cd_prescricao,
                AntimicrobianoAtendimento.id_origem_item_prescricao == item.cd_item_prescricao,
                AntimicrobianoAtendimento.data_hora_aplicacao == item.dt_aplicacao,
            )
        )
        if not antimicrobial:
            antimicrobial = AntimicrobianoAtendimento(
                atendimento_id=attendance.id,
                id_origem_prescricao=item.cd_prescricao,
                id_origem_item_prescricao=item.cd_item_prescricao,
            )
            db.add(antimicrobial)
        antimicrobial.id_origem_produto = item.cd_produto
        antimicrobial.nome_antimicrobiano = item.ds_antimicrobiano
        antimicrobial.principio_ativo = item.ds_principio_ativo
        antimicrobial.data_hora_inicio = item.dt_inicio
        antimicrobial.data_hora_aplicacao = item.dt_aplicacao
        antimicrobial.data_hora_fim = item.dt_fim
        antimicrobial.ativo = _active_until(item.sn_ativo, item.dt_fim)
        product = db.scalar(
            select(ProdutoAntimicrobiano).where(ProdutoAntimicrobiano.codigo_produto == item.cd_produto)
        ) if item.cd_produto else None
        dose_quantity, total_quantity, total_grams, total_unit = calculate_product_quantity(item.qt_dose, product)
        antimicrobial.quantidade_dose = dose_quantity
        antimicrobial.quantidade_total = total_quantity
        antimicrobial.quantidade_total_gramas = total_grams
        antimicrobial.unidade_quantidade_total = total_unit
        antimicrobial.dose = item.ds_dose
        antimicrobial.via = item.ds_via
        antimicrobial.frequencia = item.ds_frequencia
        antimicrobial.dias_uso = item.dias_uso
        antimicrobials_by_patient.setdefault(item.cd_atendimento, []).append(
            {
                "cd_prescricao": item.cd_prescricao,
                "cd_item_prescricao": item.cd_item_prescricao,
                "cd_produto": item.cd_produto,
                "ds_antimicrobiano": item.ds_antimicrobiano,
                "ds_principio_ativo": item.ds_principio_ativo,
                "dt_inicio": item.dt_inicio,
                "dt_aplicacao": item.dt_aplicacao,
                "dt_fim": item.dt_fim,
                "sn_ativo": item.sn_ativo,
                "ds_dose": item.ds_dose,
                "ds_via": item.ds_via,
                "ds_frequencia": item.ds_frequencia,
                "dias_uso": item.dias_uso,
            }
        )

    for item in payload.exam_requests:
        attendance = _attendance_for_detail(db, item.cd_paciente, item.cd_atendimento)
        request = db.scalar(select(SolicitacaoExameAtendimento).where(SolicitacaoExameAtendimento.id_origem_pedido == item.cd_pedido))
        if request and request.atendimento_id != attendance.id:
            raise HTTPException(status_code=422, detail=f"Pedido {item.cd_pedido} vinculado a outro atendimento")
        if not request:
            request = SolicitacaoExameAtendimento(atendimento_id=attendance.id, id_origem_pedido=item.cd_pedido)
            db.add(request)
        request.data_hora_solicitacao = item.dt_solicitacao

    for item in payload.cultures:
        attendance = _attendance_for_detail(db, item.cd_paciente, item.cd_atendimento)
        culture = db.scalar(
            select(CulturaAtendimento).where(
                CulturaAtendimento.atendimento_id == attendance.id,
                CulturaAtendimento.id_origem_pedido == item.cd_pedido,
                CulturaAtendimento.id_origem_exame == item.cd_exame,
            )
        )
        if not culture:
            culture = CulturaAtendimento(atendimento_id=attendance.id, id_origem_pedido=item.cd_pedido, id_origem_exame=item.cd_exame)
            db.add(culture)
        culture.exame = item.ds_exame
        culture.material = item.ds_material
        culture.microorganismo = item.ds_microorganismo
        culture.resultado = item.ds_resultado
        culture.positivo = _is_active(item.sn_positivo)
        culture.data_hora_coleta = item.dt_coleta
        culture.data_hora_resultado = item.dt_resultado

    for item in payload.invasive_procedures:
        attendance = _attendance_for_detail(db, item.cd_paciente, item.cd_atendimento)
        procedure = db.scalar(
            select(ProcedimentoInvasivoAtendimento).where(
                ProcedimentoInvasivoAtendimento.atendimento_id == attendance.id,
                ProcedimentoInvasivoAtendimento.id_origem_procedimento == item.cd_procedimento,
                ProcedimentoInvasivoAtendimento.data_hora_inicio == item.dt_inicio,
            )
        )
        if not procedure:
            procedure = ProcedimentoInvasivoAtendimento(
                atendimento_id=attendance.id,
                id_origem_procedimento=item.cd_procedimento,
                data_hora_inicio=item.dt_inicio,
            )
            db.add(procedure)
        procedure.procedimento = item.ds_procedimento
        procedure.local_instalacao = item.ds_local_instalacao
        procedure.data_hora_fim = item.dt_fim
        procedure.ativo = item.dt_fim is None
        procedure.dias_permanencia = item.dias_permanencia

    for item in payload.isolations:
        attendance = _attendance_for_detail(db, item.cd_paciente, item.cd_atendimento)
        isolation = db.scalar(
            select(IsolamentoAtendimento).where(
                IsolamentoAtendimento.atendimento_id == attendance.id,
                IsolamentoAtendimento.id_origem_isolamento == item.cd_isolamento,
                IsolamentoAtendimento.data_hora_inicio == item.dt_inicio,
            )
        )
        if not isolation:
            isolation = IsolamentoAtendimento(
                atendimento_id=attendance.id,
                id_origem_isolamento=item.cd_isolamento,
                data_hora_inicio=item.dt_inicio,
            )
            db.add(isolation)
        isolation.isolamento = item.ds_isolamento
        isolation.data_hora_fim = item.dt_fim
        isolation.ativo = _active_until(item.sn_ativo, item.dt_fim)

    if not historical:
        for item in payload.patients:
            patient_payload = {
                "cd_atendimento": item.cd_atendimento,
                "cd_paciente": item.cd_paciente,
                "ds_unidade": item.unit,
                "active": item.active,
            }
            antimicrobial_audit_service.sync_for_patient(db, patient_payload, antimicrobials_by_patient.get(item.cd_atendimento, []), monitoring_run.id)

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
        "modo_carga": payload.modo_carga,
        "chave_lote": payload.chave_lote,
        "data_referencia": reference_at.isoformat() if historical else None,
        "duplicate": False,
        "snapshots_received": len(payload.patients),
        "bed_movements_received": created_movements,
        "antimicrobials_received": len(payload.antimicrobials),
        "cultures_received": len(payload.cultures),
        "exam_requests_received": len(payload.exam_requests),
        "invasive_procedures_received": len(payload.invasive_procedures),
        "isolations_received": len(payload.isolations),
        "alerts_created": created_alerts,
    }
