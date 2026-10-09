from datetime import date, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import app.models  # noqa: F401
from app.api.routes.reports import _rows
from app.models.base import Base
from app.models.clinical import (
    AntimicrobianoAtendimento,
    Atendimento,
    CulturaAtendimento,
    Paciente,
    ProcedimentoInvasivoAtendimento,
)
from app.models.lab_pdf_import import ImportacaoPdfLaboratorio, ResultadoPdfLaboratorio
from app.models.user import Role, User


def test_positive_culture_report_combines_sources_and_clinical_history() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = Session(engine)
    role = Role(name="SCIH")
    user = User(email="report@example.org", full_name="Report", hashed_password="x", role=role)
    patient = Paciente(id_origem_paciente="P1")
    attendance = Atendimento(
        paciente=patient, id_origem_atendimento="A1", ativo=True,
        unidade_atual="CTI", leito_atual="BOX 1",
    )
    db.add_all([user, attendance])
    db.flush()
    batch = ImportacaoPdfLaboratorio(
        nome_arquivo="culturas.pdf", sha256="c" * 64, paginas=1,
        total_resultados=2, usuario_id=user.id, status="VALIDADA",
    )
    db.add(batch)
    db.flush()
    db.add_all([
        CulturaAtendimento(
            atendimento_id=attendance.id, id_origem_pedido="1", id_origem_exame="1",
            exame="Hemocultura", microorganismo="Escherichia coli", resultado="Positiva",
            positivo=True, data_hora_coleta=datetime(2026, 10, 3, 10),
        ),
        ResultadoPdfLaboratorio(
            importacao_id=batch.id, ordem=1, pagina=1, os_pedido="2",
            data_coleta=datetime(2026, 10, 4, 10), data_resultado=datetime(2026, 10, 4, 12),
            exame_amostra="Urocultura Cultura", resultado="Positiva, identificando BGN",
            situacao="POSITIVA", atendimento_id=attendance.id,
        ),
        ResultadoPdfLaboratorio(
            importacao_id=batch.id, ordem=2, pagina=1, os_pedido="2",
            data_coleta=datetime(2026, 10, 4, 10), data_resultado=datetime(2026, 10, 5, 12),
            exame_amostra="Urocultura", resultado="Positiva, identificado E. coli",
            situacao="POSITIVA", atendimento_id=attendance.id,
        ),
        AntimicrobianoAtendimento(
            atendimento_id=attendance.id, id_origem_prescricao="10", id_origem_item_prescricao="1",
            nome_antimicrobiano="Ceftriaxona", data_hora_inicio=datetime(2026, 10, 4), ativo=True,
        ),
        ProcedimentoInvasivoAtendimento(
            atendimento_id=attendance.id, id_origem_procedimento="20", procedimento="CVC",
            data_hora_inicio=datetime(2026, 10, 2), ativo=True,
        ),
    ])
    db.commit()

    rows = _rows(db, "positive_cultures", date(2026, 10, 1), date(2026, 10, 31), "CTI", "ATIVO")

    assert len(rows) == 2
    assert rows[0]["Resultado"] == "Positiva, identificado E. coli"
    assert rows[0]["Antimicrobiano"] == "Sim: Ceftriaxona"
    assert rows[0]["Procedimento invasivo"] == "Sim: CVC"
    assert {row["Fonte"] for row in rows} == {"Integração hospitalar", "PDF validado"}

    db.close()
    engine.dispose()
