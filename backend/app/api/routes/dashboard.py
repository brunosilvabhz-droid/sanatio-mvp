from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.alert import Alert
from app.models.clinical import (
    AntimicrobianoAtendimento,
    Atendimento,
    CulturaAtendimento,
    IsolamentoAtendimento,
    Paciente,
    SnapshotAtendimento,
)
from app.models.lab_pdf_import import ImportacaoPdfLaboratorio, ResultadoPdfLaboratorio
from app.models.patient_monitoring_snapshot import PatientMonitoringSnapshot

router = APIRouter(prefix="/dashboard", tags=["Dashboard"], dependencies=[Depends(get_current_user)])


def _prolonged_antimicrobial_attendances(db: Session, minimum_days: int = 7) -> int:
    return db.scalar(
        select(func.count(func.distinct(AntimicrobianoAtendimento.atendimento_id)))
        .join(Atendimento, Atendimento.id == AntimicrobianoAtendimento.atendimento_id)
        .where(
            Atendimento.ativo.is_(True),
            AntimicrobianoAtendimento.dias_uso >= minimum_days,
        )
    ) or 0


def _positive_culture_attendances(
    db: Session,
    snapshots: list[SnapshotAtendimento] | None = None,
) -> int:
    attendance_ids = {
        snapshot.atendimento_id
        for snapshot in snapshots or []
        if snapshot.possui_cultura_positiva
    }
    attendance_ids.update(
        db.scalars(
            select(CulturaAtendimento.atendimento_id)
            .join(Atendimento, Atendimento.id == CulturaAtendimento.atendimento_id)
            .where(Atendimento.ativo.is_(True), CulturaAtendimento.positivo.is_(True))
        ).all()
    )
    attendance_ids.update(
        db.scalars(
            select(ResultadoPdfLaboratorio.atendimento_id)
            .join(Atendimento, Atendimento.id == ResultadoPdfLaboratorio.atendimento_id)
            .join(ImportacaoPdfLaboratorio, ImportacaoPdfLaboratorio.id == ResultadoPdfLaboratorio.importacao_id)
            .where(
                Atendimento.ativo.is_(True),
                ImportacaoPdfLaboratorio.status == "VALIDADA",
                ResultadoPdfLaboratorio.situacao == "POSITIVA",
            )
        ).all()
    )
    return len(attendance_ids)


@router.get("/isolation-map")
def isolation_map(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.execute(
        select(IsolamentoAtendimento, Atendimento, Paciente)
        .join(Atendimento, Atendimento.id == IsolamentoAtendimento.atendimento_id)
        .join(Paciente, Paciente.id == Atendimento.paciente_id)
        .where(IsolamentoAtendimento.ativo.is_(True), Atendimento.ativo.is_(True))
        .order_by(Atendimento.unidade_atual, Atendimento.leito_atual, IsolamentoAtendimento.data_hora_inicio)
    ).all()
    return [
        {
            "cd_atendimento": atendimento.id_origem_atendimento,
            "cd_paciente": paciente.id_origem_paciente,
            "unidade": atendimento.unidade_atual,
            "leito": atendimento.leito_atual,
            "isolamento": isolamento.isolamento,
            "inicio": isolamento.data_hora_inicio,
        }
        for isolamento, atendimento, paciente in rows
    ]


@router.get("/summary")
def summary(db: Session = Depends(get_db)) -> dict:
    prolonged_antimicrobials = _prolonged_antimicrobial_attendances(db)
    clinical_snapshots = db.scalars(
        select(SnapshotAtendimento)
        .join(Atendimento, Atendimento.id == SnapshotAtendimento.atendimento_id)
        .where(Atendimento.ativo.is_(True))
        .order_by(SnapshotAtendimento.data_hora_coleta.desc())
    ).all()
    clinical_latest: dict[int, SnapshotAtendimento] = {}
    for snapshot in clinical_snapshots:
        clinical_latest.setdefault(snapshot.atendimento_id, snapshot)
    if clinical_latest:
        snapshot_values = list(clinical_latest.values())
        positive_cultures = _positive_culture_attendances(db, snapshot_values)
        open_alerts = db.scalar(select(func.count(Alert.id)).where(Alert.status.in_(["ABERTO", "EM_ANALISE"]))) or 0
        critical_alerts = db.scalar(select(func.count(Alert.id)).where(Alert.severity == "ALTA", Alert.status.in_(["ABERTO", "EM_ANALISE"]))) or 0
        return {
            "monitored_patients": len(snapshot_values),
            "open_alerts": open_alerts,
            "critical_alerts": critical_alerts,
            "high_risk_patients": len([p for p in snapshot_values if p.status_risco == "alto"]),
            "positive_cultures": positive_cultures,
            "prolonged_antimicrobials": prolonged_antimicrobials,
            "active_isolations": len([p for p in snapshot_values if p.possui_isolamento_ativo]),
        }

    snapshots = db.scalars(select(PatientMonitoringSnapshot).order_by(PatientMonitoringSnapshot.collected_at.desc())).all()
    latest: dict[str, PatientMonitoringSnapshot] = {}
    for snapshot in snapshots:
        latest.setdefault(snapshot.cd_atendimento, snapshot)
    if latest:
        snapshot_values = list(latest.values())
        positive_cultures = _positive_culture_attendances(db)
        open_alerts = db.scalar(select(func.count(Alert.id)).where(Alert.status.in_(["ABERTO", "EM_ANALISE"]))) or 0
        critical_alerts = db.scalar(select(func.count(Alert.id)).where(Alert.severity == "ALTA", Alert.status.in_(["ABERTO", "EM_ANALISE"]))) or 0
        return {
            "monitored_patients": len(snapshot_values),
            "open_alerts": open_alerts,
            "critical_alerts": critical_alerts,
            "high_risk_patients": len([p for p in snapshot_values if p.risk_status == "alto"]),
            "positive_cultures": max(
                positive_cultures,
                len([p for p in snapshot_values if p.has_positive_culture]),
            ),
            "prolonged_antimicrobials": prolonged_antimicrobials,
            "active_isolations": len([p for p in snapshot_values if p.has_active_isolation]),
        }

    open_alerts = db.scalar(select(func.count(Alert.id)).where(Alert.status.in_(["ABERTO", "EM_ANALISE"]))) or 0
    critical_alerts = db.scalar(select(func.count(Alert.id)).where(Alert.severity == "ALTA", Alert.status.in_(["ABERTO", "EM_ANALISE"]))) or 0
    return {
        "monitored_patients": 0,
        "open_alerts": open_alerts,
        "critical_alerts": critical_alerts,
        "high_risk_patients": 0,
        "positive_cultures": _positive_culture_attendances(db),
        "prolonged_antimicrobials": 0,
        "active_isolations": 0,
    }
