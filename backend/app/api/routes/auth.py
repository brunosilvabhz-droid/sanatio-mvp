from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from threading import Lock
from time import monotonic

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_password_reset_token,
    get_password_hash,
    hash_password_reset_token,
    verify_password,
)
from app.models.user import PasswordResetToken, User
from app.schemas.auth import LoginRequest, MessageResponse, PasswordResetConfirm, PasswordResetRequest, TokenResponse, UserRead
from app.services.email_service import send_email

router = APIRouter(prefix="/auth", tags=["Autenticação"])

LOGIN_WINDOW_SECONDS = 15 * 60
LOGIN_MAX_FAILURES = 5
LOGIN_MAX_TRACKED_KEYS = 10_000
_login_failures: dict[str, deque[float]] = defaultdict(deque)
_login_lock = Lock()
_dummy_password_hash = get_password_hash("sanatio-dummy-password")


def _login_key(request: Request, email: str) -> str:
    forwarded = request.headers.get("x-forwarded-for", "").split(",", 1)[0].strip()
    address = forwarded or (request.client.host if request.client else "unknown")
    return f"{address}:{email.strip().lower()}"


def _prune_failures(key: str, now: float) -> deque[float]:
    failures = _login_failures[key]
    while failures and now - failures[0] >= LOGIN_WINDOW_SECONDS:
        failures.popleft()
    return failures


def _check_login_limit(key: str) -> None:
    now = monotonic()
    with _login_lock:
        failures = _prune_failures(key, now)
        if len(failures) >= LOGIN_MAX_FAILURES:
            retry_after = max(int(LOGIN_WINDOW_SECONDS - (now - failures[0])), 1)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Muitas tentativas de acesso. Tente novamente mais tarde.",
                headers={"Retry-After": str(retry_after)},
            )


def _record_login_failure(key: str) -> None:
    now = monotonic()
    with _login_lock:
        if key not in _login_failures and len(_login_failures) >= LOGIN_MAX_TRACKED_KEYS:
            stale_keys = [
                tracked_key for tracked_key, failures in _login_failures.items()
                if not failures or now - failures[-1] >= LOGIN_WINDOW_SECONDS
            ]
            for stale_key in stale_keys:
                _login_failures.pop(stale_key, None)
            if len(_login_failures) >= LOGIN_MAX_TRACKED_KEYS:
                oldest_key = min(_login_failures, key=lambda tracked_key: _login_failures[tracked_key][-1])
                _login_failures.pop(oldest_key, None)
        _prune_failures(key, now).append(now)


def _clear_login_failures(key: str) -> None:
    with _login_lock:
        _login_failures.pop(key, None)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)) -> TokenResponse:
    key = _login_key(request, payload.email)
    _check_login_limit(key)
    user = db.scalar(select(User).where(func.lower(User.email) == payload.email.strip().lower(), User.active.is_(True)))
    valid_password = verify_password(payload.password, user.hashed_password if user else _dummy_password_hash)
    if not user or not valid_password:
        _record_login_failure(key)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="E-mail ou senha inválidos")
    _clear_login_failures(key)
    return TokenResponse(access_token=create_access_token(user.email, {"role": user.role.name}))


@router.post("/password-reset/request", response_model=MessageResponse)
def request_password_reset(payload: PasswordResetRequest, db: Session = Depends(get_db)) -> MessageResponse:
    message = "Se o e-mail estiver cadastrado, enviaremos as instruções para redefinir a senha."
    user = db.scalar(select(User).where(func.lower(User.email) == str(payload.email).strip().lower(), User.active.is_(True)))
    if not user:
        return MessageResponse(message=message)

    now = datetime.now(timezone.utc)
    for previous in db.scalars(
        select(PasswordResetToken).where(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used_at.is_(None),
        )
    ):
        previous.used_at = now

    token, token_hash = create_password_reset_token()
    db.add(
        PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=now + timedelta(minutes=settings.password_reset_token_expire_minutes),
        )
    )
    db.commit()

    reset_url = f"{settings.app_public_url.rstrip('/')}/reset-password?token={token}"
    send_email(
        to=[user.email],
        subject="Redefinição de senha do SANATIO",
        body=(
            f"Olá, {user.full_name}.\n\n"
            "Recebemos uma solicitação para redefinir sua senha no SANATIO.\n\n"
            f"Acesse o link abaixo em até {settings.password_reset_token_expire_minutes} minutos:\n"
            f"{reset_url}\n\n"
            "Se você não solicitou a alteração, ignore esta mensagem."
        ),
    )
    return MessageResponse(message=message)


@router.post("/password-reset/confirm", response_model=MessageResponse)
def confirm_password_reset(payload: PasswordResetConfirm, db: Session = Depends(get_db)) -> MessageResponse:
    item = db.scalar(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash == hash_password_reset_token(payload.token),
            PasswordResetToken.used_at.is_(None),
        )
    )
    now = datetime.now(timezone.utc)
    if not item:
        raise HTTPException(status_code=400, detail="Link de redefinição inválido ou já utilizado")
    expires_at = item.expires_at if item.expires_at.tzinfo else item.expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= now or not item.user.active:
        item.used_at = now
        db.commit()
        raise HTTPException(status_code=400, detail="Link de redefinição expirado")

    item.user.hashed_password = get_password_hash(payload.password)
    item.used_at = now
    db.commit()
    return MessageResponse(message="Senha redefinida com sucesso.")


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
