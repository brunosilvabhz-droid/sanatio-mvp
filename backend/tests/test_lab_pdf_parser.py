import unittest
from unittest.mock import patch

from app.services.lab_pdf_parser import parse_lab_pdf


class FakePage:
    def __init__(self, text):
        self.text = text

    def extract_text(self):
        return self.text


class FakePdf:
    def __init__(self, pages):
        self.pages = [FakePage(text) for text in pages]

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return None


class LabPdfParserTest(unittest.TestCase):
    def test_os_suffix_partial_final_and_multiline_positive(self):
        page = """LABORATÓRIO SÃO PAULO
HOSPITAL SOCOR (SOC)
OS: 750.271993 PACIENTE TESTE
03/09/26 03:54 07/09/26 07:41 HEMOCULTURA Sangue Negativo até o momento
03/09/26 03:54 07/09/26 08:37 HEMOCULTURA Sangue CULTURA FINALIZADA: Negativa
OS: 750.272157 OUTRO PACIENTE
04/09/26 06:24 07/09/26 11:57 HEMOCULTURA Sangue Cultura positiva, identificado Pseudomonas
confirmado por teste adicional.
PRONTO ATENDIMENTO SOCOR"""
        with patch("app.services.lab_pdf_parser.pdfplumber.open", return_value=FakePdf([page])):
            pages, rows = parse_lab_pdf(b"%PDF-synthetic")
        self.assertEqual(pages, 1)
        self.assertEqual([row["os_pedido"] for row in rows], ["271993", "271993", "272157"])
        self.assertEqual([row["situacao"] for row in rows], ["PARCIAL", "NEGATIVA", "POSITIVA"])
        self.assertTrue(rows[-1]["resultado"].endswith("teste adicional."))

    def test_rejects_image_only_pdf(self):
        with patch("app.services.lab_pdf_parser.pdfplumber.open", return_value=FakePdf([""])):
            with self.assertRaisesRegex(ValueError, "OCR"):
                parse_lab_pdf(b"%PDF-synthetic")


if __name__ == "__main__":
    unittest.main()
