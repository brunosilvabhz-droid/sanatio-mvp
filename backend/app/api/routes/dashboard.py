from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.alert import Alert
from app.models.patient_monitoring_snapshot import PatientMonitoringSnapshot
from app.services import monitoring_service, soulmv_adapter

router = APIRouter(prefix="/dashboard", tags=["Dashboard"], dependencies=[Depends(get_current_user)])


@router.get("/summary")
def summary(db: Session = Depends(get_db)) -> dict:
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

    patients = [monitoring_service.patient_with_risk(p) for p in soulmv_adapter.get_patients()]
    open_alerts = db.scalar(select(func.count(Alert.id)).where(Alert.status.in_(["ABERTO", "EM_ANALISE"]))) or 0
    critical_alerts = db.scalar(select(func.count(Alert.id)).where(Alert.severity == "ALTA", Alert.status.in_(["ABERTO", "EM_ANALISE"]))) or 0
    cultures_positive = sum(len([c for c in soulmv_adapter.get_cultures(p["cd_atendimento"]) if c["sn_positivo"] == "S"]) for p in patients)
    prolonged_antimicrobials = sum(
        len([a for a in soulmv_adapter.get_antimicrobials(p["cd_atendimento"]) if a["sn_ativo"] == "S" and a["dias_uso"] > 7])
        for p in patients
    )
    return {
        "monitored_patients": len(patients),
        "open_alerts": open_alerts,
        "critical_alerts": critical_alerts,
        "high_risk_patients": len([p for p in patients if p["status_risco"] == "alto"]),
        "positive_cultures": cultures_positive,
        "prolonged_antimicrobials": prolonged_antimicrobials,
    }
