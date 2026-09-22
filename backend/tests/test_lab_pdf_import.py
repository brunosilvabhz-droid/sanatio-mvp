import asyncio
import io
import unittest
from datetime import datetime
from unittest.mock import patch

from fastapi import HTTPException, UploadFile
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

import app.models  # noqa: F401
from app.api.routes.lab_pdf import LinkRequest, confirm_suggestions, import_pdf, link_result, patient_results
from app.models.base import Base
from app.models.clinical import Atendimento, CulturaAtendimento, Paciente
from app.models.lab_pdf_import import ResultadoPdfLaboratorio
from app.models.user import Role, User


class LabPdfImportTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        role = Role(name="SCIH")
        self.user = User(email="test@example.org", full_name="Test", hashed_password="x", role=role, can_view_patient_name=True)
        patient = Paciente(id_origem_paciente="100")
        self.attendance = Atendimento(paciente=patient, id_origem_atendimento="200", ativo=True)
        self.db.add_all([self.user, self.attendance])
        self.db.flush()
        self.db.add(CulturaAtendimento(
            atendimento_id=self.attendance.id, id_origem_pedido="271993", id_origem_exame="1",
            exame="Hemocultura", data_hora_coleta=datetime(2026, 9, 3, 3, 54),
        ))
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_import_suggest_confirm_and_show_on_patient(self):
        parsed = [{
            "pagina": 1, "os_pedido": "271993", "nome_relatorio": "PACIENTE TESTE",
            "data_coleta": datetime(2026, 9, 3, 3, 54),
            "data_resultado": datetime(2026, 9, 7, 7, 41),
            "exame_amostra": "Hemocultura", "resultado": "Negativo até o momento", "situacao": "PARCIAL",
        }]
        file = UploadFile(filename="relatorio.pdf", file=io.BytesIO(b"%PDF-test"))
        with patch("app.api.routes.lab_pdf.parse_lab_pdf", return_value=(1, parsed)):
            batch = asyncio.run(import_pdf(file=file, db=self.db, user=self.user))
        self.assertEqual(batch["sugestoes"], 1)
        self.assertEqual(patient_results("200", self.db, self.user), [])
        result = confirm_suggestions(batch["id"], self.db, self.user)
        self.assertEqual(result["vinculados"], 1)
        self.assertEqual(patient_results("200", self.db, self.user)[0]["os_pedido"], "271993")

    def test_unmatched_os_needs_explicit_manual_confirmation(self):
        row = ResultadoPdfLaboratorio(
            importacao_id=1, ordem=1, pagina=1, os_pedido="999999",
            data_coleta=datetime(2026, 9, 3), data_resultado=datetime(2026, 9, 7),
            exame_amostra="Cultura", resultado="Negativo até o momento", situacao="PARCIAL",
        )
        from app.models.lab_pdf_import import ImportacaoPdfLaboratorio
        batch = ImportacaoPdfLaboratorio(nome_arquivo="x.pdf", sha256="a" * 64, paginas=1, total_resultados=1, usuario_id=self.user.id)
        self.db.add(batch)
        self.db.flush()
        row.importacao_id = batch.id
        self.db.add(row)
        self.db.commit()
        with self.assertRaises(HTTPException) as error:
            link_result(row.id, LinkRequest(cd_atendimento="200"), self.db, self.user)
        self.assertEqual(error.exception.status_code, 422)
        linked = link_result(row.id, LinkRequest(cd_atendimento="200", confirmar_sem_os=True), self.db, self.user)
        self.assertEqual(linked["cd_atendimento"], "200")


if __name__ == "__main__":
    unittest.main()
