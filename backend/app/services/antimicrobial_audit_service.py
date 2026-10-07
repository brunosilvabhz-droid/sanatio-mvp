from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.antimicrobial_audit import AntimicrobialAudit, AntimicrobialAuditAction


PROTECTED_STATUSES = {"JUSTIFICADO", "INTERVENCAO_SUGERIDA", "RESOLVIDO"}


def _active(row: dict) -> bool:
    return str(row.get("sn_ativo", "")).upper() == "S"


def _priority(days_in_use: int) -> str:
    if days_in_use >= 14:
        return "ALTA"
    if days_in_use >= 7:
        return "MEDIA"
    return "BAIXA"


def _initial_status(active: bool, days_in_use: int) -> str:
    if not active:
        return "ENCERRADO"
    if days_in_use >= 7:
        return "PENDENTE"
    return "MONITORADO"


def _aware(value: datetime | None) -> datetime | None:
    if value and value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def treatment_courses(antimicrobials: list[dict], now: datetime | None = None) -> tuple[list[dict], set[tuple[str, str]]]:
    now = _aware(now) or datetime.now(timezone.utc)
    latest_prescriptions: dict[tuple[str, str], dict] = {}
    for item in antimicrobials:
        key = (str(item.get("cd_prescricao") or ""), str(item.get("cd_item_prescricao") or ""))
        if not all(key):
            continue
        current = latest_prescriptions.get(key)
        item_application = _aware(item.get("dt_aplicacao")) or _aware(item.get("dt_inicio"))
        current_application = (_aware(current.get("dt_aplicacao")) or _aware(current.get("dt_inicio"))) if current else None
        if current is None or (item_application and (not current_application or item_application >= current_application)):
            latest_prescriptions[key] = dict(item)

    by_medication: dict[str, list[dict]] = {}
    for item in latest_prescriptions.values():
        medication = str(item.get("ds_principio_ativo") or item.get("ds_antimicrobiano") or "").strip().casefold()
        by_medication.setdefault(medication, []).append(item)

    courses: list[dict] = []
    for prescriptions in by_medication.values():
        prescriptions.sort(key=lambda item: _aware(item.get("dt_inicio")) or datetime.min.replace(tzinfo=timezone.utc))
        episodes: list[list[dict]] = []
        for item in prescriptions:
            start = _aware(item.get("dt_inicio"))
            if not episodes:
                episodes.append([item])
                continue
            previous_ends = [_aware(value.get("dt_fim")) for value in episodes[-1]]
            open_prescription = any(end is None for end in previous_ends)
            episode_end = max((end for end in previous_ends if end), default=None)
            if start and (open_prescription or (episode_end and start <= episode_end + timedelta(days=1))):
                episodes[-1].append(item)
            else:
                episodes.append([item])

        for episode in episodes:
            latest = max(episode, key=lambda item: _aware(item.get("dt_inicio")) or datetime.min.replace(tzinfo=timezone.utc))
            course_start = min(_aware(item.get("dt_inicio")) for item in episode if item.get("dt_inicio"))
            latest_end = _aware(latest.get("dt_fim"))
            active = _active(latest) and (latest_end is None or latest_end > now)
            course_end = now if active else max((_aware(item.get("dt_fim")) for item in episode if item.get("dt_fim")), default=now)
            consolidated = dict(latest)
            consolidated["sn_ativo"] = "S" if active else "N"
            consolidated["dias_uso"] = max((min(course_end, now).date() - course_start.date()).days, 0)
            courses.append(consolidated)
    return courses, set(latest_prescriptions)


def sync_for_patient(db: Session, patient: dict, antimicrobials: list[dict], monitoring_run_id: int | None = None) -> int:
    synced = 0
    patient_active = bool(patient.get("active", True))
    courses, prescription_keys = treatment_courses(antimicrobials)
    existing_audits = list(db.scalars(select(AntimicrobialAudit).where(
        AntimicrobialAudit.cd_prescricao.in_({key[0] for key in prescription_keys}),
        AntimicrobialAudit.cd_item_prescricao.in_({key[1] for key in prescription_keys}),
    ))) if prescription_keys else []
    for audit in existing_audits:
        if (audit.cd_prescricao, audit.cd_item_prescricao) in prescription_keys and audit.status not in PROTECTED_STATUSES:
            audit.active = False
            audit.status = "ENCERRADO"

    for item in courses:
        cd_prescricao = str(item.get("cd_prescricao") or "")
        cd_item_prescricao = str(item.get("cd_item_prescricao") or "")
        if not cd_prescricao or not cd_item_prescricao:
            continue

        active = patient_active and _active(item)
        days_in_use = int(item.get("dias_uso") or 0)
        audit = db.scalar(
            select(AntimicrobialAudit).where(
                AntimicrobialAudit.cd_prescricao == cd_prescricao,
                AntimicrobialAudit.cd_item_prescricao == cd_item_prescricao,
            )
        )
        if not audit:
            audit = AntimicrobialAudit(
                cd_prescricao=cd_prescricao,
                cd_item_prescricao=cd_item_prescricao,
                status=_initial_status(active, days_in_use),
            )
            db.add(audit)
            synced += 1
        elif active and audit.status == "ENCERRADO":
            audit.status = _initial_status(True, days_in_use)
        elif audit.status == "MONITORADO" and active and days_in_use >= 7:
            audit.status = "PENDENTE"

        audit.monitoring_run_id = monitoring_run_id
        audit.cd_atendimento = str(patient["cd_atendimento"])
        audit.cd_paciente = str(patient["cd_paciente"])
        audit.unit = patient.get("ds_unidade")
        audit.cd_produto = str(item.get("cd_produto") or "") or None
        audit.antimicrobial_name = str(item.get("ds_antimicrobiano") or "Antimicrobiano nao identificado")
        audit.started_at = item["dt_inicio"]
        audit.ended_at = item.get("dt_fim")
        audit.days_in_use = days_in_use
        audit.active = active
        audit.dose = item.get("ds_dose")
        audit.route = item.get("ds_via")
        audit.frequency = item.get("ds_frequencia")
        audit.priority = _priority(days_in_use)

        if not active and audit.status not in PROTECTED_STATUSES:
            audit.status = "ENCERRADO"

    return synced


def update_audit(
    db: Session,
    audit: AntimicrobialAudit,
    user_id: int,
    status: str,
    decision: str | None,
    comment: str,
) -> AntimicrobialAudit:
    audit.status = status
    audit.decision = decision
    audit.justification = comment
    audit.reviewed_by_user_id = user_id
    audit.reviewed_at = datetime.now(timezone.utc)
    db.add(
        AntimicrobialAuditAction(
            audit_id=audit.id,
            user_id=user_id,
            action="AUDIT_UPDATE",
            status=status,
            decision=decision,
            comment=comment,
        )
    )
    db.commit()
    db.refresh(audit)
    return audit
