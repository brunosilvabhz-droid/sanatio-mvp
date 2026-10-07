from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "SANATIO"
    environment: str = "development"
    app_public_url: str = ""
    database_url: str = "postgresql+psycopg://sanatio:sanatio@localhost:5432/sanatio"
    secret_key: str = "development-only-key-change-before-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 720
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    trusted_hosts: str = "localhost,127.0.0.1,192.168.18.175"
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
    smtp_use_tls: bool = True
    password_reset_token_expire_minutes: int = 30
    alert_email_enabled: bool = True
    alert_notification_emails: str = ""
    alert_notification_roles: str = "SCIH,INFECTO"
    support_contact_email: str = "contato@impactocg.com"
    cors_origin_regex: str = r"https?://(localhost|127\.0\.0\.1|10\..+|192\.168\..+|172\.(1[6-9]|2[0-9]|3[0-1])\..+):5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def trusted_host_list(self) -> list[str]:
        return [host.strip() for host in self.trusted_hosts.split(",") if host.strip()]

    @property
    def alert_notification_email_list(self) -> list[str]:
        return [email.strip().lower() for email in self.alert_notification_emails.split(",") if email.strip()]

    @property
    def alert_notification_role_list(self) -> list[str]:
        return [role.strip().upper() for role in self.alert_notification_roles.split(",") if role.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @model_validator(mode="after")
    def validate_production_secrets(self):
        if self.is_production and (
            self.secret_key in {"change-me", "change-me-in-production", "development-only-key-change-before-production"}
            or len(self.secret_key) < 32
        ):
            raise ValueError("SECRET_KEY de producao deve ter pelo menos 32 caracteres e nao pode usar o valor padrao")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
