from datetime import date, datetime, time, timezone
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import LongTable, Paragraph, SimpleDocTemplate, Spacer, TableStyle
from sqlalchemy import select
from sqlalchemy.orm import Session
from xml.sax.saxutils import escape

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.alert import Alert
from app.models.clinical import (
    AntimicrobianoAtendimento,
    Atendimento,
    CulturaAtendimento,
    IsolamentoAtendimento,
    Paciente,
    ProcedimentoInvasivoAtendimento,
)
from app.models.lab_pdf_import import ImportacaoPdfLaboratorio, ResultadoPdfLaboratorio
from app.models.user import User

router = APIRouter(prefix="/reports", tags=["Relatórios"], dependencies=[Depends(get_current_user)])

REPORT_LABELS = {
    "patients": "Pacientes",
    "antimicrobials": "Antimicrobianos",
    "isolations": "Isolamentos",
    "alerts": "Alertas",
    "positive_cultures": "Culturas positivas",
}


def _export_value(value: object) -> object:
    return value.isoformat() if isinstance(value, (date, datetime)) else value


def _display_value(value: object) -> str:
    if value is None or value == "":
        return "-"
    if isinstance(value, datetime):
        return value.astimezone().strftime("%d/%m/%Y %H:%M") if value.tzinfo else value.strftime("%d/%m/%Y %H:%M")
    if isinstance(value, date):
        return value.strftime("%d/%m/%Y")
    return str(value)


def _period(start: date | None, end: date | None) -> tuple[datetime | None, datetime | None]:
    start_at = datetime.combine(start, time.min, tzinfo=timezone.utc) if start else None
    end_at = datetime.combine(end, time.max, tzinfo=timezone.utc) if end else None
    return start_at, end_at


def _positive_culture_rows(
    db: Session,
    start_at: datetime | None,
    end_at: datetime | None,
    unit: str | None,
    status: str | None,
) -> list[dict]:
    clinical_stmt = (
        select(CulturaAtendimento, Atendimento, Paciente)
        .join(Atendimento, Atendimento.id == CulturaAtendimento.atendimento_id)
        .join(Paciente, Paciente.id == Atendimento.paciente_id)
        .where(CulturaAtendimento.positivo.is_(True))
    )
    pdf_stmt = (
        select(ResultadoPdfLaboratorio, Atendimento, Paciente)
        .join(Atendimento, Atendimento.id == ResultadoPdfLaboratorio.atendimento_id)
        .join(Paciente, Paciente.id == Atendimento.paciente_id)
        .join(ImportacaoPdfLaboratorio, ImportacaoPdfLaboratorio.id == ResultadoPdfLaboratorio.importacao_id)
        .where(
            ImportacaoPdfLaboratorio.status == "VALIDADA",
            ResultadoPdfLaboratorio.situacao == "POSITIVA",
        )
    )
    if start_at:
        clinical_stmt = clinical_stmt.where(CulturaAtendimento.data_hora_coleta >= start_at)
        pdf_stmt = pdf_stmt.where(ResultadoPdfLaboratorio.data_coleta >= start_at)
    if end_at:
        clinical_stmt = clinical_stmt.where(CulturaAtendimento.data_hora_coleta <= end_at)
        pdf_stmt = pdf_stmt.where(ResultadoPdfLaboratorio.data_coleta <= end_at)
    if unit:
        clinical_stmt = clinical_stmt.where(Atendimento.unidade_atual.ilike(f"%{unit}%"))
        pdf_stmt = pdf_stmt.where(Atendimento.unidade_atual.ilike(f"%{unit}%"))
    if status == "ATIVO":
        clinical_stmt = clinical_stmt.where(Atendimento.ativo.is_(True))
        pdf_stmt = pdf_stmt.where(Atendimento.ativo.is_(True))
    if status == "ENCERRADO":
        clinical_stmt = clinical_stmt.where(Atendimento.ativo.is_(False))
        pdf_stmt = pdf_stmt.where(Atendimento.ativo.is_(False))

    cultures: list[dict] = []
    attendance_ids: set[int] = set()
    for culture, attendance, patient in db.execute(clinical_stmt).all():
        attendance_ids.add(attendance.id)
        cultures.append({
            "attendance_id": attendance.id,
            "collection": culture.data_hora_coleta,
            "result_at": culture.data_hora_resultado,
            "attendance": attendance.id_origem_atendimento,
            "patient": patient.id_origem_paciente,
            "unit": attendance.unidade_atual,
            "bed": attendance.leito_atual,
            "exam": " / ".join(filter(None, [culture.exame, culture.material])),
            "microorganism": culture.microorganismo,
            "result": culture.resultado,
            "source": "Integração hospitalar",
            "active": attendance.ativo,
        })

    latest_pdf: dict[tuple[int, str, str], tuple[ResultadoPdfLaboratorio, Atendimento, Paciente]] = {}
    for result, attendance, patient in db.execute(pdf_stmt).all():
        normalized_exam = " ".join(result.exame_amostra.strip().casefold().split()).removesuffix(" cultura")
        key = (attendance.id, result.os_pedido, f"{result.data_coleta.isoformat()}:{normalized_exam}")
        current = latest_pdf.get(key)
        if current is None or result.data_resultado > current[0].data_resultado:
            latest_pdf[key] = (result, attendance, patient)
    for result, attendance, patient in latest_pdf.values():
        attendance_ids.add(attendance.id)
        cultures.append({
            "attendance_id": attendance.id,
            "collection": result.data_coleta,
            "result_at": result.data_resultado,
            "attendance": attendance.id_origem_atendimento,
            "patient": patient.id_origem_paciente,
            "unit": attendance.unidade_atual,
            "bed": attendance.leito_atual,
            "exam": result.exame_amostra,
            "microorganism": None,
            "result": result.resultado,
            "source": "PDF validado",
            "active": attendance.ativo,
        })

    antimicrobials: dict[int, set[str]] = {}
    procedures: dict[int, set[str]] = {}
    if attendance_ids:
        for attendance_id, name in db.execute(
            select(AntimicrobianoAtendimento.atendimento_id, AntimicrobianoAtendimento.nome_antimicrobiano)
            .where(AntimicrobianoAtendimento.atendimento_id.in_(attendance_ids))
        ):
            antimicrobials.setdefault(attendance_id, set()).add(name)
        for attendance_id, name in db.execute(
            select(ProcedimentoInvasivoAtendimento.atendimento_id, ProcedimentoInvasivoAtendimento.procedimento)
            .where(ProcedimentoInvasivoAtendimento.atendimento_id.in_(attendance_ids))
        ):
            procedures.setdefault(attendance_id, set()).add(name)

    cultures.sort(key=lambda item: (item["collection"], item["result_at"] or item["collection"]), reverse=True)
    return [
        {
            "Coleta": item["collection"],
            "Resultado em": item["result_at"],
            "Atendimento": item["attendance"],
            "Paciente": item["patient"],
            "Unidade": item["unit"],
            "Leito": item["bed"],
            "Exame / amostra": item["exam"],
            "Microrganismo": item["microorganism"],
            "Resultado": item["result"],
            "Antimicrobiano": (
                f"Sim: {', '.join(sorted(antimicrobials[item['attendance_id']]))}"
                if item["attendance_id"] in antimicrobials else "Não"
            ),
            "Procedimento invasivo": (
                f"Sim: {', '.join(sorted(procedures[item['attendance_id']]))}"
                if item["attendance_id"] in procedures else "Não"
            ),
            "Fonte": item["source"],
            "Status atendimento": "ATIVO" if item["active"] else "ENCERRADO",
        }
        for item in cultures[:5000]
    ]


def _rows(db: Session, report_type: str, start: date | None, end: date | None, unit: str | None, status: str | None) -> list[dict]:
    start_at, end_at = _period(start, end)
    if report_type == "positive_cultures":
        return _positive_culture_rows(db, start_at, end_at, unit, status)
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
    output = BytesIO()
    document = SimpleDocTemplate(
        output, pagesize=landscape(A4),
        leftMargin=10 * mm, rightMargin=10 * mm, topMargin=16 * mm, bottomMargin=14 * mm,
        title=f"SANATIO - {title}", author="SANATIO",
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("ReportTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=16, leading=19, textColor=colors.HexColor("#092F3A"), spaceAfter=2 * mm)
    meta_style = ParagraphStyle("ReportMeta", parent=styles["Normal"], fontSize=8, leading=10, textColor=colors.HexColor("#52666D"))
    header_style = ParagraphStyle("TableHeader", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=7, leading=8, textColor=colors.white)
    cell_style = ParagraphStyle("TableCell", parent=styles["Normal"], fontSize=6.5, leading=8, textColor=colors.HexColor("#17333C"))
    story = [
        Paragraph(f"SANATIO | {escape(title)}", title_style),
        Paragraph(f"Emitido em {datetime.now().strftime('%d/%m/%Y %H:%M')} &nbsp;&nbsp;|&nbsp;&nbsp; {len(rows)} registro(s)", meta_style),
        Spacer(1, 5 * mm),
    ]
    if rows:
        headers = list(rows[0])
        table_data = [[Paragraph(escape(header), header_style) for header in headers]]
        table_data.extend([[Paragraph(escape(_display_value(row.get(header))), cell_style) for header in headers] for row in rows])
        available_width = landscape(A4)[0] - 20 * mm
        weights = [max(9, min(28, max(len(str(header)), max((len(_display_value(row.get(header))) for row in rows[:100]), default=0)))) for header in headers]
        weight_total = sum(weights)
        column_widths = [available_width * weight / weight_total for weight in weights]
        table = LongTable(table_data, colWidths=column_widths, repeatRows=1, splitByRow=True)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#008C99")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#C7D8DD")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F7F8")]),
        ]))
        story.append(table)
    else:
        story.append(Paragraph("Nenhum registro encontrado para os filtros informados.", styles["Normal"]))

    def footer(canvas, doc) -> None:
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#C7D8DD"))
        canvas.line(10 * mm, 10 * mm, landscape(A4)[0] - 10 * mm, 10 * mm)
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#52666D"))
        canvas.drawString(10 * mm, 6 * mm, "SANATIO - Uso assistencial")
        canvas.drawRightString(landscape(A4)[0] - 10 * mm, 6 * mm, f"Página {doc.page}")
        canvas.restoreState()

    document.build(story, onFirstPage=footer, onLaterPages=footer)
    return output.getvalue()


@router.get("/clinical.pdf")
def clinical_report_pdf(report_type: str, start: date | None = None, end: date | None = None, unit: str | None = None, status: str | None = None, db: Session = Depends(get_db)) -> StreamingResponse:
    rows = _rows(db, report_type, start, end, unit, status)
    return StreamingResponse(BytesIO(_pdf_bytes(REPORT_LABELS.get(report_type, report_type), rows)), media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="sanatio-{report_type}.pdf"'})
