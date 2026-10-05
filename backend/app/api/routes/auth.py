from collections import defaultdict, deque
from threading import Lock
from time import monotonic

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, UserRead

router = APIRouter(prefix="/auth", tags=["Autenticação"])

LOGIN_WINDOW_SECONDS = 15 * 60
LOGIN_MAX_FAILURES = 5
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
        _prune_failures(key, now).append(now)


def _clear_login_failures(key: str) -> None:
    with _login_lock:
        _login_failures.pop(key, None)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)) -> TokenResponse:
    key = _login_key(request, payload.email)
    _check_login_limit(key)
    user = db.scalar(select(User).where(User.email == payload.email, User.active.is_(True)))
    valid_password = verify_password(payload.password, user.hashed_password if user else _dummy_password_hash)
    if not user or not valid_password:
        _record_login_failure(key)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="E-mail ou senha inválidos")
    _clear_login_failures(key)
    return TokenResponse(access_token=create_access_token(user.email, {"role": user.role.name}))


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
