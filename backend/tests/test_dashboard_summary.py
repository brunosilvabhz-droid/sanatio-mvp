from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import app.models  # noqa: F401
from app.api.routes.dashboard import _positive_culture_attendances
from app.models.base import Base
from app.models.clinical import Atendimento, CulturaAtendimento, Paciente, SnapshotAtendimento
from app.models.lab_pdf_import import ImportacaoPdfLaboratorio, ResultadoPdfLaboratorio
from app.models.user import Role, User


def test_positive_cultures_include_only_validated_results_for_active_attendances() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = Session(engine)
    role = Role(name="SCIH")
    user = User(email="dashboard@example.org", full_name="Dashboard", hashed_password="x", role=role)
    patient = Paciente(id_origem_paciente="P1")
    active = Atendimento(paciente=patient, id_origem_atendimento="A1", ativo=True)
    inactive = Atendimento(paciente=patient, id_origem_atendimento="A2", ativo=False)
    db.add_all([user, active, inactive])
    db.flush()

    validated = ImportacaoPdfLaboratorio(
        nome_arquivo="validada.pdf", sha256="a" * 64, paginas=1,
        total_resultados=3, usuario_id=user.id, status="VALIDADA",
    )
    pending = ImportacaoPdfLaboratorio(
        nome_arquivo="pendente.pdf", sha256="b" * 64, paginas=1,
        total_resultados=1, usuario_id=user.id, status="PENDENTE",
    )
    db.add_all([validated, pending])
    db.flush()

    def result(batch_id: int, order: int, attendance_id: int) -> ResultadoPdfLaboratorio:
        return ResultadoPdfLaboratorio(
            importacao_id=batch_id, ordem=order, pagina=1, os_pedido=str(order),
            data_coleta=datetime(2026, 10, 1), data_resultado=datetime(2026, 10, 2),
            exame_amostra="Hemocultura", resultado="Positiva", situacao="POSITIVA",
            atendimento_id=attendance_id,
        )

    db.add_all([
        result(validated.id, 1, active.id),
        result(validated.id, 2, active.id),
        result(validated.id, 3, inactive.id),
        result(pending.id, 1, active.id),
        CulturaAtendimento(
            atendimento_id=active.id, id_origem_pedido="1", id_origem_exame="1",
            exame="Hemocultura", data_hora_coleta=datetime(2026, 10, 1), positivo=True,
        ),
    ])
    db.commit()

    snapshot = SnapshotAtendimento(
        atendimento_id=active.id, status_risco="baixo", possui_cultura_positiva=True,
    )
    assert _positive_culture_attendances(db, [snapshot]) == 1

    db.close()
    engine.dispose()
