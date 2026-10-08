from datetime import datetime, timedelta
from unicodedata import combining, normalize

from app.models.clinical import ProcedimentoInvasivoAtendimento


def _normalized(value: str | None) -> str:
    return "".join(character for character in normalize("NFKD", value or "") if not combining(character)).lower().strip()


def device_kind(procedure: str | None, location: str | None = None) -> str | None:
    name = _normalized(procedure)
    if name == "cvc" or "cateter venoso central" in name or "venoso central" in name:
        return "CVC"
    if name == "vm" or "ventilacao mecanica" in name or "respirador" in name:
        return "VM"
    if name in {"cvd", "svd"} or "sonda vesical" in name or "cateter vesical" in name:
        return "CVD"

    fallback = _normalized(location)
    if "cvc" in fallback or "cateter venoso central" in fallback:
        return "CVC"
    if "ventil" in fallback or "respirador" in fallback:
        return "VM"
    if "cvd" in fallback or "svd" in fallback or "sonda vesical" in fallback:
        return "CVD"
    return None


def effective_end(procedure: ProcedimentoInvasivoAtendimento, attendance_end: datetime | None = None) -> datetime | None:
    end = procedure.data_hora_fim
    if not end and not procedure.ativo:
        end = procedure.data_hora_inicio + timedelta(days=max(procedure.dias_permanencia or 0, 0))
    if attendance_end and (not end or attendance_end < end):
        end = attendance_end
    return end
