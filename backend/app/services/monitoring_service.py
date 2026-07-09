from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.monitoring_rule import MonitoringRule
from app.services import alert_service, risk_service, soulmv_adapter

RULE_MAP = {
    "ANTIMICROBIAL_GT7": "antimicrobial_gt7",
    "POSITIVE_CULTURE": "positive_culture",
    "INVASIVE_GT7": "invasive_gt7",
    "LONG_STAY": "long_stay",
    "ACTIVE_ISOLATION": "active_isolation",
}


def patient_with_risk(patient: dict) -> dict:
    cd = str(patient["cd_atendimento"])
    antimicrobials = soulmv_adapter.get_antimicrobials(cd)
    cultures = soulmv_adapter.get_cultures(cd)
    procedures = soulmv_adapter.get_invasive_procedures(cd)
    isolations = soulmv_adapter.get_isolations(cd)
    risk = risk_service.calculate_patient_risk(patient, antimicrobials, cultures, procedures, isolations)
    return {**patient, "status_risco": risk["status"], "_risk": risk}


def run_monitoring(db: Session) -> dict:
    rules = db.scalars(select(MonitoringRule).where(MonitoringRule.active.is_(True))).all()
    patients = soulmv_adapter.get_patients()
    created = 0

    for patient in patients:
        enriched = patient_with_risk(patient)
        criteria = enriched["_risk"]["criteria"]
        for rule in rules:
            criterion = RULE_MAP.get(rule.rule_type)
            if not criterion or not criteria.get(criterion):
                continue
            alert = alert_service.create_alert_if_missing(
                db,
                {
                    "cd_atendimento": str(patient["cd_atendimento"]),
                    "cd_paciente": str(patient["cd_paciente"]),
                    "patient_name": patient["nm_paciente"],
                    "unit": patient["ds_unidade"],
                    "rule_id": rule.id,
                    "alert_type": rule.rule_type,
                    "severity": rule.severity,
                    "title": rule.name,
                    "description": rule.description or rule.name,
                    "recommendation": "Avaliar prontuário, conduta e necessidade de intervenção do SCIH.",
                    "status": "ABERTO",
                    "source": "soulmv_views",
                },
            )
            if alert:
                created += 1
    db.commit()
    return {"patients_processed": len(patients), "alerts_created": created}
