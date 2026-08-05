from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "SANATIO"
    app_public_url: str = ""
    database_url: str = "postgresql+psycopg://sanatio:sanatio@localhost:5432/sanatio"
    secret_key: str = "change-me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 720
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    use_mock_soulmv: bool = True
    expose_patient_names_in_api: bool = False

    soulmv_oracle_host: str = ""
    soulmv_oracle_port: int = 1521
    soulmv_oracle_service: str = ""
    soulmv_oracle_user: str = ""
    soulmv_oracle_password: str = Field(default="", repr=False)

    smtp_host: str = "smtp-relay.brevo.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = Field(default="", repr=False)
    smtp_from_email: str = "sanatio@impactocg.com"
    smtp_from_name: str = "SANATIO"
    support_contact_email: str = "contato@impactocg.com"
    cors_origin_regex: str = r"https?://(localhost|127\.0\.0\.1|10\..+|192\.168\..+|172\.(1[6-9]|2[0-9]|3[0-1])\..+):5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
