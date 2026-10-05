import pytest
from fastapi import HTTPException

from app.api.routes.auth import (
    LOGIN_MAX_FAILURES,
    _check_login_limit,
    _clear_login_failures,
    _record_login_failure,
)
from app.core.config import Settings
from app.core.security import create_access_token, decode_access_token


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
