import csv
import io
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.alert import AlertAction
from app.models.antimicrobial_audit import AntimicrobialAuditAction
from app.models.intervention import InterventionRecipient, InterventionRequest
from app.models.user import User
from app.schemas.intervention import (
    InterventionCreate,
    InterventionRead,
    InterventionResponseUpdate,
    RecipientRead,
)
from app.services.email_service import send_email

router = APIRouter(tags=["Intervencoes"])


def _intervention_to_read(item: InterventionRequest) -> InterventionRead:
    return InterventionRead(
        id=item.id,
        cd_atendimento=item.cd_atendimento,
        cd_paciente=item.cd_paciente,
        source_type=item.source_type,
        source_id=item.source_id,
        reason=item.reason,
        message=item.message,
        status=item.status,
        requested_by_user_id=item.requested_by_user_id,
        requested_by_name=item.requested_by.full_name if item.requested_by else None,
        responded_by_user_id=item.responded_by_user_id,
        responded_by_name=item.responded_by.full_name if item.responded_by else None,
        response=item.response,
        response_justification=item.response_justification,
        created_at=item.created_at,
        responded_at=item.responded_at,
        updated_at=item.updated_at,
        recipients=[
            {
                "id": recipient.id,
                "user_id": recipient.user_id,
                "email": recipient.email,
                "user_name": recipient.user.full_name if recipient.user else None,
                "status": recipient.status,
                "created_at": recipient.created_at,
            }
            for recipient in item.recipients
        ],
    )


def _intervention_url(intervention_id: int) -> str:
    if not settings.app_public_url:
        return "Acesse a tela de Intervencoes no SANATIO."
    return f"{settings.app_public_url.rstrip('/')}/interventions?intervention={intervention_id}"


def _send_intervention_email(item: InterventionRequest, recipients: list[User], requester: User) -> bool:
    body = (
        "Uma intervencao foi solicitada no SANATIO.\n\n"
        f"Intervencao: #{item.id}\n"
        f"Paciente ID: {item.cd_paciente}\n"
        f"Atendimento ID: {item.cd_atendimento}\n"
        f"Solicitante: {requester.full_name}\n\n"
        f"Motivo do alerta:\n{item.reason}\n\n"
        f"Mensagem do SCIH:\n{item.message}\n\n"
        "Por seguranca, o nome do paciente nao e enviado por e-mail.\n"
        "Acesse o SANATIO para aceitar ou recusar a intervencao e registrar a justificativa.\n\n"
        f"Link: {_intervention_url(item.id)}"
    )
    return send_email(
        to=[user.email for user in recipients],
        subject=f"[SANATIO] Intervencao #{item.id} - Atendimento {item.cd_atendimento}",
        body=body,
    )


def _send_intervention_response_email(item: InterventionRequest, responder: User) -> bool:
    if not item.requested_by:
        return False
    body = (
        "Uma intervencao solicitada no SANATIO recebeu resposta.\n\n"
        f"Intervencao: #{item.id}\n"
        f"Paciente ID: {item.cd_paciente}\n"
        f"Atendimento ID: {item.cd_atendimento}\n"
        f"Respondido por: {responder.full_name}\n"
        f"Resposta: {item.response}\n\n"
        f"Justificativa:\n{item.response_justification}\n\n"
        "Por seguranca, o nome do paciente nao e enviado por e-mail.\n\n"
        f"Link: {_intervention_url(item.id)}"
    )
    return send_email(
        to=[item.requested_by.email],
        subject=f"[SANATIO] Intervencao #{item.id} respondida - {item.response}",
        body=body,
    )


@router.get("/recipients", response_model=list[RecipientRead])
def recipients(db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> list[dict]:
    users = db.scalars(
        select(User)
        .options(selectinload(User.role))
        .where(User.active.is_(True))
        .order_by(case((User.role.has(name="MEDICO"), 1), (User.role.has(name="INFECTO"), 2), else_=3), User.full_name)
    ).all()
    return [{"id": user.id, "email": user.email, "full_name": user.full_name, "role_name": user.role.name} for user in users]


@router.get("/interventions", response_model=list[InterventionRead])
def list_interventions(
    atendimento: str | None = None,
    paciente: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[InterventionRead]:
    stmt = (
        select(InterventionRequest)
        .options(
            selectinload(InterventionRequest.requested_by),
            selectinload(InterventionRequest.responded_by),
            selectinload(InterventionRequest.recipients).selectinload(InterventionRecipient.user),
        )
        .order_by(InterventionRequest.created_at.desc())
    )
    if atendimento:
        stmt = stmt.where(InterventionRequest.cd_atendimento.ilike(f"%{atendimento}%"))
    if paciente:
        stmt = stmt.where(InterventionRequest.cd_paciente.ilike(f"%{paciente}%"))
    if status:
        stmt = stmt.where(InterventionRequest.status == status)
    return [_intervention_to_read(item) for item in db.scalars(stmt).all()]


@router.post("/interventions", response_model=InterventionRead)
def create_intervention(
    payload: InterventionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> InterventionRead:
    if not payload.recipient_user_ids:
        raise HTTPException(status_code=422, detail="Selecione ao menos um destinatario")
    recipients = db.scalars(select(User).where(User.id.in_(payload.recipient_user_ids), User.active.is_(True))).all()
    if len(recipients) != len(set(payload.recipient_user_ids)):
        raise HTTPException(status_code=422, detail="Destinatario invalido")

    item = InterventionRequest(
        cd_atendimento=payload.cd_atendimento,
        cd_paciente=payload.cd_paciente,
        source_type=payload.source_type,
        source_id=payload.source_id,
        reason=payload.reason,
        message=payload.message,
        requested_by_user_id=current_user.id,
        status="ENVIADA",
    )
    db.add(item)
    db.flush()
    recipient_rows = []
    for user in recipients:
        recipient = InterventionRecipient(intervention_id=item.id, user_id=user.id, email=user.email, status="ENVIADO")
        recipient_rows.append(recipient)
        db.add(recipient)

    if payload.source_type == "ALERT" and payload.source_id:
        db.add(AlertAction(alert_id=payload.source_id, user_id=current_user.id, action="INTERVENTION_SENT", comment=payload.message))
    if payload.source_type == "ANTIMICROBIAL_AUDIT" and payload.source_id:
        db.add(
            AntimicrobialAuditAction(
                audit_id=payload.source_id,
                user_id=current_user.id,
                action="INTERVENTION_SENT",
                status="INTERVENCAO_SUGERIDA",
                comment=payload.message,
            )
        )
    email_sent = _send_intervention_email(item, recipients, current_user)
    if not email_sent:
        for recipient in recipient_rows:
            recipient.status = "EMAIL_NAO_ENVIADO"
    db.commit()
    item = db.scalar(
        select(InterventionRequest)
        .options(
            selectinload(InterventionRequest.requested_by),
            selectinload(InterventionRequest.responded_by),
            selectinload(InterventionRequest.recipients).selectinload(InterventionRecipient.user),
        )
        .where(InterventionRequest.id == item.id)
    )
    return _intervention_to_read(item)


@router.patch("/interventions/{intervention_id}/response", response_model=InterventionRead)
def respond_intervention(
    intervention_id: int,
    payload: InterventionResponseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> InterventionRead:
    if payload.response not in {"ACEITA", "RECUSADA"}:
        raise HTTPException(status_code=422, detail="Resposta invalida")
    if not payload.justification.strip():
        raise HTTPException(status_code=422, detail="Justificativa obrigatoria")
    item = db.scalar(
        select(InterventionRequest)
        .options(selectinload(InterventionRequest.recipients))
        .where(InterventionRequest.id == intervention_id)
    )
    if not item:
        raise HTTPException(status_code=404, detail="Intervencao nao encontrada")
    item.status = payload.response
    item.response = payload.response
    item.response_justification = payload.justification
    item.responded_by_user_id = current_user.id
    item.responded_at = datetime.now(timezone.utc)
    for recipient in item.recipients:
        if recipient.user_id == current_user.id:
            recipient.status = payload.response
    db.commit()
    item = db.scalar(
        select(InterventionRequest)
        .options(
            selectinload(InterventionRequest.requested_by),
            selectinload(InterventionRequest.responded_by),
            selectinload(InterventionRequest.recipients).selectinload(InterventionRecipient.user),
        )
        .where(InterventionRequest.id == intervention_id)
    )
    _send_intervention_response_email(item, current_user)
    return _intervention_to_read(item)


@router.get("/reports/interventions.csv")
def interventions_csv(db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> Response:
    rows = db.scalars(select(InterventionRequest).options(selectinload(InterventionRequest.requested_by)).order_by(InterventionRequest.created_at.desc())).all()
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["id", "created_at", "cd_paciente", "cd_atendimento", "source_type", "status", "requested_by", "response", "response_justification"])
    writer.writeheader()
    for row in rows:
        writer.writerow(
            {
                "id": row.id,
                "created_at": row.created_at,
                "cd_paciente": row.cd_paciente,
                "cd_atendimento": row.cd_atendimento,
                "source_type": row.source_type,
                "status": row.status,
                "requested_by": row.requested_by.full_name if row.requested_by else "Sistema",
                "response": row.response,
                "response_justification": row.response_justification,
            }
        )
    return Response(output.getvalue(), media_type="text/csv; charset=utf-8", headers={"Content-Disposition": 'attachment; filename="sanatio-intervencoes.csv"'})


@router.get("/reports/interventions.pdf")
def interventions_pdf(db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> Response:
    total = db.scalar(select(func.count()).select_from(InterventionRequest)) or 0
    accepted = db.scalar(select(func.count()).select_from(InterventionRequest).where(InterventionRequest.status == "ACEITA")) or 0
    rejected = db.scalar(select(func.count()).select_from(InterventionRequest).where(InterventionRequest.status == "RECUSADA")) or 0
    body = f"SANATIO - Relatorio de intervencoes\\n\\nTotal: {total}\\nAceitas: {accepted}\\nRecusadas: {rejected}\\nGerado automaticamente pelo MVP."
    pdf = _simple_pdf(body)
    return Response(pdf, media_type="application/pdf", headers={"Content-Disposition": 'attachment; filename="sanatio-intervencoes.pdf"'})


def _simple_pdf(text: str) -> bytes:
    escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)").replace("\n", ") Tj T* (")
    stream = f"BT /F1 12 Tf 72 760 Td 16 TL ({escaped}) Tj ET".encode()
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    result = b"%PDF-1.4\n"
    offsets = []
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(result))
        result += f"{index} 0 obj\n".encode() + obj + b"\nendobj\n"
    xref = len(result)
    result += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    for offset in offsets:
        result += f"{offset:010d} 00000 n \n".encode()
    result += f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode()
    return result
