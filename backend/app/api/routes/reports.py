from datetime import date, datetime, time, timezone
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.alert import Alert
from app.models.clinical import AntimicrobianoAtendimento, Atendimento, IsolamentoAtendimento, Paciente
from app.models.user import User

router = APIRouter(prefix="/reports", tags=["Relatórios"], dependencies=[Depends(get_current_user)])

REPORT_LABELS = {
    "patients": "Pacientes",
    "antimicrobials": "Antimicrobianos",
    "isolations": "Isolamentos",
    "alerts": "Alertas",
}


def _export_value(value: object) -> object:
    return value.isoformat() if isinstance(value, (date, datetime)) else value


def _period(start: date | None, end: date | None) -> tuple[datetime | None, datetime | None]:
    start_at = datetime.combine(start, time.min, tzinfo=timezone.utc) if start else None
    end_at = datetime.combine(end, time.max, tzinfo=timezone.utc) if end else None
    return start_at, end_at


def _rows(db: Session, report_type: str, start: date | None, end: date | None, unit: str | None, status: str | None) -> list[dict]:
    start_at, end_at = _period(start, end)
    if report_type == "patients":
        stmt = select(Atendimento, Paciente).join(Paciente, Paciente.id == Atendimento.paciente_id)
        if start_at: stmt = stmt.where(Atendimento.data_hora_entrada >= start_at)
        if end_at: stmt = stmt.where(Atendimento.data_hora_entrada <= end_at)
        if unit: stmt = stmt.where(Atendimento.unidade_atual.ilike(f"%{unit}%"))
        if status == "ATIVO": stmt = stmt.where(Atendimento.ativo.is_(True))
        if status == "ENCERRADO": stmt = stmt.where(Atendimento.ativo.is_(False))
        return [{"Atendimento": a.id_origem_atendimento, "Paciente": p.id_origem_paciente, "Unidade": a.unidade_atual, "Leito": a.leito_atual, "Entrada": a.data_hora_entrada, "Alta": a.data_hora_saida, "Status": "ATIVO" if a.ativo else "ENCERRADO"} for a, p in db.execute(stmt.limit(5000)).all()]
    if report_type == "antimicrobials":
        stmt = select(AntimicrobianoAtendimento, Atendimento, Paciente).join(Atendimento, Atendimento.id == AntimicrobianoAtendimento.atendimento_id).join(Paciente, Paciente.id == Atendimento.paciente_id)
        if start_at: stmt = stmt.where(AntimicrobianoAtendimento.data_hora_inicio >= start_at)
        if end_at: stmt = stmt.where(AntimicrobianoAtendimento.data_hora_inicio <= end_at)
        if unit: stmt = stmt.where(Atendimento.unidade_atual.ilike(f"%{unit}%"))
        if status == "ATIVO": stmt = stmt.where(AntimicrobianoAtendimento.ativo.is_(True))
        if status == "ENCERRADO": stmt = stmt.where(AntimicrobianoAtendimento.ativo.is_(False))
        return [{"Atendimento": a.id_origem_atendimento, "Paciente": p.id_origem_paciente, "Unidade": a.unidade_atual, "Antimicrobiano": m.nome_antimicrobiano, "Princípio ativo": m.principio_ativo, "Início": m.data_hora_inicio, "Fim": m.data_hora_fim, "Status": "ATIVO" if m.ativo else "ENCERRADO"} for m, a, p in db.execute(stmt.limit(5000)).all()]
    if report_type == "isolations":
        stmt = select(IsolamentoAtendimento, Atendimento, Paciente).join(Atendimento, Atendimento.id == IsolamentoAtendimento.atendimento_id).join(Paciente, Paciente.id == Atendimento.paciente_id)
        if start_at: stmt = stmt.where(IsolamentoAtendimento.data_hora_inicio >= start_at)
        if end_at: stmt = stmt.where(IsolamentoAtendimento.data_hora_inicio <= end_at)
        if unit: stmt = stmt.where(Atendimento.unidade_atual.ilike(f"%{unit}%"))
        if status == "ATIVO": stmt = stmt.where(IsolamentoAtendimento.ativo.is_(True))
        if status == "ENCERRADO": stmt = stmt.where(IsolamentoAtendimento.ativo.is_(False))
        return [{"Atendimento": a.id_origem_atendimento, "Paciente": p.id_origem_paciente, "Unidade": a.unidade_atual, "Isolamento": i.isolamento, "Início": i.data_hora_inicio, "Fim": i.data_hora_fim, "Status": "ATIVO" if i.ativo else "ENCERRADO"} for i, a, p in db.execute(stmt.limit(5000)).all()]
    if report_type == "alerts":
        stmt = select(Alert)
        if start_at: stmt = stmt.where(Alert.created_at >= start_at)
        if end_at: stmt = stmt.where(Alert.created_at <= end_at)
        if unit: stmt = stmt.where(Alert.unit.ilike(f"%{unit}%"))
        if status: stmt = stmt.where(Alert.status == status)
        return [{"Atendimento": a.cd_atendimento, "Paciente": a.cd_paciente, "Unidade": a.unit, "Alerta": a.title, "Severidade": a.severity, "Status": a.status, "Criado em": a.created_at} for a in db.scalars(stmt.limit(5000))]
    raise HTTPException(status_code=422, detail="Tipo de relatório inválido")


@router.get("/clinical")
def clinical_report(report_type: str, start: date | None = None, end: date | None = None, unit: str | None = None, status: str | None = None, db: Session = Depends(get_db)) -> dict:
    rows = _rows(db, report_type, start, end, unit, status)
    return {"title": REPORT_LABELS.get(report_type, report_type), "total": len(rows), "rows": rows}


@router.get("/clinical.xlsx")
def clinical_report_xlsx(report_type: str, start: date | None = None, end: date | None = None, unit: str | None = None, status: str | None = None, db: Session = Depends(get_db)) -> StreamingResponse:
    rows = _rows(db, report_type, start, end, unit, status)
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = REPORT_LABELS.get(report_type, "Relatório")[:31]
    headers = list(rows[0]) if rows else ["Sem dados"]
    sheet.append(headers)
    for row in rows:
        sheet.append([_export_value(row.get(header)) for header in headers])
    for cell in sheet[1]: cell.font = cell.font.copy(bold=True)
    output = BytesIO()
    workbook.save(output)
    output.seek(0)
    return StreamingResponse(output, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": f'attachment; filename="sanatio-{report_type}.xlsx"'})


def _pdf_bytes(title: str, rows: list[dict]) -> bytes:
    lines = [f"SANATIO - {title}", f"Total: {len(rows)}", ""]
    for row in rows:
        lines.append(" | ".join(f"{key}: {value or '-'}" for key, value in row.items()))
    chunks = [lines[index:index + 65] for index in range(0, len(lines), 65)] or [[f"SANATIO - {title}", "Sem dados"]]
    font_id = 3 + len(chunks) * 2
    page_ids = [3 + index * 2 for index in range(len(chunks))]
    objects = [b"<< /Type /Catalog /Pages 2 0 R >>", f"<< /Type /Pages /Kids [{' '.join(f'{page_id} 0 R' for page_id in page_ids)}] /Count {len(chunks)} >>".encode()]
    for index, chunk in enumerate(chunks):
        page_id = page_ids[index]
        content_id = page_id + 1
        commands = ["BT /F1 8 Tf 36 806 Td"]
        for line_index, line in enumerate(chunk):
            escaped = str(line)[:150].replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            if line_index:
                commands.append("0 -11 Td")
            commands.append(f"({escaped}) Tj")
        commands.append("ET")
        stream = "\n".join(commands).encode("latin-1", errors="replace")
        objects.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 {font_id} 0 R >> >> /Contents {content_id} 0 R >>".encode())
        objects.append(b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream")
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    result = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, 1):
        offsets.append(len(result)); result.extend(f"{index} 0 obj\n".encode()); result.extend(obj); result.extend(b"\nendobj\n")
    xref = len(result); result.extend(f"xref\n0 {len(objects)+1}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]: result.extend(f"{offset:010d} 00000 n \n".encode())
    result.extend(f"trailer << /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode())
    return bytes(result)


@router.get("/clinical.pdf")
def clinical_report_pdf(report_type: str, start: date | None = None, end: date | None = None, unit: str | None = None, status: str | None = None, db: Session = Depends(get_db)) -> StreamingResponse:
    rows = _rows(db, report_type, start, end, unit, status)
    return StreamingResponse(BytesIO(_pdf_bytes(REPORT_LABELS.get(report_type, report_type), rows)), media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="sanatio-{report_type}.pdf"'})
