from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.clinical import (
    AntimicrobianoAtendimento,
    Atendimento,
    ExecucaoIntegracao,
    MovimentacaoLeito,
    Paciente,
    SolicitacaoExameAtendimento,
)


def clean(value: str | None) -> str:
    return str(value or "").strip()


def parse_date(value: str | None) -> datetime | None:
    value = clean(value)
    return datetime.strptime(value, "%d/%m/%y").replace(tzinfo=timezone.utc) if value else None


def read_csv(path: Path) -> tuple[list[dict[str, str]], str]:
    raw = path.read_bytes()
    with path.open(encoding="utf-8-sig", newline="") as csv_file:
        return list(csv.DictReader(csv_file)), hashlib.sha256(raw).hexdigest()


REQUIRED_COLUMNS = {
    "antimicrobials": {
        "CD_ATENDIMENTO", "CD_PACIENTE", "CD_PRESCRICAO", "CD_ITEM_PRESCRICAO",
        "CD_PRODUTO", "DS_ANTIMICROBIANO", "PRINCIPIO_ATIVO", "DT_INICIO",
        "DT_APLICACAO", "DT_FIM", "SN_ATIVO", "DS_DOSE", "DS_VIA",
        "DS_FREQUENCIA", "DIAS_USO",
    },
    "movements": {
        "CD_ATENDIMENTO", "CD_PACIENTE", "DT_MOVIMENTACAO", "DS_UNIDADE_ORIGEM",
        "DS_LEITO_ORIGEM", "DS_UNIDADE_DESTINO", "DS_LEITO_DESTINO",
    },
    "exam-requests": {"CD_PEDIDO", "CD_ATENDIMENTO", "CD_PACIENTE", "DT_SOLICITACAO"},
}


def validate_columns(kind: str, rows: list[dict[str, str]]) -> None:
    if not rows:
        raise ValueError("O arquivo CSV esta vazio")
    missing = REQUIRED_COLUMNS[kind] - set(rows[0])
    if missing:
        raise ValueError(f"Colunas obrigatorias ausentes: {', '.join(sorted(missing))}")


def ensure_attendances(db, rows: list[dict[str, str]]) -> tuple[dict[str, Atendimento], int, int]:
    references: dict[str, str] = {}
    for row in rows:
        attendance_id = clean(row["CD_ATENDIMENTO"])
        patient_id = clean(row["CD_PACIENTE"])
        if not attendance_id or not patient_id:
            raise ValueError("Paciente ou atendimento vazio")
        if attendance_id in references and references[attendance_id] != patient_id:
            raise ValueError(f"Atendimento {attendance_id} associado a pacientes diferentes")
        references[attendance_id] = patient_id

    patients = {
        item.id_origem_paciente: item
        for item in db.scalars(select(Paciente).where(Paciente.id_origem_paciente.in_(set(references.values()))))
    }
    attendances = {
        item.id_origem_atendimento: item
        for item in db.scalars(select(Atendimento).where(Atendimento.id_origem_atendimento.in_(set(references))))
    }
    new_patients = 0
    new_attendances = 0
    for attendance_id, patient_id in references.items():
        patient = patients.get(patient_id)
        if not patient:
            patient = Paciente(id_origem_paciente=patient_id)
            patients[patient_id] = patient
            db.add(patient)
            db.flush()
            new_patients += 1
        attendance = attendances.get(attendance_id)
        if not attendance:
            attendance = Atendimento(
                paciente_id=patient.id,
                id_origem_atendimento=attendance_id,
                ativo=False,
            )
            attendances[attendance_id] = attendance
            db.add(attendance)
            new_attendances += 1
        elif attendance.paciente_id != patient.id:
            raise ValueError(f"Atendimento {attendance_id} ja associado a outro paciente no SANATIO")
    db.flush()
    return attendances, new_patients, new_attendances


def start_run(db, kind: str, digest: str, patient_count: int) -> ExecucaoIntegracao:
    batch_key = f"csv-{kind}:{digest}"
    if db.scalar(select(ExecucaoIntegracao).where(ExecucaoIntegracao.chave_lote == batch_key)):
        raise RuntimeError("Este arquivo ja foi carregado anteriormente")
    run = ExecucaoIntegracao(
        status="EM_EXECUCAO",
        modo_carga="HISTORICA",
        chave_lote=batch_key,
        data_hora_inicio=datetime.now(timezone.utc),
        total_pacientes_recebidos=patient_count,
    )
    db.add(run)
    db.flush()
    return run


def finish_run(db, run: ExecucaoIntegracao, *, movement_count: int = 0) -> None:
    run.status = "SUCESSO"
    run.total_movimentacoes_recebidas = movement_count
    run.total_snapshots_recebidos = 0
    run.total_alertas_gerados = 0
    run.data_hora_fim = datetime.now(timezone.utc)
    db.commit()


def antimicrobial_rows(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], int, int]:
    grouped: dict[tuple[str, ...], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[(clean(row["CD_ATENDIMENTO"]), clean(row["CD_PRESCRICAO"]), clean(row["CD_ITEM_PRESCRICAO"]), clean(row["DT_APLICACAO"]))].append(row)
    result = []
    exact_duplicates = 0
    merged_principles = 0
    for items in grouped.values():
        unique_rows = {tuple(clean(item.get(field)) for field in items[0]) for item in items}
        exact_duplicates += len(items) - len(unique_rows)
        base = dict(items[0])
        principles = sorted({clean(item["PRINCIPIO_ATIVO"]) for item in items if clean(item["PRINCIPIO_ATIVO"])})
        for field in base:
            if field != "PRINCIPIO_ATIVO" and len({clean(item.get(field)) for item in items}) > 1:
                raise ValueError(f"Conflito nao suportado em {field} para uma mesma aplicacao")
        if len(principles) > 1:
            merged_principles += 1
        base["PRINCIPIO_ATIVO"] = " + ".join(principles)
        result.append(base)
    return result, exact_duplicates, merged_principles


def movement_rows(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], int]:
    fields = list(rows[0]) if rows else []
    unique = {tuple(clean(row.get(field)) for field in fields): row for row in rows}
    return list(unique.values()), len(rows) - len(unique)


def load_antimicrobials(db, source: list[dict[str, str]], digest: str, apply: bool) -> dict:
    rows, exact_duplicates, merged_principles = antimicrobial_rows(source)
    attendance_ids = {clean(row["CD_ATENDIMENTO"]) for row in rows}
    existing_attendances = set(db.scalars(select(Atendimento.id_origem_atendimento).where(Atendimento.id_origem_atendimento.in_(attendance_ids))))
    report = {
        "source_rows": len(source), "records_after_consolidation": len(rows),
        "exact_duplicates_removed": exact_duplicates, "principle_conflicts_merged": merged_principles,
        "unique_attendances": len(attendance_ids), "missing_attendances": len(attendance_ids - existing_attendances),
        "mode": "APPLY" if apply else "DRY_RUN", "file_sha256": digest,
    }
    if not apply:
        return report
    attendances, new_patients, new_attendances = ensure_attendances(db, rows)
    run = start_run(db, "antimicrobianos", digest, len({clean(row["CD_PACIENTE"]) for row in rows}))
    attendance_db_ids = {item.id for item in attendances.values()}
    existing = {
        (item.atendimento_id, item.id_origem_prescricao, item.id_origem_item_prescricao, item.data_hora_aplicacao): item
        for item in db.scalars(select(AntimicrobianoAtendimento).where(AntimicrobianoAtendimento.atendimento_id.in_(attendance_db_ids)))
    }
    created = updated = 0
    for row in rows:
        attendance = attendances[clean(row["CD_ATENDIMENTO"])]
        application = parse_date(row["DT_APLICACAO"])
        key = (attendance.id, clean(row["CD_PRESCRICAO"]), clean(row["CD_ITEM_PRESCRICAO"]), application)
        item = existing.get(key)
        if not item:
            item = AntimicrobianoAtendimento(
                atendimento_id=attendance.id,
                id_origem_prescricao=key[1],
                id_origem_item_prescricao=key[2],
                data_hora_aplicacao=application,
            )
            db.add(item); created += 1
        else:
            updated += 1
        start = parse_date(row["DT_INICIO"])
        end = parse_date(row["DT_FIM"])
        item.id_origem_produto = clean(row["CD_PRODUTO"]) or None
        item.nome_antimicrobiano = clean(row["DS_ANTIMICROBIANO"])
        item.principio_ativo = clean(row["PRINCIPIO_ATIVO"]) or None
        item.data_hora_inicio = start
        item.data_hora_fim = end
        item.ativo = clean(row["SN_ATIVO"]).upper() == "S"
        item.dose = clean(row["DS_DOSE"]) or None
        item.via = clean(row["DS_VIA"]) or None
        item.frequencia = clean(row["DS_FREQUENCIA"]) or None
        item.dias_uso = int(clean(row["DIAS_USO"])) if clean(row["DIAS_USO"]) else max(((end or datetime.now(timezone.utc)).date() - start.date()).days, 0)
    finish_run(db, run)
    report.update(created=created, updated=updated, new_patients=new_patients, new_attendances=new_attendances, integration_run_id=run.id)
    return report


def load_movements(db, source: list[dict[str, str]], digest: str, apply: bool) -> dict:
    fields = list(source[0]) if source else []
    rows, exact_duplicates = movement_rows(source)
    attendance_ids = {clean(row["CD_ATENDIMENTO"]) for row in rows}
    existing_attendances = set(db.scalars(select(Atendimento.id_origem_atendimento).where(Atendimento.id_origem_atendimento.in_(attendance_ids))))
    report = {
        "source_rows": len(source), "records_after_deduplication": len(rows),
        "exact_duplicates_removed": exact_duplicates, "unique_attendances": len(attendance_ids),
        "missing_attendances": len(attendance_ids - existing_attendances), "mode": "APPLY" if apply else "DRY_RUN", "file_sha256": digest,
    }
    if not apply:
        return report
    attendances, new_patients, new_attendances = ensure_attendances(db, rows)
    run = start_run(db, "movimentacoes", digest, len({clean(row["CD_PACIENTE"]) for row in rows}))
    source_keys = {
        hashlib.sha256(json.dumps({field: clean(row.get(field)) for field in fields}, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        for row in rows
    }
    existing = {item.chave_origem: item for item in db.scalars(select(MovimentacaoLeito).where(MovimentacaoLeito.chave_origem.in_(source_keys)))}
    created = updated = 0
    for row in rows:
        source_key = hashlib.sha256(json.dumps({field: clean(row.get(field)) for field in fields}, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        item = existing.get(source_key)
        if not item:
            item = MovimentacaoLeito(chave_origem=source_key, atendimento_id=attendances[clean(row["CD_ATENDIMENTO"])].id)
            db.add(item); created += 1
        else:
            updated += 1
        item.unidade_origem = clean(row["DS_UNIDADE_ORIGEM"]) or None
        item.leito_origem = clean(row["DS_LEITO_ORIGEM"]) or None
        item.unidade_destino = clean(row["DS_UNIDADE_DESTINO"]) or None
        item.leito_destino = clean(row["DS_LEITO_DESTINO"]) or None
        item.data_hora_movimentacao = parse_date(row["DT_MOVIMENTACAO"])
    finish_run(db, run, movement_count=len(rows))
    report.update(created=created, updated=updated, new_patients=new_patients, new_attendances=new_attendances, integration_run_id=run.id)
    return report


def load_exam_requests(db, rows: list[dict[str, str]], digest: str, apply: bool) -> dict:
    order_ids = [clean(row["CD_PEDIDO"]) for row in rows]
    if len(order_ids) != len(set(order_ids)):
        raise ValueError("O arquivo possui pedidos duplicados")
    attendance_ids = {clean(row["CD_ATENDIMENTO"]) for row in rows}
    existing_attendances = set(db.scalars(select(Atendimento.id_origem_atendimento).where(Atendimento.id_origem_atendimento.in_(attendance_ids))))
    report = {
        "source_rows": len(rows), "unique_orders": len(order_ids), "unique_attendances": len(attendance_ids),
        "missing_attendances": len(attendance_ids - existing_attendances), "mode": "APPLY" if apply else "DRY_RUN", "file_sha256": digest,
    }
    if not apply:
        return report
    attendances, new_patients, new_attendances = ensure_attendances(db, rows)
    run = start_run(db, "solicitacoes-exame", digest, len({clean(row["CD_PACIENTE"]) for row in rows}))
    existing = {item.id_origem_pedido: item for item in db.scalars(select(SolicitacaoExameAtendimento).where(SolicitacaoExameAtendimento.id_origem_pedido.in_(order_ids)))}
    created = updated = 0
    for row in rows:
        order_id = clean(row["CD_PEDIDO"])
        attendance = attendances[clean(row["CD_ATENDIMENTO"])]
        item = existing.get(order_id)
        if not item:
            item = SolicitacaoExameAtendimento(atendimento_id=attendance.id, id_origem_pedido=order_id)
            db.add(item); created += 1
        else:
            if item.atendimento_id != attendance.id:
                raise ValueError(f"Pedido {order_id} ja vinculado a outro atendimento")
            updated += 1
        item.data_hora_solicitacao = parse_date(row["DT_SOLICITACAO"])
    finish_run(db, run)
    report.update(created=created, updated=updated, new_patients=new_patients, new_attendances=new_attendances, integration_run_id=run.id)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Carga unica de dados clinicos CSV.")
    parser.add_argument("kind", choices=["antimicrobials", "movements", "exam-requests"])
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    rows, digest = read_csv(args.csv_path)
    validate_columns(args.kind, rows)
    with SessionLocal() as db:
        loaders = {
            "antimicrobials": load_antimicrobials,
            "movements": load_movements,
            "exam-requests": load_exam_requests,
        }
        report = loaders[args.kind](db, rows, digest, args.apply)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
