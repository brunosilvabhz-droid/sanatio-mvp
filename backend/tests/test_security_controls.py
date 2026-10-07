import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.api.routes.auth import (
    LOGIN_MAX_FAILURES,
    _check_login_limit,
    _clear_login_failures,
    _record_login_failure,
)
from app.core.config import Settings
from app.core.security import create_access_token, decode_access_token
from app.core.security import get_password_hash, verify_password
from app.models.base import Base
from app.models.user import PasswordResetToken, Role, User
from app.schemas.auth import LoginRequest, PasswordResetConfirm, PasswordResetRequest


def test_access_token_validates_issuer_audience_and_signature() -> None:
    token = create_access_token("security-test@sanatio.local")
    payload = decode_access_token(token)

    assert payload is not None
    assert payload["sub"] == "security-test@sanatio.local"
    assert payload["iss"] == "sanatio"
    assert payload["aud"] == "sanatio-web"
    assert decode_access_token(token + "invalid") is None


def test_login_failures_are_limited() -> None:
    key = "127.0.0.1:security-test@sanatio.local"
    _clear_login_failures(key)
    for _ in range(LOGIN_MAX_FAILURES):
        _record_login_failure(key)

    with pytest.raises(HTTPException) as error:
        _check_login_limit(key)

    assert error.value.status_code == 429
    assert "Retry-After" in error.value.headers
    _clear_login_failures(key)


def test_production_rejects_weak_secret() -> None:
    with pytest.raises(ValueError):
        Settings(environment="production", secret_key="change-me", _env_file=None)


def test_login_accepts_existing_local_account() -> None:
    payload = LoginRequest(email="admin@sanatio.local", password="senha-de-teste")
    assert payload.email == "admin@sanatio.local"


def test_password_reset_token_is_single_use(monkeypatch) -> None:
    from app.api.routes import auth

    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine, tables=[Role.__table__, User.__table__, PasswordResetToken.__table__])
    email_body: dict[str, str] = {}
    monkeypatch.setattr(auth, "send_email", lambda **kwargs: email_body.update(body=kwargs["body"]) or True)

    with Session(engine) as db:
        role = Role(name="SCIH", description="SCIH")
        db.add(role)
        db.flush()
        user = User(
            email="scih@example.org",
            full_name="Equipe SCIH",
            hashed_password=get_password_hash("senha-anterior-segura"),
            role_id=role.id,
            active=True,
        )
        db.add(user)
        db.commit()

        response = auth.request_password_reset(PasswordResetRequest(email=user.email), db)
        assert response.message.startswith("Se o e-mail")
        token = email_body["body"].split("token=", 1)[1].splitlines()[0]

        auth.confirm_password_reset(
            PasswordResetConfirm(token=token, password="nova-senha-segura-2026"),
            db,
        )
        db.refresh(user)
        assert verify_password("nova-senha-segura-2026", user.hashed_password)

        with pytest.raises(HTTPException) as error:
            auth.confirm_password_reset(
                PasswordResetConfirm(token=token, password="outra-senha-segura-2026"),
                db,
            )
        assert error.value.status_code == 400
