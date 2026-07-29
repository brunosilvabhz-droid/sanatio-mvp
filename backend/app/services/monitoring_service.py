import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.patient_monitoring_snapshot import PatientMonitoringSnapshot
from app.models.monitoring_rule import MonitoringRule
from app.services import alert_service, antimicrobial_audit_service, risk_service, soulmv_adapter

RULE_MAP = {
    "ANTIMICROBIAL_DAYS": "antimicrobial_days",
    "ANTIMICROBIAL_GT7": "antimicrobial_days",
    "POSITIVE_CULTURE": "positive_culture",
    "INVASIVE_DEVICE_DAYS": "invasive_device_days",
    "INVASIVE_GT7": "invasive_device_days",
    "LONG_STAY": "long_stay_days",
    "ACTIVE_ISOLATION": "active_isolation",
    "RISK_STATUS": "risk_status",
}


def _int_value(value: str, fallback: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def rule_matches(rule: MonitoringRule, criteria: dict) -> bool:
    if rule.rule_type == "COMPOSITE":
        try:
            selected = json.loads(rule.parameter_value)
        except json.JSONDecodeError:
            return False
        if not isinstance(selected, list) or not selected:
            return False
        values = [bool(criteria.get(str(item))) for item in selected]
        return all(values) if rule.parameter_key == "all" else any(values)

    criterion = RULE_MAP.get(rule.rule_type)
    if not criterion:
        return False
    if criterion in {"positive_culture", "active_isolation"}:
        return bool(criteria.get(criterion))
    if criterion in {"antimicrobial_days", "invasive_device_days", "long_stay_days"}:
        return int(criteria.get(criterion, 0)) >= _int_value(rule.parameter_value)
    if criterion == "risk_status":
        return str(criteria.get(criterion, "")).lower() == str(rule.parameter_value).lower()
    return False


def patient_monitoring_indicators(patient: dict) -> tuple[dict, dict, list[dict]]:
    cd = str(patient["cd_atendimento"])
    antimicrobials = soulmv_adapter.get_antimicrobials(cd)
    cultures = soulmv_adapter.get_cultures(cd)
    procedures = soulmv_adapter.get_invasive_procedures(cd)
    isolations = soulmv_adapter.get_isolations(cd)
    risk = risk_service.calculate_patient_risk(patient, antimicrobials, cultures, procedures, isolations)

    max_antimicrobial_days = max(
        [int(item.get("dias_uso") or 0) for item in antimicrobials if risk_service.active(item)] or [0]
    )
    max_invasive_device_days = max(
        [int(item.get("dias_permanencia") or 0) for item in procedures if risk_service.active(item)] or [0]
    )
    indicators = {
        "positive_culture": any(str(item.get("sn_positivo", "")).upper() == "S" for item in cultures),
        "antimicrobial_days": max_antimicrobial_days,
        "invasive_device_days": max_invasive_device_days,
        "long_stay_days": int(patient.get("dias_internacao") or 0),
        "active_isolation": any(risk_service.active(item) for item in isolations),
        "risk_status": risk["status"],
    }
    return indicators, risk, antimicrobials


def patient_with_risk(patient: dict) -> dict:
    _, risk, _ = patient_monitoring_indicators(patient)
    labels = {
        "positive_culture": "cultura positiva",
        "antimicrobial_gt7": "antimicrobiano por mais de 7 dias",
        "antimicrobial_gt10": "antimicrobiano por mais de 10 dias",
        "invasive_gt7": "procedimento invasivo por mais de 7 dias",
        "invasive_gt14": "procedimento invasivo por mais de 14 dias",
        "long_stay": "internacao por 10 dias ou mais",
        "active_isolation": "isolamento ativo",
    }
    reasons = [label for key, label in labels.items() if risk["criteria"].get(key)]
    return {**patient, "status_risco": risk["status"], "risk_reasons": reasons, "_risk": risk}


def run_monitoring(db: Session, monitoring_run_id: int | None = None) -> dict:
    rules = db.scalars(select(MonitoringRule).where(MonitoringRule.active.is_(True))).all()
    patients = soulmv_adapter.get_patients_internal()
    created = 0

    for patient in patients:
        indicators, _, antimicrobials = patient_monitoring_indicators(patient)
        antimicrobial_audit_service.sync_for_patient(db, patient, antimicrobials, monitoring_run_id)
        db.add(
            PatientMonitoringSnapshot(
                monitoring_run_id=monitoring_run_id,
                cd_atendimento=str(patient["cd_atendimento"]),
                cd_paciente=str(patient["cd_paciente"]),
                unit=patient.get("ds_unidade"),
                risk_status=indicators["risk_status"],
                days_in_hospital=indicators["long_stay_days"],
                has_positive_culture=indicators["positive_culture"],
                max_antimicrobial_days=indicators["antimicrobial_days"],
                max_invasive_device_days=indicators["invasive_device_days"],
                has_active_isolation=indicators["active_isolation"],
            )
        )

        criteria = {
            **indicators,
            "positive_culture": indicators["positive_culture"],
            "antimicrobial_gt7": indicators["antimicrobial_days"] > 7,
            "antimicrobial_gt10": indicators["antimicrobial_days"] > 10,
            "invasive_gt7": indicators["invasive_device_days"] > 7,
            "invasive_gt14": indicators["invasive_device_days"] > 14,
            "long_stay": indicators["long_stay_days"] >= 10,
            "active_isolation": indicators["active_isolation"],
            "high_risk": indicators["risk_status"] == "alto",
        }
        for rule in rules:
            if not rule_matches(rule, criteria):
                continue
            alert = alert_service.create_alert_if_missing(
                db,
                {
                    "cd_atendimento": str(patient["cd_atendimento"]),
                    "cd_paciente": str(patient["cd_paciente"]),
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
