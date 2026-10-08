from datetime import datetime, timezone

from app.models.clinical import ProcedimentoInvasivoAtendimento
from app.services.invasive_device import device_kind, effective_end


def test_procedure_name_has_priority_over_location() -> None:
    assert device_kind("VM", "CVC EM VFD") == "VM"
    assert device_kind("CVD", "CVC PUNCIONADO") == "CVD"
    assert device_kind("CVC", "CDL") == "CVC"


def test_inactive_procedure_uses_reported_stay_as_implicit_end() -> None:
    started_at = datetime(2026, 9, 3, tzinfo=timezone.utc)
    procedure = ProcedimentoInvasivoAtendimento(
        atendimento_id=1,
        id_origem_procedimento="1",
        procedimento="CVC",
        data_hora_inicio=started_at,
        ativo=False,
        dias_permanencia=5,
    )
    assert effective_end(procedure) == datetime(2026, 9, 8, tzinfo=timezone.utc)
