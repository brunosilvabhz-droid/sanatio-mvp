from collections.abc import Iterable
from datetime import datetime, timezone

from app.core.config import settings
from app.core.oracle import oracle_connection
from app.services import mock_data

VIEW_COLUMNS = {
    "VW_SANATIO_PACIENTES_INTERNADOS": [
        "cd_atendimento", "cd_paciente", "nm_paciente", "dt_nascimento", "tp_sexo", "dt_atendimento",
        "cd_unidade", "ds_unidade", "cd_leito", "ds_leito", "cd_prestador", "nm_prestador", "cd_convenio", "nm_convenio",
    ],
    "VW_SANATIO_MOVIMENTACOES": [
        "cd_atendimento", "cd_paciente", "dt_movimentacao", "cd_unidade_origem", "ds_unidade_origem",
        "cd_unidade_destino", "ds_unidade_destino", "cd_leito_origem", "ds_leito_origem", "cd_leito_destino", "ds_leito_destino",
    ],
    "VW_SANATIO_ANTIMICROBIANOS": [
        "cd_atendimento", "cd_paciente", "cd_prescricao", "cd_item_prescricao", "cd_produto", "ds_antimicrobiano",
        "dt_inicio", "dt_fim", "sn_ativo", "ds_frequencia", "ds_via", "ds_dose",
    ],
    "VW_SANATIO_CULTURAS": [
        "cd_atendimento", "cd_paciente", "cd_pedido", "cd_exame", "ds_exame", "dt_coleta", "dt_resultado",
        "ds_material", "ds_microorganismo", "ds_resultado", "sn_positivo",
    ],
    "VW_SANATIO_PROCEDIMENTOS_INVASIVOS": [
        "cd_atendimento", "cd_paciente", "cd_procedimento", "ds_procedimento", "dt_inicio", "dt_fim", "sn_ativo", "ds_local_instalacao",
    ],
    "VW_SANATIO_ISOLAMENTOS": [
        "cd_atendimento", "cd_paciente", "cd_isolamento", "ds_isolamento", "dt_inicio", "dt_fim", "sn_ativo",
    ],
}


def _days_since(value) -> int:
    if not value:
        return 0
    now = mock_data.TODAY if settings.use_mock_soulmv else datetime.now(timezone.utc).replace(tzinfo=None)
    return max((now.date() - value.date()).days, 0)


def _oracle_select(view_name: str, where: str = "", params: dict | None = None) -> list[dict]:
    columns = VIEW_COLUMNS[view_name]
    sql = f"SELECT {', '.join(columns)} FROM {view_name} {where}"
    with oracle_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(sql, params or {})
        return [dict(zip(columns, row, strict=False)) for row in cursor.fetchall()]


def _with_patient_metrics(patient: dict) -> dict:
    birth = patient["dt_nascimento"]
    today = mock_data.TODAY.date() if settings.use_mock_soulmv else datetime.now().date()
    return {
        **patient,
        "idade": today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day)),
        "dias_internacao": _days_since(patient["dt_atendimento"]),
    }


def _with_antimicrobial_metrics(row: dict) -> dict:
    end = row.get("dt_fim") or (mock_data.TODAY if settings.use_mock_soulmv else datetime.now())
    return {**row, "dias_uso": max((end.date() - row["dt_inicio"].date()).days, 0)}


def _with_procedure_metrics(row: dict) -> dict:
    end = row.get("dt_fim") or (mock_data.TODAY if settings.use_mock_soulmv else datetime.now())
    return {**row, "dias_permanencia": max((end.date() - row["dt_inicio"].date()).days, 0)}


def get_patients() -> list[dict]:
    rows = mock_data.mock_patients() if settings.use_mock_soulmv else _oracle_select("VW_SANATIO_PACIENTES_INTERNADOS")
    patients = [_with_patient_metrics(row) for row in rows]
    if settings.expose_patient_names_in_api:
        return patients
    return [{**patient, "nm_paciente": None} for patient in patients]


def get_patients_internal() -> list[dict]:
    rows = mock_data.mock_patients() if settings.use_mock_soulmv else _oracle_select("VW_SANATIO_PACIENTES_INTERNADOS")
    return [_with_patient_metrics(row) for row in rows]


def get_patient(cd_atendimento: str) -> dict | None:
    return next((p for p in get_patients() if str(p["cd_atendimento"]) == str(cd_atendimento)), None)


def get_patient_internal(cd_atendimento: str) -> dict | None:
    return next((p for p in get_patients_internal() if str(p["cd_atendimento"]) == str(cd_atendimento)), None)


def _filter(rows: Iterable[dict], cd_atendimento: str) -> list[dict]:
    return [row for row in rows if str(row["cd_atendimento"]) == str(cd_atendimento)]


def get_antimicrobials(cd_atendimento: str) -> list[dict]:
    rows = mock_data.mock_antimicrobials() if settings.use_mock_soulmv else _oracle_select(
        "VW_SANATIO_ANTIMICROBIANOS", "WHERE cd_atendimento = :cd_atendimento", {"cd_atendimento": cd_atendimento}
    )
    return [_with_antimicrobial_metrics(row) for row in _filter(rows, cd_atendimento)]


def get_cultures(cd_atendimento: str) -> list[dict]:
    rows = mock_data.mock_cultures() if settings.use_mock_soulmv else _oracle_select(
        "VW_SANATIO_CULTURAS", "WHERE cd_atendimento = :cd_atendimento", {"cd_atendimento": cd_atendimento}
    )
    return _filter(rows, cd_atendimento)


def get_invasive_procedures(cd_atendimento: str) -> list[dict]:
    rows = mock_data.mock_invasive_procedures() if settings.use_mock_soulmv else _oracle_select(
        "VW_SANATIO_PROCEDIMENTOS_INVASIVOS", "WHERE cd_atendimento = :cd_atendimento", {"cd_atendimento": cd_atendimento}
    )
    return [_with_procedure_metrics(row) for row in _filter(rows, cd_atendimento)]


def get_isolations(cd_atendimento: str) -> list[dict]:
    rows = mock_data.mock_isolations() if settings.use_mock_soulmv else _oracle_select(
        "VW_SANATIO_ISOLAMENTOS", "WHERE cd_atendimento = :cd_atendimento", {"cd_atendimento": cd_atendimento}
    )
    return _filter(rows, cd_atendimento)
