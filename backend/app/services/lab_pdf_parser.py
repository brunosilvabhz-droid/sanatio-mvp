import io
import re
from datetime import datetime

import pdfplumber


OS_PATTERN = re.compile(r"\bOS:\s*750\.(\d+)\b", re.IGNORECASE)
ROW_PATTERN = re.compile(r"^(\d{2}/\d{2}/\d{2}\s+\d{2}:\d{2})\s+(\d{2}/\d{2}/\d{2}\s+\d{2}:\d{2})\s+(.+)$")
RESULT_PATTERN = re.compile(r"\b(?:NEGATIV[OA]\s+AT[EÉ]\s+O\s+MOMENTO|CULTURA\s+FINALIZADA\s*:|POSITIV[OA]\b|NEGATIV[OA]\b)", re.IGNORECASE)


def parse_lab_pdf(content: bytes) -> tuple[int, list[dict]]:
    if not content.startswith(b"%PDF-"):
        raise ValueError("O arquivo não é um PDF válido")
    try:
        document = pdfplumber.open(io.BytesIO(content))
    except Exception as exc:
        raise ValueError("Não foi possível abrir o PDF") from exc
    with document:
        if len(document.pages) > 100:
            raise ValueError("O relatório excede 100 páginas")
        rows: list[dict] = []
        for page_number, page in enumerate(document.pages, start=1):
            text = page.extract_text() or ""
            if not text.strip():
                raise ValueError(f"Página {page_number} sem texto selecionável. PDF digitalizado requer OCR e revisão manual")
            current_os = None
            current_name = None
            for line in text.splitlines():
                line = line.strip()
                os_match = OS_PATTERN.search(line)
                if os_match:
                    current_os = os_match.group(1)
                    current_name = line[os_match.end():].strip()
                    continue
                row_match = ROW_PATTERN.match(line)
                if row_match:
                    if not current_os:
                        raise ValueError(f"Página {page_number}: exame sem OS identificável")
                    details = row_match.group(3)
                    result_match = RESULT_PATTERN.search(details)
                    if not result_match:
                        raise ValueError(f"Página {page_number}: resultado não reconhecido para OS 750.{current_os}")
                    observation = details[result_match.start():].strip().lstrip("* ")
                    if re.search(r"POSITIV[AO]", observation, re.IGNORECASE):
                        status = "POSITIVA"
                    elif "FINALIZADA" in observation.upper() and re.search(r"NEGATIV[AO]", observation, re.IGNORECASE):
                        status = "NEGATIVA"
                    else:
                        status = "PARCIAL"
                    rows.append({
                        "pagina": page_number,
                        "os_pedido": current_os,
                        "nome_relatorio": current_name,
                        "data_coleta": datetime.strptime(row_match.group(1), "%d/%m/%y %H:%M"),
                        "data_resultado": datetime.strptime(row_match.group(2), "%d/%m/%y %H:%M"),
                        "exame_amostra": details[:result_match.start()].strip(),
                        "resultado": observation,
                        "situacao": status,
                    })
                    continue
                if rows and rows[-1]["pagina"] == page_number and current_os == rows[-1]["os_pedido"]:
                    if line and not line.startswith(("LAB", "Dt.Coleta", "HOSPITAL", "OS:")) and "ANDAR SOCOR" not in line and "ATENDIMENTO SOCOR" not in line and line != "CTI SOCOR":
                        rows[-1]["resultado"] += " " + line
        if not rows:
            raise ValueError("Nenhum resultado de cultura com OS 750. foi encontrado")
        return len(document.pages), rows
