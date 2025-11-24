# app/core/settings.py
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal


class SMTPSettings(BaseModel):
    host: str
    port: int
    user: str
    password: str
    from_name: str
    from_email: str


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: Literal["development", "staging", "production"] = "development"
    app_name: str = "HireX API"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    secret_key: str = "please_change_me"

    smtp_host: str = "smtp-relay.brevo.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_pass: str = ""
    smtp_from_name: str = "HireX"
    smtp_from_email: str = "no-reply@hirex.dev"

    mail_debug: bool = False

    @property
    def smtp(self) -> SMTPSettings:
        return SMTPSettings(
            host=self.smtp_host,
            port=self.smtp_port,
            user=self.smtp_user,
            password=self.smtp_pass,
            from_name=self.smtp_from_name,
            from_email=self.smtp_from_email,
        )


settings = Settings()
