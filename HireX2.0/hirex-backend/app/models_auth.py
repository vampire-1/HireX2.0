# app/models_auth.py
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import EmailStr
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import DateTime, UniqueConstraint


class User(SQLModel, table=True):
    __tablename__ = "user"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: EmailStr = Field(index=True, unique=True)
    password_hash: str

    created_at: datetime = Field(
        sa_column=Column(DateTime(), default=datetime.utcnow)
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow)
    )


class PurposeEnum(str, Enum):
    signup = "signup"
    login = "login"


class AuthTxn(SQLModel, table=True):
    __tablename__ = "authtxn"

    id: Optional[int] = Field(default=None, primary_key=True)

    transaction_id: str = Field(index=True)
    email: EmailStr
    password_hash: Optional[str] = None
    purpose: PurposeEnum  # <-- use Enum, not Literal

    otp_code: str
    attempts: int = 0
    expires_at: datetime

    created_at: datetime = Field(
        sa_column=Column(DateTime(), default=datetime.utcnow)
    )

    __table_args__ = (
        UniqueConstraint("transaction_id", name="uq_authtxn_tid"),
    )
