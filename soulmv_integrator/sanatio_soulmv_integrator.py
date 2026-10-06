from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from typing import Any
from urllib import error, request

from dotenv import load_dotenv


LOG = logging.getLogger("sanatio_soulmv_integrator")


DEFAULT_CONFIG = "config.hml.json"

LEGACY_VIEW_NAMES = {
    "VW_SANATIO_PACIENTES_ATENDIMENTOS": "SANATIO.VW_PACIENTES_ATENDIMENTOS",
    "VW_SANATIO_MOVIMENTACOES_LEITO": "SANATIO.VW_MOVIMENTACOES_LEITO",
    "VW_SANATIO_ANTIMICROBIANOS": "SANATIO.VW_ANTIMICROBIANOS",
    "VW_SANATIO_CULTURAS": "SANATIO.VW_CULTURAS",
    "VW_SANATIO_SOLICITACOES_EXAMES": "SANATIO.VW_SOLICITACOES_EXAMES",
    "VW_SANATIO_PROCEDIMENTOS_INVASIVOS": "SANATIO.VW_PROCEDIMENTOS_INVASIVOS",
    "VW_SANATIO_ISOLAMENTOS": "SANATIO.VW_ISOLAMENTOS",
}


@dataclass(frozen=True)
class QuerySpec:
    key: str
    required_columns: tuple[str, ...]
    sql: str
    params: dict[str, Any]


def normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    return {str(key).lower(): value for key, value in row.items()}


def parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().upper() in {"S", "Y", "YES", "TRUE", "1", "ATIVO"}


def iso(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day).isoformat()
    return str(value)


def safe_int(value: Any, default: int = 0) -> int:
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def as_date(value: Any) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return datetime.fromisoformat(str(value)).date()
    except ValueError:
        return None


def days_between(start: Any, end: Any | None = None, reference_date: date | None = None) -> int:
    if not start:
        return 0
    if isinstance(start, datetime):
        start_date = start.date()
    elif isinstance(start, date):
        start_date = start
    else:
        try:
            start_date = datetime.fromisoformat(str(start)).date()
        except ValueError:
            return 0

    if end:
        if isinstance(end, datetime):
            end_date = end.date()
        elif isinstance(end, date):
            end_date = end
        else:
            try:
                end_date = datetime.fromisoformat(str(end)).date()
            except ValueError:
                end_date = datetime.now().date()
    else:
        end_date = reference_date or datetime.now().date()
    return max((end_date - start_date).days, 0)


def active_on(start: Any, end: Any | None, reference_date: date) -> bool:
    start_date = as_date(start)
    end_date = as_date(end)
    return bool(start_date and start_date <= reference_date and (end_date is None or end_date > reference_date))


def load_config(path: str) -> dict[str, Any]:
    with open(path, encoding="utf-8") as file:
        config = json.load(file)

    config["database"]["engine"] = os.getenv("SOULMV_DB_ENGINE", config["database"].get("engine", "oracle")).lower()
    config["database"]["dsn"] = os.getenv("SOULMV_DSN", config["database"].get("dsn", ""))
    config["sanatio"]["ingest_url"] = os.getenv("SANATIO_INGEST_URL", config["sanatio"].get("ingest_url", ""))
    config["sanatio"]["token"] = os.getenv("SANATIO_TOKEN", config["sanatio"].get("token", ""))
    try:
        lookback_days = int(os.getenv("SOULMV_LOOKBACK_DAYS", config.get("query", {}).get("lookback_days", 2)))
    except (TypeError, ValueError) as exc:
        raise ValueError("SOULMV_LOOKBACK_DAYS deve ser um numero inteiro") from exc
    if not 0 <= lookback_days <= 90:
        raise ValueError("SOULMV_LOOKBACK_DAYS deve ficar entre 0 e 90")
    config.setdefault("query", {})["lookback_days"] = lookback_days
    config["views"] = {
        key: LEGACY_VIEW_NAMES.get(value, value)
        for key, value in config["views"].items()
    }
    return config


def quote_view(view_name: str) -> str:
    if not view_name.replace("_", "").replace(".", "").isalnum():
        raise ValueError(f"Nome de view invalido: {view_name}")
    return view_name


def _bind(engine: str, name: str) -> str:
    return f":{name}" if engine == "oracle" else f"%({name})s"


def _query_window(
    engine: str,
    lookback_days: int,
    historical_start: date | None = None,
    historical_end: date | None = None,
) -> tuple[dict[str, str], dict[str, Any]]:
    if historical_start and historical_end:
        start_at = datetime.combine(historical_start, time.min)
        end_at = datetime.combine(historical_end + timedelta(days=1), time.min)
        start = _bind(engine, "window_start")
        end = _bind(engine, "window_end")
        return {
            "patients": f"dt_atendimento < {end} AND (dt_alta IS NULL OR dt_alta >= {start})",
            "bed_movements": f"dt_movimentacao >= {start} AND dt_movimentacao < {end}",
            "antimicrobials": f"dt_inicio < {end} AND (dt_fim IS NULL OR dt_fim >= {start})",
            "cultures": f"(dt_coleta >= {start} AND dt_coleta < {end}) OR (dt_resultado >= {start} AND dt_resultado < {end})",
            "exam_requests": f"dt_solicitacao >= {start} AND dt_solicitacao < {end}",
            "invasive_procedures": f"dt_inicio < {end} AND (dt_fim IS NULL OR dt_fim >= {start})",
            "isolations": f"dt_inicio < {end} AND (dt_fim IS NULL OR dt_fim >= {start})",
        }, {"window_start": start_at, "window_end": end_at}

    if lookback_days == 0:
        return {}, {}

    days = _bind(engine, "lookback_days")
    start = f"SYSDATE - {days}" if engine == "oracle" else f"CURRENT_TIMESTAMP - ({days} * INTERVAL '1 day')"
    return {
        "patients": f"dt_alta IS NULL OR dt_alta >= {start} OR dt_atendimento >= {start}",
        "bed_movements": f"dt_movimentacao >= {start}",
        "antimicrobials": f"dt_fim IS NULL OR dt_fim >= {start} OR dt_inicio >= {start} OR dt_aplicacao >= {start}",
        "cultures": f"dt_coleta >= {start} OR dt_resultado >= {start}",
        "exam_requests": f"dt_solicitacao >= {start}",
        "invasive_procedures": f"dt_fim IS NULL OR dt_fim >= {start} OR dt_inicio >= {start}",
        "isolations": f"dt_fim IS NULL OR dt_fim >= {start} OR dt_inicio >= {start}",
    }, {"lookback_days": lookback_days}


def query_specs(
    views: dict[str, str],
    engine: str,
    lookback_days: int,
    historical_start: date | None = None,
    historical_end: date | None = None,
) -> list[QuerySpec]:
    patients = quote_view(views["patients"])
    bed_movements = quote_view(views["bed_movements"])
    antimicrobials = quote_view(views["antimicrobials"])
    cultures = quote_view(views["cultures"]) if views.get("cultures") else None
    invasive = quote_view(views["invasive_procedures"]) if views.get("invasive_procedures") else None
    isolations = quote_view(views["isolations"]) if views.get("isolations") else None
    filters, params = _query_window(engine, lookback_days, historical_start, historical_end)

    def where(key: str) -> str:
        return f"WHERE ({filters[key]})" if key in filters else ""

    specs = [
        QuerySpec(
            key="patients",
            required_columns=("cd_atendimento", "cd_paciente", "dt_atendimento", "dt_alta", "ds_unidade", "ds_leito"),
            sql=f"""
                SELECT
                    cd_atendimento,
                    cd_paciente,
                    dt_atendimento,
                    dt_alta,
                    ds_unidade,
                    ds_leito
                FROM {patients}
                {where("patients")}
            """,
            params=params,
        ),
        QuerySpec(
            key="bed_movements",
            required_columns=("cd_atendimento", "cd_paciente", "dt_movimentacao"),
            sql=f"""
                SELECT
                    cd_atendimento,
                    cd_paciente,
                    dt_movimentacao,
                    ds_unidade_origem,
                    ds_leito_origem,
                    ds_unidade_destino,
                    ds_leito_destino
                FROM {bed_movements}
                {where("bed_movements")}
            """,
            params=params,
        ),
        QuerySpec(
            key="antimicrobials",
            required_columns=(
                "cd_atendimento",
                "cd_paciente",
                "cd_prescricao",
                "cd_item_prescricao",
                "ds_antimicrobiano",
                "ds_principio_ativo",
                "dt_inicio",
                "dt_aplicacao",
            ),
            sql=f"""
                SELECT *
                FROM {antimicrobials}
                {where("antimicrobials")}
            """,
            params=params,
        ),
    ]
    if invasive:
        specs.append(QuerySpec(
            key="invasive_procedures",
            required_columns=("cd_atendimento", "cd_paciente", "cd_procedimento", "ds_procedimento", "dt_inicio"),
            sql=f"""
                SELECT
                    cd_atendimento,
                    cd_paciente,
                    cd_procedimento,
                    ds_procedimento,
                    dt_inicio,
                    dt_fim,
                    sn_ativo,
                    ds_local_instalacao
                FROM {invasive}
                {where("invasive_procedures")}
            """,
            params=params,
        ))
    if isolations:
        specs.append(QuerySpec(
            key="isolations",
            required_columns=("cd_atendimento", "cd_paciente", "cd_isolamento", "ds_isolamento", "dt_inicio"),
            sql=f"""
                SELECT
                    cd_atendimento,
                    cd_paciente,
                    cd_isolamento,
                    ds_isolamento,
                    dt_inicio,
                    dt_fim,
                    sn_ativo
                FROM {isolations}
                {where("isolations")}
            """,
            params=params,
        ))
    if cultures:
        specs.append(QuerySpec(
            key="cultures",
            required_columns=("cd_atendimento", "cd_paciente", "cd_pedido", "cd_exame", "ds_exame", "dt_coleta"),
            sql=f"""
                SELECT cd_atendimento, cd_paciente, cd_pedido, cd_exame,
                       ds_exame, dt_coleta, dt_resultado, ds_material,
                       ds_resultado, ds_microorganismo, sn_positivo
                FROM {cultures}
                {where("cultures")}
            """,
            params=params,
        ))
    if views.get("exam_requests"):
        requests = quote_view(views["exam_requests"])
        specs.append(QuerySpec(
            key="exam_requests",
            required_columns=("cd_atendimento", "cd_paciente", "cd_pedido"),
            sql=f"SELECT cd_atendimento, cd_paciente, cd_pedido, dt_solicitacao FROM {requests} {where('exam_requests')}",
            params=params,
        ))
    return specs


def connect(engine: str, dsn: str):
    if engine == "postgres":
        import psycopg
        from psycopg.rows import dict_row

        return psycopg.connect(dsn, row_factory=dict_row)
    if engine == "oracle":
        import oracledb

        if os.getenv("SOULMV_ORACLE_THICK", "false").strip().lower() in {"1", "true", "yes", "sim"}:
            oracledb.init_oracle_client()
            LOG.info("Oracle Client inicializado em modo Thick: %s", oracledb.clientversion())
        return oracledb.connect(dsn)
    raise ValueError("database.engine deve ser 'oracle' ou 'postgres'")


def fetch_rows(conn, engine: str, spec: QuerySpec) -> list[dict[str, Any]]:
    LOG.info("Lendo %s", spec.key)
    if engine == "postgres":
        rows = conn.execute(spec.sql, spec.params).fetchall()
        normalized = [normalize_row(dict(row)) for row in rows]
    else:
        cursor = conn.cursor()
        cursor.execute(spec.sql, spec.params)
        columns = [column[0].lower() for column in cursor.description]
        normalized = [dict(zip(columns, row)) for row in cursor.fetchall()]
        cursor.close()

    for column in spec.required_columns:
        if normalized and column not in normalized[0]:
            raise RuntimeError(f"View de {spec.key} nao retornou o alias obrigatorio '{column}'")
    LOG.info("%s: %s linhas", spec.key, len(normalized))
    return normalized


def calculate_risk(
    patient: dict[str, Any],
    rows: dict[str, list[dict[str, Any]]],
    thresholds: dict[str, int],
    reference_date: date | None = None,
) -> dict[str, Any]:
    cd_atendimento = str(patient["cd_atendimento"])
    cultures = [row for row in rows.get("cultures", []) if str(row["cd_atendimento"]) == cd_atendimento]
    antimicrobials = [row for row in rows["antimicrobials"] if str(row["cd_atendimento"]) == cd_atendimento]
    invasive = [row for row in rows.get("invasive_procedures", []) if str(row["cd_atendimento"]) == cd_atendimento]
    isolations = [row for row in rows.get("isolations", []) if str(row["cd_atendimento"]) == cd_atendimento]

    if reference_date:
        active_antimicrobials = [row for row in antimicrobials if active_on(row.get("dt_inicio"), row.get("dt_fim"), reference_date)]
        active_invasive = [row for row in invasive if active_on(row.get("dt_inicio"), row.get("dt_fim"), reference_date)]
        active_isolations = [row for row in isolations if active_on(row.get("dt_inicio"), row.get("dt_fim"), reference_date)]
        cultures = [row for row in cultures if (as_date(row.get("dt_coleta")) or reference_date) <= reference_date]
    else:
        active_antimicrobials = [row for row in antimicrobials if parse_bool(row.get("sn_ativo")) and not row.get("dt_fim")]
        active_invasive = [row for row in invasive if parse_bool(row.get("sn_ativo")) and not row.get("dt_fim")]
        active_isolations = [row for row in isolations if parse_bool(row.get("sn_ativo")) and not row.get("dt_fim")]

    max_antimicrobial_days = max([days_between(row.get("dt_inicio"), None, reference_date) if reference_date else safe_int(row.get("dias_uso"), days_between(row.get("dt_inicio"), row.get("dt_fim"))) for row in active_antimicrobials] or [0])
    max_invasive_device_days = max([days_between(row.get("dt_inicio"), None, reference_date) if reference_date else safe_int(row.get("dias_permanencia"), days_between(row.get("dt_inicio"), row.get("dt_fim"))) for row in active_invasive] or [0])
    discharge = patient.get("dt_alta")
    if reference_date and as_date(discharge) and as_date(discharge) > reference_date:
        discharge = None
    days_in_hospital = days_between(patient.get("dt_atendimento"), discharge, reference_date)
    has_positive_culture = any(parse_bool(row.get("sn_positivo")) for row in cultures)
    has_active_isolation = bool(active_isolations)

    high = (
        has_positive_culture
        or max_antimicrobial_days >= thresholds["antimicrobial_days_high"]
        or max_invasive_device_days >= thresholds["invasive_device_days_high"]
        or days_in_hospital >= thresholds["hospital_stay_days_high"]
        or has_active_isolation
    )
    medium = max_antimicrobial_days >= thresholds["antimicrobial_days_medium"] or days_in_hospital >= thresholds["hospital_stay_days_medium"]
    risk_status = "alto" if high else "medio" if medium else "baixo"

    return {
        "risk_status": risk_status,
        "days_in_hospital": days_in_hospital,
        "has_positive_culture": has_positive_culture,
        "max_antimicrobial_days": max_antimicrobial_days,
        "max_invasive_device_days": max_invasive_device_days,
        "has_active_isolation": has_active_isolation,
    }


def build_payload(
    rows: dict[str, list[dict[str, Any]]],
    thresholds: dict[str, int],
    reference_date: date | None = None,
) -> dict[str, Any]:
    patients = []
    for row in rows["patients"]:
        unit = row.get("ds_unidade")
        bed = row.get("ds_leito")
        if reference_date:
            movements = [
                movement for movement in rows.get("bed_movements", [])
                if str(movement.get("cd_atendimento")) == str(row["cd_atendimento"])
                and as_date(movement.get("dt_movimentacao"))
                and as_date(movement.get("dt_movimentacao")) <= reference_date
            ]
            if movements:
                latest_movement = max(movements, key=lambda item: str(item.get("dt_movimentacao")))
                unit = latest_movement.get("ds_unidade_destino") or unit
                bed = latest_movement.get("ds_leito_destino") or bed
        patient = {
            "cd_atendimento": str(row["cd_atendimento"]),
            "cd_paciente": str(row["cd_paciente"]),
            "unit": unit,
            "bed": bed,
            "active": active_on(row.get("dt_atendimento"), row.get("dt_alta"), reference_date) if reference_date else row.get("dt_alta") is None,
            "admitted_at": iso(row.get("dt_atendimento")),
            "discharged_at": iso(row.get("dt_alta")),
        }
        patient.update(calculate_risk(row, rows, thresholds, reference_date))
        patients.append(patient)

    return {
        "patients": patients,
        "bed_movements": [
            {
                "cd_atendimento": str(row["cd_atendimento"]),
                "cd_paciente": str(row["cd_paciente"]),
                "moved_at": iso(row["dt_movimentacao"]),
                "from_unit": row.get("ds_unidade_origem"),
                "from_bed": row.get("ds_leito_origem"),
                "to_unit": row.get("ds_unidade_destino"),
                "to_bed": row.get("ds_leito_destino"),
            }
            for row in rows["bed_movements"]
        ],
        "antimicrobials": [
            {
                "cd_atendimento": str(row["cd_atendimento"]),
                "cd_paciente": str(row["cd_paciente"]),
                "cd_prescricao": str(row["cd_prescricao"]),
                "cd_item_prescricao": str(row["cd_item_prescricao"]),
                "cd_produto": str(row["cd_produto"]) if row.get("cd_produto") is not None else None,
                "ds_antimicrobiano": row["ds_antimicrobiano"],
                "ds_principio_ativo": row.get("ds_principio_ativo"),
                "dt_inicio": iso(row["dt_inicio"]),
                "dt_aplicacao": iso(row["dt_aplicacao"]),
                "dt_fim": iso(row.get("dt_fim")),
                "sn_ativo": "S" if (active_on(row.get("dt_inicio"), row.get("dt_fim"), reference_date) if reference_date else parse_bool(row.get("sn_ativo", "S"))) else "N",
                "ds_frequencia": row.get("ds_frequencia"),
                "ds_via": row.get("ds_via"),
                "ds_dose": row.get("ds_dose"),
                "dias_uso": days_between(row.get("dt_inicio"), None, reference_date) if reference_date and active_on(row.get("dt_inicio"), row.get("dt_fim"), reference_date) else safe_int(row.get("dias_uso"), days_between(row.get("dt_inicio"), row.get("dt_fim"))),
            }
            for row in rows["antimicrobials"]
        ],
        "cultures": [
            {
                "cd_atendimento": str(row["cd_atendimento"]),
                "cd_paciente": str(row["cd_paciente"]),
                "cd_pedido": str(row["cd_pedido"]),
                "cd_exame": str(row["cd_exame"]),
                "ds_exame": row["ds_exame"],
                "dt_coleta": iso(row["dt_coleta"]),
                "dt_resultado": iso(row.get("dt_resultado")),
                "ds_material": row.get("ds_material"),
                "ds_microorganismo": row.get("ds_microorganismo"),
                "ds_resultado": row.get("ds_resultado"),
                "sn_positivo": "S" if parse_bool(row.get("sn_positivo")) else "N",
            }
            for row in rows.get("cultures", [])
        ],
        "exam_requests": [
            {
                "cd_atendimento": str(row["cd_atendimento"]),
                "cd_paciente": str(row["cd_paciente"]),
                "cd_pedido": str(row["cd_pedido"]),
                "dt_solicitacao": iso(row.get("dt_solicitacao")),
            }
            for row in rows.get("exam_requests", [])
        ],
        "invasive_procedures": [
            {
                "cd_atendimento": str(row["cd_atendimento"]),
                "cd_paciente": str(row["cd_paciente"]),
                "cd_procedimento": str(row["cd_procedimento"]),
                "ds_procedimento": row["ds_procedimento"],
                "dt_inicio": iso(row["dt_inicio"]),
                "dt_fim": iso(row.get("dt_fim")),
                "sn_ativo": "S" if (active_on(row.get("dt_inicio"), row.get("dt_fim"), reference_date) if reference_date else parse_bool(row.get("sn_ativo", "S"))) else "N",
                "ds_local_instalacao": row.get("ds_local_instalacao"),
                "dias_permanencia": days_between(row.get("dt_inicio"), None, reference_date) if reference_date and active_on(row.get("dt_inicio"), row.get("dt_fim"), reference_date) else safe_int(row.get("dias_permanencia"), days_between(row.get("dt_inicio"), row.get("dt_fim"))),
            }
            for row in rows.get("invasive_procedures", [])
        ],
        "isolations": [
            {
                "cd_atendimento": str(row["cd_atendimento"]),
                "cd_paciente": str(row["cd_paciente"]),
                "cd_isolamento": str(row["cd_isolamento"]),
                "ds_isolamento": row["ds_isolamento"],
                "dt_inicio": iso(row["dt_inicio"]),
                "dt_fim": iso(row.get("dt_fim")),
                "sn_ativo": "S" if (active_on(row.get("dt_inicio"), row.get("dt_fim"), reference_date) if reference_date else parse_bool(row.get("sn_ativo", "S"))) else "N",
            }
            for row in rows.get("isolations", [])
        ],
    }


def filter_historical_rows(
    rows: dict[str, list[dict[str, Any]]],
    start_date: date,
    end_date: date,
) -> dict[str, list[dict[str, Any]]]:
    patients = []
    attendance_ids: set[str] = set()
    for row in rows["patients"]:
        admitted_at = as_date(row.get("dt_atendimento"))
        discharged_at = as_date(row.get("dt_alta"))
        if admitted_at and admitted_at <= end_date and (discharged_at is None or discharged_at >= start_date):
            patients.append(row)
            attendance_ids.add(str(row["cd_atendimento"]))

    filtered = {"patients": patients}
    for key, items in rows.items():
        if key == "patients":
            continue
        filtered[key] = [item for item in items if str(item.get("cd_atendimento")) in attendance_ids]
    return filtered


def split_payload(
    payload: dict[str, Any],
    batch_size: int,
    batch_prefix: str,
    reference_at: datetime,
) -> list[dict[str, Any]]:
    patients = payload["patients"]
    if batch_size < 1:
        raise ValueError("batch_size deve ser maior que zero")
    total = max((len(patients) + batch_size - 1) // batch_size, 1)
    batches = []
    detail_keys = ("bed_movements", "antimicrobials", "cultures", "exam_requests", "invasive_procedures", "isolations")
    for index in range(total):
        selected = patients[index * batch_size:(index + 1) * batch_size]
        attendance_ids = {item["cd_atendimento"] for item in selected}
        batch = {
            "modo_carga": "HISTORICA",
            "data_referencia": reference_at.isoformat(),
            "chave_lote": f"{batch_prefix}:parte-{index + 1:04d}-de-{total:04d}",
            "patients": selected,
        }
        for key in detail_keys:
            batch[key] = [item for item in payload.get(key, []) if item["cd_atendimento"] in attendance_ids]
        batches.append(batch)
    return batches


def post_payload(ingest_url: str, token: str, payload: dict[str, Any]) -> dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(
        ingest_url,
        data=body,
        headers={"Content-Type": "application/json", "X-Sanatio-Token": token},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"SANATIO retornou HTTP {exc.code}: {detail}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Nao foi possivel conectar ao SANATIO: {exc}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description="Integrador MV SOUL -> SANATIO.")
    parser.add_argument("--config", default=DEFAULT_CONFIG, help="Arquivo JSON de configuracao.")
    parser.add_argument("--dry-run", action="store_true", help="Monta o payload e imprime no console sem enviar.")
    parser.add_argument("--output", help="Arquivo para salvar o payload JSON montado.")
    parser.add_argument("--historical-start", help="Inicio da carga historica no formato AAAA-MM-DD.")
    parser.add_argument("--historical-end", help="Fim da carga historica no formato AAAA-MM-DD.")
    parser.add_argument("--batch-size", type=int, default=500, help="Pacientes por lote na carga historica.")
    parser.add_argument("--log-level", default=os.getenv("LOG_LEVEL", "INFO"), help="Nivel de log.")
    args = parser.parse_args()

    load_dotenv(os.getenv("SANATIO_ENV_FILE", ".env.integrador"))

    historical = bool(args.historical_start or args.historical_end)
    if historical and not (args.historical_start and args.historical_end):
        parser.error("--historical-start e --historical-end devem ser informados juntos")
    if args.batch_size < 1:
        parser.error("--batch-size deve ser maior que zero")

    historical_start = None
    historical_end = None
    if historical:
        try:
            historical_start = date.fromisoformat(args.historical_start)
            historical_end = date.fromisoformat(args.historical_end)
        except ValueError:
            parser.error("As datas historicas devem usar o formato AAAA-MM-DD")
        if historical_start > historical_end:
            parser.error("A data inicial nao pode ser posterior a data final")

    logging.basicConfig(level=args.log_level.upper(), format="%(asctime)s %(levelname)s %(message)s")
    config = load_config(args.config)
    engine = config["database"]["engine"]
    dsn = config["database"]["dsn"]
    lookback_days = config["query"]["lookback_days"]
    specs = query_specs(config["views"], engine, lookback_days, historical_start, historical_end)
    if historical:
        LOG.info("Consultas limitadas no banco ao periodo historico de %s a %s.", historical_start, historical_end)
    elif lookback_days:
        LOG.info("Consultas incrementais limitadas aos ultimos %s dia(s), preservando registros ativos.", lookback_days)
    else:
        LOG.warning("Filtro incremental desativado: as views serao consultadas integralmente.")

    if not dsn:
        LOG.error("DSN do banco nao informado.")
        return 2
    if not config["sanatio"]["token"]:
        LOG.error("Token SANATIO nao informado.")
        return 2

    try:
        with connect(engine, dsn) as conn:
            rows = {spec.key: fetch_rows(conn, engine, spec) for spec in specs}
    except Exception:
        LOG.exception("Falha ao ler views do MV SOUL.")
        return 1

    if historical:
        rows = filter_historical_rows(rows, historical_start, historical_end)
        if not rows["patients"]:
            LOG.warning("Nenhum atendimento encontrado no periodo historico informado.")
            return 0
        reference_at = datetime.combine(historical_end, time.max, tzinfo=timezone.utc)
        payload = build_payload(rows, config["risk_thresholds"], historical_end)
        batches = split_payload(
            payload,
            args.batch_size,
            f"historica:{historical_start.isoformat()}:{historical_end.isoformat()}",
            reference_at,
        )
    else:
        payload = build_payload(rows, config["risk_thresholds"])
        batches = [payload]

    counts = {key: len(value) for key, value in payload.items() if isinstance(value, list)}
    LOG.info("Payload montado: %s", counts)
    if historical:
        LOG.info("Carga historica preparada em %s lote(s).", len(batches))

    if args.output:
        with open(args.output, "w", encoding="utf-8") as file:
            json.dump(batches[0] if len(batches) == 1 else {"batches": batches}, file, ensure_ascii=False, indent=2)
        LOG.info("Payload salvo em %s", args.output)

    if args.dry_run:
        print(json.dumps(batches[0] if len(batches) == 1 else {"batches": batches}, ensure_ascii=False, indent=2))
        return 0

    results = []
    for index, batch in enumerate(batches, start=1):
        try:
            result = post_payload(config["sanatio"]["ingest_url"], config["sanatio"]["token"], batch)
        except Exception:
            LOG.exception("Falha ao enviar lote %s de %s ao SANATIO.", index, len(batches))
            return 1
        results.append(result)
        LOG.info("Lote %s de %s enviado: %s", index, len(batches), json.dumps(result, ensure_ascii=False))

    response = {
        "modo_carga": "HISTORICA" if historical else "INCREMENTAL",
        "lotes_enviados": len(results),
        "resultados": results,
    }
    print(json.dumps(response, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
