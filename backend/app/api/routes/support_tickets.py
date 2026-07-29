from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.support_ticket import SupportTicket
from app.models.user import User
from app.schemas.support_ticket import SupportTicketCreate, SupportTicketRead, SupportTicketUpdate
from app.services.email_service import send_email

router = APIRouter(prefix="/support/tickets", tags=["Chamados"])

VALID_CATEGORIES = {"ERRO", "DUVIDA", "SOLICITACAO"}
VALID_STATUSES = {"ABERTO", "EM_ANALISE", "RESPONDIDO", "RESOLVIDO", "CANCELADO"}


def _ticket_to_read(ticket: SupportTicket) -> SupportTicketRead:
    return SupportTicketRead(
        id=ticket.id,
        category=ticket.category,
        title=ticket.title,
        description=ticket.description,
        status=ticket.status,
        requester_user_id=ticket.requester_user_id,
        requester_name=ticket.requester.full_name if ticket.requester else None,
        requester_email=ticket.requester.email if ticket.requester else None,
        responder_user_id=ticket.responder_user_id,
        responder_name=ticket.responder.full_name if ticket.responder else None,
        admin_response=ticket.admin_response,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        responded_at=ticket.responded_at,
    )


def _send_created_email(ticket: SupportTicket, requester: User) -> None:
    body = (
        "Chamado aberto no SANATIO.\n\n"
        f"Numero: #{ticket.id}\n"
        f"Categoria: {ticket.category}\n"
        f"Solicitante: {requester.full_name} <{requester.email}>\n"
        f"Titulo: {ticket.title}\n\n"
        f"Descricao:\n{ticket.description}\n\n"
        "Acompanhe o andamento pela tela de Suporte do SANATIO."
    )
    send_email(
        to=[requester.email, settings.support_contact_email],
        subject=f"[SANATIO] Chamado #{ticket.id} aberto - {ticket.title}",
        body=body,
    )


def _send_updated_email(ticket: SupportTicket) -> None:
    if not ticket.requester:
        return
    body = (
        "Seu chamado no SANATIO foi atualizado.\n\n"
        f"Numero: #{ticket.id}\n"
        f"Categoria: {ticket.category}\n"
        f"Status: {ticket.status}\n"
        f"Titulo: {ticket.title}\n\n"
        f"Resposta:\n{ticket.admin_response or 'Sem resposta informada.'}\n\n"
        "Acompanhe o andamento pela tela de Suporte do SANATIO."
    )
    send_email(
        to=[ticket.requester.email],
        subject=f"[SANATIO] Chamado #{ticket.id} atualizado - {ticket.status}",
        body=body,
    )


@router.get("", response_model=list[SupportTicketRead])
def list_tickets(
    status: str | None = None,
    category: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[SupportTicketRead]:
    stmt = (
        select(SupportTicket)
        .options(selectinload(SupportTicket.requester), selectinload(SupportTicket.responder))
        .order_by(SupportTicket.created_at.desc())
    )
    if current_user.role.name != "ADMIN":
        stmt = stmt.where(SupportTicket.requester_user_id == current_user.id)
    if status:
        stmt = stmt.where(SupportTicket.status == status)
    if category:
        stmt = stmt.where(SupportTicket.category == category)
    return [_ticket_to_read(ticket) for ticket in db.scalars(stmt).all()]


@router.post("", response_model=SupportTicketRead)
def create_ticket(
    payload: SupportTicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SupportTicketRead:
    category = payload.category.strip().upper()
    if category not in VALID_CATEGORIES:
        raise HTTPException(status_code=422, detail="Categoria invalida")
    if not payload.title.strip() or not payload.description.strip():
        raise HTTPException(status_code=422, detail="Titulo e descricao sao obrigatorios")

    ticket = SupportTicket(
        category=category,
        title=payload.title.strip(),
        description=payload.description.strip(),
        requester_user_id=current_user.id,
        status="ABERTO",
    )
    db.add(ticket)
    db.commit()
    ticket = db.scalar(
        select(SupportTicket)
        .options(selectinload(SupportTicket.requester), selectinload(SupportTicket.responder))
        .where(SupportTicket.id == ticket.id)
    )
    _send_created_email(ticket, current_user)
    return _ticket_to_read(ticket)


@router.patch("/{ticket_id}", response_model=SupportTicketRead)
def update_ticket(
    ticket_id: int,
    payload: SupportTicketUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SupportTicketRead:
    if current_user.role.name != "ADMIN":
        raise HTTPException(status_code=403, detail="Apenas ADMIN pode responder chamados")
    status = payload.status.strip().upper()
    if status not in VALID_STATUSES:
        raise HTTPException(status_code=422, detail="Status invalido")

    ticket = db.scalar(
        select(SupportTicket)
        .options(selectinload(SupportTicket.requester), selectinload(SupportTicket.responder))
        .where(SupportTicket.id == ticket_id)
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="Chamado nao encontrado")

    ticket.status = status
    ticket.admin_response = (payload.admin_response or "").strip() or ticket.admin_response
    ticket.responder_user_id = current_user.id
    ticket.responded_at = datetime.now(timezone.utc)
    db.commit()
    ticket = db.scalar(
        select(SupportTicket)
        .options(selectinload(SupportTicket.requester), selectinload(SupportTicket.responder))
        .where(SupportTicket.id == ticket_id)
    )
    _send_updated_email(ticket)
    return _ticket_to_read(ticket)
