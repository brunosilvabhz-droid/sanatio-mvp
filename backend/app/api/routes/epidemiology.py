from fastapi import APIRouter, Depends
from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.clinical import AntimicrobianoAtendimento, CulturaAtendimento
from app.models.user import User

router = APIRouter(prefix="/epidemiology", tags=["Epidemiologia"])


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
                "totalDose": float(days_value),
                "ddd": round(days_value / 10, 2),
                "dot": round(days_value / 10, 2),
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
