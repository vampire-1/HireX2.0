# app/config.py
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR_DEFAULT = ROOT / "data"
RESUME_DIR_DEFAULT = DATA_DIR_DEFAULT / "resumes"

class Settings(BaseSettings):
    # ---- Core paths / storage ----
    DATA_DIR: str = DATA_DIR_DEFAULT.as_posix()
    RESUME_DIR: str = RESUME_DIR_DEFAULT.as_posix()
    DB_URL: str = f"sqlite:///{(DATA_DIR_DEFAULT / 'hirex.db').as_posix()}"

    # ---- Embeddings / Vector index ----
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    FAISS_INDEX_PATH: str = (DATA_DIR_DEFAULT / "faiss_index.bin").as_posix()
    FAISS_META_PATH: str = (DATA_DIR_DEFAULT / "faiss_meta.jsonl").as_posix()

    # ---- Auth / JWT ----
    JWT_SECRET: str = os.environ.get("JWT_SECRET", "dev-secret-change-me")
    SECRET_KEY: Optional[str] = os.environ.get("SECRET_KEY")

    # ---- CORS (frontend) ----
    FRONTEND_ORIGINS: str = os.environ.get(
        "FRONTEND_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    )

    # ---- SMTP / Email ----
    SMTP_ENABLED: bool = (os.environ.get("SMTP_ENABLED", "false").lower() == "true")
    SMTP_HOST: str = os.environ.get("SMTP_HOST", "localhost")
    SMTP_PORT: int = int(os.environ.get("SMTP_PORT", "587"))
    SMTP_USER: Optional[str] = os.environ.get("SMTP_USER")
    SMTP_PASS: Optional[str] = os.environ.get("SMTP_PASS")
    SMTP_FROM: str = os.environ.get("SMTP_FROM", "HireX <no-reply@hirex.local>")

    # ---- OCR (optional) ----
    TESSERACT_CMD: Optional[str] = os.environ.get("TESSERACT_CMD")
    POPPLER_PATH: Optional[str] = os.environ.get("POPPLER_PATH")

    # Pydantic Settings config
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",          # ignore unknown keys in .env
        case_sensitive=False,    # allow smtp_enabled / SMTP_ENABLED
    )

    # If SECRET_KEY exists, prefer it for JWT
    @field_validator("JWT_SECRET", mode="before")
    @classmethod
    def prefer_secret_key(cls, v):
        return os.environ.get("SECRET_KEY") or v

settings = Settings()

# Ensure directories exist
Path(settings.DATA_DIR).mkdir(parents=True, exist_ok=True)
Path(settings.RESUME_DIR).mkdir(parents=True, exist_ok=True)
