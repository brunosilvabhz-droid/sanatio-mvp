from __future__ import annotations

import argparse
import json
import os
import sys
from urllib import error, request

import psycopg
from psycopg.rows import dict_row


DEFAULT_DSN = "postgresql://sanatio:sanatio@localhost:5432/sanatio"
DEFAULT_INGEST_URL = "http://localhost:8000/ingest/snapshots"


SNAPSHOT_SQL = """
WITH antimicrobial AS (
    SELECT
        cd_atendimento,
        COALESCE(MAX((CURRENT_DATE - dt_inicio::date)::int), 0) AS max_antimicrobial_days
    FROM soulmv_mock.mv_antimicrobianos
    WHERE sn_ativo = 'S' AND dt_fim IS NULL
    GROUP BY cd_atendimento
),
culture AS (
    SELECT
        cd_atendimento,
        BOOL_OR(sn_positivo = 'S') AS has_positive_culture
    FROM soulmv_mock.mv_culturas
    GROUP BY cd_atendimento
),
invasive AS (
    SELECT
        cd_atendimento,
        COALESCE(MAX((CURRENT_DATE - dt_inicio::date)::int), 0) AS max_invasive_device_days
    FROM soulmv_mock.mv_procedimentos_invasivos
    WHERE sn_ativo = 'S' AND dt_fim IS NULL
    GROUP BY cd_atendimento
),
isolation AS (
    SELECT
        cd_atendimento,
        BOOL_OR(sn_ativo = 'S' AND dt_fim IS NULL) AS has_active_isolation
    FROM soulmv_mock.mv_isolamentos
    GROUP BY cd_atendimento
)
SELECT
    p.cd_atendimento,
    p.cd_paciente,
    p.ds_unidade AS unit,
    p.ds_leito AS bed,
    (p.dt_alta IS NULL) AS active,
    p.dt_atendimento AS admitted_at,
    p.dt_alta AS discharged_at,
    GREATEST((CURRENT_DATE - p.dt_atendimento::date)::int, 0) AS days_in_hospital,
    COALESCE(c.has_positive_culture, false) AS has_positive_culture,
    COALESCE(a.max_antimicrobial_days, 0) AS max_antimicrobial_days,
    COALESCE(i.max_invasive_device_days, 0) AS max_invasive_device_days,
    COALESCE(s.has_active_isolation, false) AS has_active_isolation
FROM soulmv_mock.mv_pacientes_internados p
LEFT JOIN antimicrobial a ON a.cd_atendimento = p.cd_atendimento
LEFT JOIN culture c ON c.cd_atendimento = p.cd_atendimento
LEFT JOIN invasive i ON i.cd_atendimento = p.cd_atendimento
LEFT JOIN isolation s ON s.cd_atendimento = p.cd_atendimento
ORDER BY p.cd_atendimento;
"""

BED_MOVEMENTS_SQL = """
SELECT
    cd_atendimento,
    cd_paciente,
    dt_movimentacao AS moved_at,
    ds_unidade_origem AS from_unit,
    ds_leito_origem AS from_bed,
    ds_unidade_destino AS to_unit,
    ds_leito_destino AS to_bed
FROM soulmv_mock.mv_movimentacoes_leito
ORDER BY cd_atendimento, dt_movimentacao;
"""

ANTIMICROBIALS_SQL = """
SELECT
    cd_atendimento,
    cd_paciente,
    cd_prescricao,
    cd_item_prescricao,
    cd_produto,
    ds_antimicrobiano,
    ds_principio_ativo,
    dt_inicio,
    COALESCE(dt_aplicacao, dt_inicio) AS dt_aplicacao,
    dt_fim,
    sn_ativo,
    ds_frequencia,
    ds_via,
    ds_dose,
    GREATEST((COALESCE(dt_fim::date, CURRENT_DATE) - dt_inicio::date)::int, 0) AS dias_uso
FROM soulmv_mock.mv_antimicrobianos
ORDER BY cd_atendimento, ds_antimicrobiano;
"""

CULTURES_SQL = """
SELECT
    cd_atendimento,
    cd_paciente,
    cd_pedido,
    cd_exame,
    ds_exame,
    dt_coleta,
    dt_resultado,
    ds_material,
    ds_microorganismo,
    ds_resultado,
    sn_positivo
FROM soulmv_mock.mv_culturas
ORDER BY cd_atendimento, dt_coleta;
"""

INVASIVE_PROCEDURES_SQL = """
SELECT
    cd_atendimento,
    cd_paciente,
    cd_procedimento,
    ds_procedimento,
    dt_inicio,
    dt_fim,
    sn_ativo,
    ds_local_instalacao,
    GREATEST((COALESCE(dt_fim::date, CURRENT_DATE) - dt_inicio::date)::int, 0) AS dias_permanencia
FROM soulmv_mock.mv_procedimentos_invasivos
ORDER BY cd_atendimento, dt_inicio;
"""

ISOLATIONS_SQL = """
SELECT
    cd_atendimento,
    cd_paciente,
    cd_isolamento,
    ds_isolamento,
    dt_inicio,
    dt_fim,
    sn_ativo
FROM soulmv_mock.mv_isolamentos
ORDER BY cd_atendimento, dt_inicio;
"""


def risk_status(row: dict) -> str:
    if (
        row["has_positive_culture"]
        or row["max_antimicrobial_days"] >= 7
        or row["max_invasive_device_days"] >= 7
        or row["days_in_hospital"] >= 10
        or row["has_active_isolation"]
    ):
        return "alto"
    if row["max_antimicrobial_days"] >= 4 or row["days_in_hospital"] >= 7:
        return "medio"
    return "baixo"


def load_snapshots(dsn: str) -> list[dict]:
    with psycopg.connect(dsn, row_factory=dict_row) as conn:
        rows = conn.execute(SNAPSHOT_SQL).fetchall()

    snapshots = []
    for row in rows:
        snapshots.append(
            {
                "cd_atendimento": str(row["cd_atendimento"]),
                "cd_paciente": str(row["cd_paciente"]),
                "unit": row["unit"],
                "bed": row["bed"],
                "active": bool(row["active"]),
                "admitted_at": row["admitted_at"].isoformat() if row["admitted_at"] else None,
                "discharged_at": row["discharged_at"].isoformat() if row["discharged_at"] else None,
                "risk_status": risk_status(row),
                "days_in_hospital": int(row["days_in_hospital"] or 0),
                "has_positive_culture": bool(row["has_positive_culture"]),
                "max_antimicrobial_days": int(row["max_antimicrobial_days"] or 0),
                "max_invasive_device_days": int(row["max_invasive_device_days"] or 0),
                "has_active_isolation": bool(row["has_active_isolation"]),
            }
        )
    return snapshots


def load_bed_movements(dsn: str) -> list[dict]:
    with psycopg.connect(dsn, row_factory=dict_row) as conn:
        rows = conn.execute(BED_MOVEMENTS_SQL).fetchall()
    return [
        {
            "cd_atendimento": str(row["cd_atendimento"]),
            "cd_paciente": str(row["cd_paciente"]),
            "moved_at": row["moved_at"].isoformat(),
            "from_unit": row["from_unit"],
            "from_bed": row["from_bed"],
            "to_unit": row["to_unit"],
            "to_bed": row["to_bed"],
        }
        for row in rows
    ]


def load_antimicrobials(dsn: str) -> list[dict]:
    with psycopg.connect(dsn, row_factory=dict_row) as conn:
        rows = conn.execute(ANTIMICROBIALS_SQL).fetchall()
    return [
        {
            "cd_atendimento": str(row["cd_atendimento"]),
            "cd_paciente": str(row["cd_paciente"]),
            "cd_prescricao": str(row["cd_prescricao"]),
            "cd_item_prescricao": str(row["cd_item_prescricao"]),
            "cd_produto": str(row["cd_produto"]) if row["cd_produto"] is not None else None,
            "ds_antimicrobiano": row["ds_antimicrobiano"],
            "ds_principio_ativo": row["ds_principio_ativo"],
            "dt_inicio": row["dt_inicio"].isoformat(),
            "dt_aplicacao": row["dt_aplicacao"].isoformat(),
            "dt_fim": row["dt_fim"].isoformat() if row["dt_fim"] else None,
            "sn_ativo": row["sn_ativo"],
            "ds_frequencia": row["ds_frequencia"],
            "ds_via": row["ds_via"],
            "ds_dose": row["ds_dose"],
            "dias_uso": int(row["dias_uso"] or 0),
        }
        for row in rows
    ]


def load_cultures(dsn: str) -> list[dict]:
    with psycopg.connect(dsn, row_factory=dict_row) as conn:
        rows = conn.execute(CULTURES_SQL).fetchall()
    return [
        {
            "cd_atendimento": str(row["cd_atendimento"]),
            "cd_paciente": str(row["cd_paciente"]),
            "cd_pedido": str(row["cd_pedido"]),
            "cd_exame": str(row["cd_exame"]),
            "ds_exame": row["ds_exame"],
            "dt_coleta": row["dt_coleta"].isoformat(),
            "dt_resultado": row["dt_resultado"].isoformat() if row["dt_resultado"] else None,
            "ds_material": row["ds_material"],
            "ds_microorganismo": row["ds_microorganismo"],
            "ds_resultado": row["ds_resultado"],
            "sn_positivo": row["sn_positivo"],
        }
        for row in rows
    ]


def load_invasive_procedures(dsn: str) -> list[dict]:
    with psycopg.connect(dsn, row_factory=dict_row) as conn:
        rows = conn.execute(INVASIVE_PROCEDURES_SQL).fetchall()
    return [
        {
            "cd_atendimento": str(row["cd_atendimento"]),
            "cd_paciente": str(row["cd_paciente"]),
            "cd_procedimento": str(row["cd_procedimento"]),
            "ds_procedimento": row["ds_procedimento"],
            "dt_inicio": row["dt_inicio"].isoformat(),
            "dt_fim": row["dt_fim"].isoformat() if row["dt_fim"] else None,
            "sn_ativo": row["sn_ativo"],
            "ds_local_instalacao": row["ds_local_instalacao"],
            "dias_permanencia": int(row["dias_permanencia"] or 0),
        }
        for row in rows
    ]


def load_isolations(dsn: str) -> list[dict]:
    with psycopg.connect(dsn, row_factory=dict_row) as conn:
        rows = conn.execute(ISOLATIONS_SQL).fetchall()
    return [
        {
            "cd_atendimento": str(row["cd_atendimento"]),
            "cd_paciente": str(row["cd_paciente"]),
            "cd_isolamento": str(row["cd_isolamento"]),
            "ds_isolamento": row["ds_isolamento"],
            "dt_inicio": row["dt_inicio"].isoformat(),
            "dt_fim": row["dt_fim"].isoformat() if row["dt_fim"] else None,
            "sn_ativo": row["sn_ativo"],
        }
        for row in rows
    ]


def post_snapshots(ingest_url: str, token: str, payload_body: dict) -> dict:
    payload = json.dumps(payload_body).encode("utf-8")
    req = request.Request(
        ingest_url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "X-Sanatio-Token": token,
        },
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"SANATIO retornou HTTP {exc.code}: {body}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Nao foi possivel conectar ao SANATIO: {exc}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description="Envia snapshots mock do MV Soul para o SANATIO.")
    parser.add_argument("--dry-run", action="store_true", help="Apenas imprime o payload, sem enviar.")
    parser.add_argument("--dsn", default=os.getenv("SOULMV_PG_DSN", DEFAULT_DSN), help="DSN PostgreSQL da fonte mock.")
    parser.add_argument("--url", default=os.getenv("SANATIO_INGEST_URL", DEFAULT_INGEST_URL), help="URL de ingestao do SANATIO.")
    parser.add_argument("--token", default=os.getenv("SANATIO_TOKEN"), help="Token hospitalar do SANATIO.")
    args = parser.parse_args()

    payload_body = {
        "patients": load_snapshots(args.dsn),
        "bed_movements": load_bed_movements(args.dsn),
        "antimicrobials": load_antimicrobials(args.dsn),
        "cultures": load_cultures(args.dsn),
        "invasive_procedures": load_invasive_procedures(args.dsn),
        "isolations": load_isolations(args.dsn),
    }
    print(json.dumps(payload_body, ensure_ascii=False, indent=2))

    if args.dry_run:
        print(
            "\nDRY RUN: "
            f"{len(payload_body['patients'])} snapshots, "
            f"{len(payload_body['bed_movements'])} movimentacoes, "
            f"{len(payload_body['antimicrobials'])} antimicrobianos, "
            f"{len(payload_body['cultures'])} culturas, "
            f"{len(payload_body['invasive_procedures'])} procedimentos invasivos e "
            f"{len(payload_body['isolations'])} isolamentos montados. Nenhum dado enviado."
        )
        return 0

    if not args.token:
        print("Erro: informe SANATIO_TOKEN ou use --token.", file=sys.stderr)
        return 2

    result = post_snapshots(args.url, args.token, payload_body)
    print("\nResposta SANATIO:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
