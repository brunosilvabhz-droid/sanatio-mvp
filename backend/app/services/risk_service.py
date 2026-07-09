def active(row: dict) -> bool:
    return str(row.get("sn_ativo", "")).upper() == "S"


def calculate_patient_risk(
    patient: dict,
    antimicrobials: list[dict],
    cultures: list[dict],
    invasive_procedures: list[dict],
    isolations: list[dict],
) -> dict:
    positive_culture = any(str(c.get("sn_positivo", "")).upper() == "S" for c in cultures)
    antimicrobial_gt7 = any(active(a) and a.get("dias_uso", 0) > 7 for a in antimicrobials)
    antimicrobial_gt10 = any(active(a) and a.get("dias_uso", 0) > 10 for a in antimicrobials)
    invasive_gt7 = any(active(p) and p.get("dias_permanencia", 0) > 7 for p in invasive_procedures)
    invasive_gt14 = any(active(p) and p.get("dias_permanencia", 0) > 14 for p in invasive_procedures)
    long_stay = patient.get("dias_internacao", 0) >= 10
    active_isolation = any(active(i) for i in isolations)

    medium_criteria = [antimicrobial_gt7, long_stay, invasive_gt7]
    high_criteria = [positive_culture, antimicrobial_gt10, invasive_gt14, active_isolation, sum(medium_criteria) >= 2]

    if any(high_criteria):
        status = "alto"
    elif any(medium_criteria):
        status = "medio"
    else:
        status = "baixo"

    return {
        "status": status,
        "criteria": {
            "positive_culture": positive_culture,
            "antimicrobial_gt7": antimicrobial_gt7,
            "antimicrobial_gt10": antimicrobial_gt10,
            "invasive_gt7": invasive_gt7,
            "invasive_gt14": invasive_gt14,
            "long_stay": long_stay,
            "active_isolation": active_isolation,
        },
    }
