from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.clinical import Atendimento, ExecucaoIntegracao, Paciente, SnapshotAtendimento

REQUIRED_COLUMNS = {
    "CD_ATENDIMENTO",
    "CD_PACIENTE",
    "DT_NASCIMENTO",
    "TP_SEXO",
    "DT_ATENDIMENTO",
    "DT_ALTA",
    "CD_UNIDADE",
    "DS_UNIDADE",
    "CD_LEITO",
    "DS_LEITO",
    "CD_PRESTADOR",
    "NM_PRESTADOR",
    "CD_CONVENIO",
    "NM_CONVENIO",
}


def parse_date(value: str, *, birth_date: bool = False) -> datetime | None:
    value = value.strip()
    if not value:
        return None
    parsed = datetime.strptime(value, "%d/%m/%y").replace(tzinfo=timezone.utc)
    if birth_date and parsed.date() > date.today():
        parsed = parsed.replace(year=parsed.year - 100)
    return parsed


def read_rows(path: Path) -> tuple[list[dict], str]:
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    with path.open(encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        missing = REQUIRED_COLUMNS.difference(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Colunas obrigatorias ausentes: {', '.join(sorted(missing))}")
        rows = []
        attendances: set[str] = set()
        for line_number, source in enumerate(reader, start=2):
            attendance_id = source["CD_ATENDIMENTO"].strip()
            patient_id = source["CD_PACIENTE"].strip()
            if not attendance_id or not patient_id:
                raise ValueError(f"Linha {line_number}: paciente ou atendimento vazio")
            if attendance_id in attendances:
                raise ValueError(f"Linha {line_number}: atendimento duplicado no arquivo")
            attendances.add(attendance_id)
            admitted_at = parse_date(source["DT_ATENDIMENTO"])
            if not admitted_at:
                raise ValueError(f"Linha {line_number}: data de atendimento vazia")
            rows.append(
                {
                    "patient_id": patient_id,
                    "attendance_id": attendance_id,
                    "birth_date": parse_date(source["DT_NASCIMENTO"], birth_date=True).date(),
                    "sex": source["TP_SEXO"].strip() or None,
                    "admitted_at": admitted_at,
                    "discharged_at": parse_date(source["DT_ALTA"]),
                    "unit_code": source["CD_UNIDADE"].strip() or None,
                    "unit": source["DS_UNIDADE"].strip() or None,
                    "bed_code": source["CD_LEITO"].strip() or None,
                    "bed": source["DS_LEITO"].strip() or None,
                    "provider_code": source["CD_PRESTADOR"].strip() or None,
                    "provider": source["NM_PRESTADOR"].strip() or None,
                    "insurance_code": source["CD_CONVENIO"].strip() or None,
                    "insurance": source["NM_CONVENIO"].strip() or None,
                }
            )
    return rows, digest


def load(path: Path, *, apply: bool) -> dict:
    rows, digest = read_rows(path)
    batch_key = f"csv-pacientes:{digest}"
    patient_ids = {row["patient_id"] for row in rows}
    attendance_ids = {row["attendance_id"] for row in rows}

    with SessionLocal() as db:
        if db.scalar(select(ExecucaoIntegracao).where(ExecucaoIntegracao.chave_lote == batch_key)):
            raise RuntimeError("Este arquivo ja foi carregado anteriormente")
        patients = {
            item.id_origem_paciente: item
            for item in db.scalars(select(Paciente).where(Paciente.id_origem_paciente.in_(patient_ids)))
        }
        attendances = {
            item.id_origem_atendimento: item
            for item in db.scalars(select(Atendimento).where(Atendimento.id_origem_atendimento.in_(attendance_ids)))
        }
        report = {
            "file_sha256": digest,
            "rows": len(rows),
            "unique_patients": len(patient_ids),
            "new_patients": len(patient_ids.difference(patients)),
            "existing_patients": len(patient_ids.intersection(patients)),
            "new_attendances": len(attendance_ids.difference(attendances)),
            "updated_attendances": len(attendance_ids.intersection(attendances)),
            "active_attendances": sum(row["discharged_at"] is None for row in rows),
            "mode": "APPLY" if apply else "DRY_RUN",
        }
        if not apply:
            return report

        started_at = datetime.now(timezone.utc)
        integration_run = ExecucaoIntegracao(
            hospital_integracao_id=None,
            status="EM_EXECUCAO",
            modo_carga="HISTORICA",
            chave_lote=batch_key,
            data_referencia=max(row["admitted_at"] for row in rows),
            data_hora_inicio=started_at,
        )
        db.add(integration_run)
        db.flush()

        for row in rows:
            patient = patients.get(row["patient_id"])
            if not patient:
                patient = Paciente(id_origem_paciente=row["patient_id"])
                patients[row["patient_id"]] = patient
                db.add(patient)
            patient.data_nascimento = row["birth_date"]
            patient.sexo = row["sex"]
        db.flush()

        for row in rows:
            attendance = attendances.get(row["attendance_id"])
            if not attendance:
                attendance = Atendimento(id_origem_atendimento=row["attendance_id"], paciente_id=patients[row["patient_id"]].id)
                attendances[row["attendance_id"]] = attendance
                db.add(attendance)
            attendance.paciente_id = patients[row["patient_id"]].id
            attendance.ativo = row["discharged_at"] is None
            attendance.codigo_unidade = row["unit_code"]
            attendance.unidade_atual = row["unit"]
            attendance.codigo_leito = row["bed_code"]
            attendance.leito_atual = row["bed"]
            attendance.codigo_prestador = row["provider_code"]
            attendance.nome_prestador = row["provider"]
            attendance.codigo_convenio = row["insurance_code"]
            attendance.nome_convenio = row["insurance"]
            attendance.data_hora_entrada = row["admitted_at"]
            attendance.data_hora_saida = row["discharged_at"]
        db.flush()

        attendance_database_ids = {item.id for item in attendances.values()}
        existing_snapshots = {
            (item.atendimento_id, item.data_hora_coleta.replace(tzinfo=timezone.utc) if item.data_hora_coleta.tzinfo is None else item.data_hora_coleta): item
            for item in db.scalars(
                select(SnapshotAtendimento).where(SnapshotAtendimento.atendimento_id.in_(attendance_database_ids))
            )
        }
        snapshots_created = 0
        for row in rows:
            attendance = attendances[row["attendance_id"]]
            collected_at = row["discharged_at"] or started_at
            stay_end = row["discharged_at"] or started_at
            snapshot = existing_snapshots.get((attendance.id, collected_at))
            if not snapshot:
                snapshot = SnapshotAtendimento(
                    atendimento_id=attendance.id,
                    data_hora_coleta=collected_at,
                )
                db.add(snapshot)
                snapshots_created += 1
            snapshot.execucao_integracao_id = integration_run.id
            snapshot.status_risco = "baixo"
            snapshot.dias_internacao = max((stay_end.date() - row["admitted_at"].date()).days, 0)
            snapshot.possui_cultura_positiva = False
            snapshot.maior_dias_antimicrobiano = 0
            snapshot.maior_dias_dispositivo_invasivo = 0
            snapshot.possui_isolamento_ativo = False

        finished_at = datetime.now(timezone.utc)
        integration_run.status = "SUCESSO"
        integration_run.total_pacientes_recebidos = len(patient_ids)
        integration_run.total_snapshots_recebidos = len(rows)
        integration_run.total_movimentacoes_recebidas = 0
        integration_run.total_alertas_gerados = 0
        integration_run.data_hora_fim = finished_at
        db.commit()
        report["integration_run_id"] = integration_run.id
        report["snapshots_created"] = snapshots_created
        report["snapshots_updated"] = len(rows) - snapshots_created
        return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Carga unica de pacientes e atendimentos a partir de CSV.")
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--apply", action="store_true", help="Confirma a gravacao; sem esta opcao executa apenas simulacao.")
    args = parser.parse_args()
    print(json.dumps(load(args.csv_path, apply=args.apply), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
