from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.clinical import AntimicrobianoAtendimento, Atendimento, Paciente
from app.services.antimicrobial_audit_service import sync_for_patient


def main() -> None:
    with SessionLocal() as db:
        rows = db.execute(
            select(AntimicrobianoAtendimento, Atendimento, Paciente)
            .join(Atendimento, Atendimento.id == AntimicrobianoAtendimento.atendimento_id)
            .join(Paciente, Paciente.id == Atendimento.paciente_id)
            .order_by(AntimicrobianoAtendimento.data_hora_aplicacao, AntimicrobianoAtendimento.id)
        ).all()
        grouped: dict[int, tuple[Atendimento, Paciente, list[dict]]] = {}
        for item, attendance, patient in rows:
            bucket = grouped.setdefault(attendance.id, (attendance, patient, []))
            operationally_active = bool(item.ativo and attendance.ativo and item.data_hora_fim is None)
            bucket[2].append(
                {
                    "cd_prescricao": item.id_origem_prescricao,
                    "cd_item_prescricao": item.id_origem_item_prescricao,
                    "cd_produto": item.id_origem_produto,
                    "ds_antimicrobiano": item.nome_antimicrobiano,
                    "dt_inicio": item.data_hora_inicio,
                    "dt_fim": item.data_hora_fim,
                    "dias_uso": item.dias_uso,
                    "sn_ativo": "S" if operationally_active else "N",
                    "ds_dose": item.dose,
                    "ds_via": item.via,
                    "ds_frequencia": item.frequencia,
                }
            )

        created = 0
        for attendance, patient, antimicrobials in grouped.values():
            created += sync_for_patient(
                db,
                {
                    "cd_atendimento": attendance.id_origem_atendimento,
                    "cd_paciente": patient.id_origem_paciente,
                    "ds_unidade": attendance.unidade_atual,
                },
                antimicrobials,
            )
        db.commit()
        print({"attendances": len(grouped), "source_rows": len(rows), "audits_created": created})


if __name__ == "__main__":
    main()
