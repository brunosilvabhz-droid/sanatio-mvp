import hashlib
from datetime import datetime, timezone
from pathlib import PurePath

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.clinical import Atendimento, CulturaAtendimento, SolicitacaoExameAtendimento
from app.models.lab_pdf_import import ImportacaoPdfLaboratorio, ResultadoPdfLaboratorio
from app.models.user import User
from app.services.lab_pdf_parser import parse_lab_pdf

router = APIRouter(prefix="/lab-pdf", tags=["Relatórios do laboratório"])


def require_lab_user(user: User = Depends(get_current_user)) -> User:
    if user.role.name not in {"ADMIN", "SCIH"}:
        raise HTTPException(status_code=403, detail="Acesso restrito à equipe SCIH")
    return user


class LinkRequest(BaseModel):
    cd_atendimento: str
    confirmar_sem_os: bool = False


def _candidate_attendances(db: Session, os_pedido: str) -> list[Atendimento]:
    cultures = list(db.scalars(
        select(Atendimento)
        .join(CulturaAtendimento, CulturaAtendimento.atendimento_id == Atendimento.id)
        .where(CulturaAtendimento.id_origem_pedido.in_([os_pedido, f"750.{os_pedido}"]))
        .distinct()
    ))
    requests = list(db.scalars(
        select(Atendimento)
        .join(SolicitacaoExameAtendimento, SolicitacaoExameAtendimento.atendimento_id == Atendimento.id)
        .where(SolicitacaoExameAtendimento.id_origem_pedido.in_([os_pedido, f"750.{os_pedido}"]))
        .distinct()
    ))
    return list({attendance.id: attendance for attendance in cultures + requests}.values())


def _row_read(row: ResultadoPdfLaboratorio, user: User, db: Session) -> dict:
    linked = db.get(Atendimento, row.atendimento_id) if row.atendimento_id else None
    suggested = db.get(Atendimento, row.atendimento_sugerido_id) if row.atendimento_sugerido_id else None
    return {
        "id": row.id,
        "pagina": row.pagina,
        "os_pedido": row.os_pedido,
        "nome_relatorio": row.nome_relatorio if user.can_view_patient_name else None,
        "data_coleta": row.data_coleta,
        "data_resultado": row.data_resultado,
        "exame_amostra": row.exame_amostra,
        "resultado": row.resultado,
        "situacao": row.situacao,
        "cd_atendimento_sugerido": suggested.id_origem_atendimento if suggested else None,
        "cd_atendimento": linked.id_origem_atendimento if linked else None,
    }


@router.post("/imports")
async def import_pdf(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_lab_user),
) -> dict:
    filename = PurePath(file.filename or "relatorio.pdf").name
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=422, detail="Selecione um arquivo PDF")
    content = await file.read(10 * 1024 * 1024 + 1)
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="O PDF excede 10 MB")
    digest = hashlib.sha256(content).hexdigest()
    existing = db.scalar(select(ImportacaoPdfLaboratorio).where(ImportacaoPdfLaboratorio.sha256 == digest))
    if existing:
        raise HTTPException(status_code=409, detail=f"Este PDF já foi importado (importação {existing.id})")
    try:
        pages, parsed = parse_lab_pdf(content)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    batch = ImportacaoPdfLaboratorio(
        nome_arquivo=filename, sha256=digest, paginas=pages,
        total_resultados=len(parsed), usuario_id=user.id,
    )
    db.add(batch)
    db.flush()
    candidates_by_os: dict[str, list[Atendimento]] = {}
    for order, item in enumerate(parsed, start=1):
        os_pedido = item["os_pedido"]
        if os_pedido not in candidates_by_os:
            candidates_by_os[os_pedido] = _candidate_attendances(db, os_pedido)
        candidates = candidates_by_os[os_pedido]
        db.add(ResultadoPdfLaboratorio(
            importacao_id=batch.id, ordem=order, **item,
            atendimento_sugerido_id=candidates[0].id if len(candidates) == 1 else None,
        ))
    db.commit()
    return {"id": batch.id, "paginas": pages, "total_resultados": len(parsed), "sugestoes": sum(len(candidates_by_os[row["os_pedido"]]) == 1 for row in parsed)}


@router.get("/imports")
def list_imports(db: Session = Depends(get_db), _: User = Depends(require_lab_user)) -> list[dict]:
    batches = db.scalars(select(ImportacaoPdfLaboratorio).order_by(ImportacaoPdfLaboratorio.id.desc()).limit(30)).all()
    return [{"id": batch.id, "nome_arquivo": batch.nome_arquivo, "paginas": batch.paginas,
             "total_resultados": batch.total_resultados, "importado_em": batch.importado_em} for batch in batches]


@router.get("/imports/{import_id}/results")
def list_results(import_id: int, db: Session = Depends(get_db), user: User = Depends(require_lab_user)) -> list[dict]:
    if not db.get(ImportacaoPdfLaboratorio, import_id):
        raise HTTPException(status_code=404, detail="Importação não encontrada")
    rows = db.scalars(select(ResultadoPdfLaboratorio).where(ResultadoPdfLaboratorio.importacao_id == import_id).order_by(ResultadoPdfLaboratorio.ordem)).all()
    response = []
    for row in rows:
        item = _row_read(row, user, db)
        if not row.atendimento_id and not row.atendimento_sugerido_id:
            candidates = _candidate_attendances(db, row.os_pedido)
            if len(candidates) == 1:
                item["cd_atendimento_sugerido"] = candidates[0].id_origem_atendimento
        response.append(item)
    return response


@router.post("/imports/{import_id}/confirm-suggestions")
def confirm_suggestions(import_id: int, db: Session = Depends(get_db), user: User = Depends(require_lab_user)) -> dict:
    if not db.get(ImportacaoPdfLaboratorio, import_id):
        raise HTTPException(status_code=404, detail="Importação não encontrada")
    rows = db.scalars(select(ResultadoPdfLaboratorio).where(
        ResultadoPdfLaboratorio.importacao_id == import_id,
        ResultadoPdfLaboratorio.atendimento_id.is_(None),
    )).all()
    linked = 0
    for row in rows:
        candidates = _candidate_attendances(db, row.os_pedido)
        if len(candidates) != 1:
            continue
        row.atendimento_id = candidates[0].id
        row.atendimento_sugerido_id = candidates[0].id
        row.vinculado_por_id = user.id
        row.vinculado_em = datetime.now(timezone.utc)
        linked += 1
    db.commit()
    return {"vinculados": linked}


@router.post("/results/{result_id}/link")
def link_result(result_id: int, payload: LinkRequest, db: Session = Depends(get_db), user: User = Depends(require_lab_user)) -> dict:
    row = db.get(ResultadoPdfLaboratorio, result_id)
    if not row:
        raise HTTPException(status_code=404, detail="Resultado não encontrado")
    attendance = db.scalar(select(Atendimento).where(Atendimento.id_origem_atendimento == payload.cd_atendimento.strip()))
    if not attendance:
        raise HTTPException(status_code=404, detail="Atendimento não encontrado no SANATIO")
    candidates = _candidate_attendances(db, row.os_pedido)
    if candidates and attendance.id not in {candidate.id for candidate in candidates}:
        raise HTTPException(status_code=422, detail="A OS está vinculada a outro atendimento nas culturas do SOUL")
    if not candidates and not payload.confirmar_sem_os:
        raise HTTPException(status_code=422, detail="A OS não foi localizada no SOUL; confirme explicitamente o vínculo manual")
    row.atendimento_id = attendance.id
    row.vinculado_por_id = user.id
    row.vinculado_em = datetime.now(timezone.utc)
    db.commit()
    return _row_read(row, user, db)


@router.get("/patients/{cd_atendimento}/results")
def patient_results(cd_atendimento: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[dict]:
    attendance = db.scalar(select(Atendimento).where(Atendimento.id_origem_atendimento == cd_atendimento))
    if not attendance:
        return []
    rows = db.scalars(select(ResultadoPdfLaboratorio).where(ResultadoPdfLaboratorio.atendimento_id == attendance.id).order_by(ResultadoPdfLaboratorio.data_resultado.desc())).all()
    return [_row_read(row, user, db) for row in rows]
