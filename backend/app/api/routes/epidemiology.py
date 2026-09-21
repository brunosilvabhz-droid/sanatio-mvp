from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.clinical import AntimicrobianoAtendimento, Atendimento, CulturaAtendimento, ProcedimentoInvasivoAtendimento
from app.models.user import User

router = APIRouter(prefix="/epidemiology", tags=["Epidemiologia"])


def _device_kind(value: str) -> str | None:
    normalized = value.lower()
    if any(term in normalized for term in ("cvc", "cateter venoso central", "venoso central")):
        return "CVC"
    if any(term in normalized for term in ("ventil", "respirador", "ventilacao mecanica", " vm ")):
        return "VM"
    if any(term in normalized for term in ("cvd", "sonda vesical", "cateter vesical", "demora")):
        return "SVD"
    return None


def _month_period(periodo: str) -> tuple[datetime, datetime]:
    year, month = [int(part) for part in periodo.split("-")]
    start = datetime(year, month, 1, tzinfo=timezone.utc)
    end = datetime(year + (month == 12), 1 if month == 12 else month + 1, 1, tzinfo=timezone.utc)
    return start, end


def _overlap_days(start: datetime, end: datetime | None, period_start: datetime, period_end: datetime) -> int:
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    if end and end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)
    overlap_start = max(start, period_start)
    overlap_end = min(end or period_end, period_end)
    return max((overlap_end.date() - overlap_start.date()).days, 1) if overlap_end > overlap_start else 0


@router.get("/device-usage")
def device_usage(
    periodo: str = Query(default_factory=lambda: date.today().strftime("%Y-%m"), pattern=r"^\d{4}-\d{2}$"),
    unidade: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> dict:
    start, end = _month_period(periodo)
    stmt = (
        select(ProcedimentoInvasivoAtendimento, Atendimento)
        .join(Atendimento, Atendimento.id == ProcedimentoInvasivoAtendimento.atendimento_id)
        .where(
            ProcedimentoInvasivoAtendimento.data_hora_inicio < end,
            (ProcedimentoInvasivoAtendimento.data_hora_fim.is_(None))
            | (ProcedimentoInvasivoAtendimento.data_hora_fim >= start),
        )
    )
    if unidade:
        stmt = stmt.where(Atendimento.unidade_atual == unidade)
    totals = {"CVC": 0, "VM": 0, "SVD": 0}
    units: dict[str, dict[str, int]] = {}
    for procedure, attendance in db.execute(stmt).all():
        kind = _device_kind(f"{procedure.procedimento} {procedure.local_instalacao or ''}")
        if not kind:
            continue
        days = _overlap_days(procedure.data_hora_inicio, procedure.data_hora_fim, start, end)
        totals[kind] += days
        unit = attendance.unidade_atual or "Unidade não informada"
        units.setdefault(unit, {"CVC": 0, "VM": 0, "SVD": 0})[kind] += days
    return {
        "periodo": periodo,
        "unidade": unidade,
        "totais": {"cvc_dia": totals["CVC"], "vm_dia": totals["VM"], "svd_dia": totals["SVD"]},
        "por_unidade": [
            {"unidade": name, "cvc_dia": values["CVC"], "vm_dia": values["VM"], "svd_dia": values["SVD"]}
            for name, values in sorted(units.items())
        ],
    }


def _classify_antimicrobial(name: str) -> str:
    value = name.lower()
    if "mero" in value or "imipenem" in value or "ertapenem" in value:
        return "Carbapenemicos"
    if "vanco" in value:
        return "Glicopeptideos"
    if "cef" in value or "triax" in value:
        return "Cefalosporinas"
    if "clinda" in value:
        return "Lincosamidas"
    if "polimix" in value:
        return "Polimixinas"
    if "piperacilina" in value or "tazobactam" in value:
        return "Penicilinas"
    return "Outros"


def _resistance_group(microorganism: str | None) -> str | None:
    if not microorganism:
        return None
    value = microorganism.lower()
    if "esbl" in value:
        return "Enterobacterias produtoras de ESBL"
    if "carbapenem" in value and "acinetobacter" in value:
        return "Acinetobacter spp. resistente a carbapenemicos"
    if "carbapenem" in value and "pseudomonas" in value:
        return "P. aeruginosa resistente a carbapenemicos"
    if "oxacilina" in value or "mrsa" in value:
        return "S. aureus resistente a Oxacilina/Meticilina"
    if "carbapenemase" in value:
        return "Enterobacterias produtoras de Carbapenemase"
    return microorganism


@router.get("/summary")
def summary(db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> dict:
    antimicrobial_rows = db.execute(
        select(
            AntimicrobianoAtendimento.nome_antimicrobiano,
            func.count(distinct(AntimicrobianoAtendimento.atendimento_id)),
            func.sum(AntimicrobianoAtendimento.dias_uso),
        )
        .group_by(AntimicrobianoAtendimento.nome_antimicrobiano)
        .order_by(func.sum(AntimicrobianoAtendimento.dias_uso).desc())
    ).all()
    consumption = []
    total_days = 0
    for name, patients, days in antimicrobial_rows:
        days_value = int(days or 0)
        total_days += days_value
        consumption.append(
            {
                "className": _classify_antimicrobial(name),
                "antimicrobial": name,
                "patients": int(patients or 0),
                "days": days_value,
                "totalDose": 0.0,
                "ddd": 0.0,
                "dot": float(days_value),
            }
        )

    positive_cultures = db.scalars(select(CulturaAtendimento).where(CulturaAtendimento.positivo.is_(True))).all()
    groups: dict[str, int] = {}
    for culture in positive_cultures:
        group = _resistance_group(culture.microorganismo)
        if group:
            groups[group] = groups.get(group, 0) + 1
    total_positive = sum(groups.values()) or 1
    pathogens = [
        {
            "label": label,
            "value": f"{(count / total_positive) * 100:.1f}% ({count})",
            "rate": f"{count} culturas positivas",
        }
        for label, count in sorted(groups.items(), key=lambda item: item[1], reverse=True)
    ]

    return {
        "consumptionRows": consumption,
        "pathogenCards": pathogens,
        "totalDays": total_days,
        "patientDays": 0,
        "therapyDuration": round(total_days / max(len(consumption), 1), 2),
    }
