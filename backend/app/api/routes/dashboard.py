from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.alert import Alert
from app.models.clinical import SnapshotAtendimento
from app.models.patient_monitoring_snapshot import PatientMonitoringSnapshot

router = APIRouter(prefix="/dashboard", tags=["Dashboard"], dependencies=[Depends(get_current_user)])


@router.get("/summary")
def summary(db: Session = Depends(get_db)) -> dict:
    clinical_snapshots = db.scalars(select(SnapshotAtendimento).order_by(SnapshotAtendimento.data_hora_coleta.desc())).all()
    clinical_latest: dict[int, SnapshotAtendimento] = {}
    for snapshot in clinical_snapshots:
        clinical_latest.setdefault(snapshot.atendimento_id, snapshot)
    if clinical_latest:
        snapshot_values = list(clinical_latest.values())
        open_alerts = db.scalar(select(func.count(Alert.id)).where(Alert.status.in_(["ABERTO", "EM_ANALISE"]))) or 0
        critical_alerts = db.scalar(select(func.count(Alert.id)).where(Alert.severity == "ALTA", Alert.status.in_(["ABERTO", "EM_ANALISE"]))) or 0
        return {
            "monitored_patients": len(snapshot_values),
            "open_alerts": open_alerts,
            "critical_alerts": critical_alerts,
            "high_risk_patients": len([p for p in snapshot_values if p.status_risco == "alto"]),
            "positive_cultures": len([p for p in snapshot_values if p.possui_cultura_positiva]),
            "prolonged_antimicrobials": len([p for p in snapshot_values if p.maior_dias_antimicrobiano > 7]),
        }

    snapshots = db.scalars(select(PatientMonitoringSnapshot).order_by(PatientMonitoringSnapshot.collected_at.desc())).all()
    latest: dict[str, PatientMonitoringSnapshot] = {}
    for snapshot in snapshots:
        latest.setdefault(snapshot.cd_atendimento, snapshot)
    if latest:
        snapshot_values = list(latest.values())
        open_alerts = db.scalar(select(func.count(Alert.id)).where(Alert.status.in_(["ABERTO", "EM_ANALISE"]))) or 0
        critical_alerts = db.scalar(select(func.count(Alert.id)).where(Alert.severity == "ALTA", Alert.status.in_(["ABERTO", "EM_ANALISE"]))) or 0
        return {
            "monitored_patients": len(snapshot_values),
            "open_alerts": open_alerts,
            "critical_alerts": critical_alerts,
            "high_risk_patients": len([p for p in snapshot_values if p.risk_status == "alto"]),
            "positive_cultures": len([p for p in snapshot_values if p.has_positive_culture]),
            "prolonged_antimicrobials": len([p for p in snapshot_values if p.max_antimicrobial_days > 7]),
        }

    open_alerts = db.scalar(select(func.count(Alert.id)).where(Alert.status.in_(["ABERTO", "EM_ANALISE"]))) or 0
    critical_alerts = db.scalar(select(func.count(Alert.id)).where(Alert.severity == "ALTA", Alert.status.in_(["ABERTO", "EM_ANALISE"]))) or 0
    return {
        "monitored_patients": 0,
        "open_alerts": open_alerts,
        "critical_alerts": critical_alerts,
        "high_risk_patients": 0,
        "positive_cultures": 0,
        "prolonged_antimicrobials": 0,
    }
