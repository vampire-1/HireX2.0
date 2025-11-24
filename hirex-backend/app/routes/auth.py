# app/routes/auth.py
from __future__ import annotations

from datetime import datetime, timedelta
import secrets, string, uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, EmailStr, constr
from sqlmodel import Session, select
from passlib.context import CryptContext

from ..db import get_session
from ..models_auth import User, AuthTxn
from ..utils.mailer import send_otp_email
from ..config import settings


router = APIRouter(prefix="/auth", tags=["auth"])

# ---------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

def _hash_password(pw: str) -> str:
    return pwd_ctx.hash(pw)

def _verify_password(pw: str, hashed: str) -> bool:
    try:
        return pwd_ctx.verify(pw, hashed)
    except Exception:
        return False

# ---------------------------------------------------------------------
# OTP / transaction helpers
# ---------------------------------------------------------------------
def _make_otp(n: int = 6) -> str:
    return "".join(secrets.choice(string.digits) for _ in range(n))

def _new_txn(
    session: Session,
    user_id: int,
    *,
    email: str,
    purpose: str,
    ttl_minutes: int = 10,
) -> AuthTxn:
    """Create & persist a new OTP transaction."""
    txn = AuthTxn(
        transaction_id=uuid.uuid4().hex,     # <-- ensure NOT NULL
        user_id=user_id,
        email=email,
        purpose=purpose,
        otp_code=_make_otp(),
        attempts=0,
        expires_at=datetime.utcnow() + timedelta(minutes=ttl_minutes),
        created_at=datetime.utcnow(),
    )
    session.add(txn)
    session.commit()
    session.refresh(txn)
    return txn

# ---------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------
class RegisterIn(BaseModel):
    email: EmailStr
    password: constr(min_length=6)

class LoginIn(BaseModel):
    email: EmailStr
    password: constr(min_length=6)

class VerifyIn(BaseModel):
    transaction_id: str
    code: constr(min_length=6, max_length=6)

class ResendIn(BaseModel):
    transaction_id: str

class TxnOut(BaseModel):
    transaction_id: str

# ---------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------
@router.post("/register", response_model=TxnOut)
def register(payload: RegisterIn, session: Session = Depends(get_session)):

    # Does a user already exist?
    existing = session.exec(select(User).where(User.email == payload.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already in use")

    # Create user
    user = User(email=payload.email, password_hash=_hash_password(payload.password))
    session.add(user)
    try:
        session.commit()
    except Exception as e:
        # Likely read-only DB or other constraint
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    session.refresh(user)

    # New OTP txn
    txn = _new_txn(session, user.id, email=user.email, purpose="signup")

    # Email the OTP in background (only if enabled)
    print(f"[DEBUG] Register: SMTP_ENABLED={settings.SMTP_ENABLED}, Email={user.email}")
    if settings.SMTP_ENABLED:
        print("[DEBUG] Register: Sending OTP email (sync)")
        try:
            send_otp_email(user.email, txn.otp_code)
        except Exception as e:
            print(f"[ERROR] Register: Failed to send email: {e}")
            # We don't raise here to allow the user to be created, but they might need to resend.
    else:
        print("[DEBUG] Register: SMTP disabled, skipping email")

    return TxnOut(transaction_id=txn.transaction_id)




@router.post("/login", response_model=TxnOut)
def login(payload: LoginIn, session: Session = Depends(get_session)):

    user = session.exec(select(User).where(User.email == payload.email)).first()
    if not user or not _verify_password(payload.password, user.password_hash or ""):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    txn = _new_txn(session, user.id, email=user.email, purpose="login")
    txn = _new_txn(session, user.id, email=user.email, purpose="login")
    print(f"[DEBUG] Login: SMTP_ENABLED={settings.SMTP_ENABLED}, Email={user.email}")
    if settings.SMTP_ENABLED:
        print("[DEBUG] Login: Sending OTP email (sync)")
        try:
            send_otp_email(user.email, txn.otp_code)
        except Exception as e:
            print(f"[ERROR] Login: Failed to send email: {e}")
    else:
        print("[DEBUG] Login: SMTP disabled, skipping email")
    return TxnOut(transaction_id=txn.transaction_id)




@router.post("/verify")
def verify(payload: VerifyIn, session: Session = Depends(get_session)):
    txn = session.exec(
        select(AuthTxn).where(AuthTxn.transaction_id == payload.transaction_id)
    ).first()
    if not txn:
        raise HTTPException(status_code=400, detail="Invalid transaction")

    # Expiry check
    if txn.expires_at and datetime.utcnow() > txn.expires_at:
        raise HTTPException(status_code=400, detail="Code expired")

    # Code check
    if txn.otp_code != payload.code:
        txn.attempts = (txn.attempts or 0) + 1
        session.add(txn)
        session.commit()
        raise HTTPException(status_code=400, detail="Incorrect code")

    # Success — in a real app you'd mint a JWT/cookie here.
    # Optionally delete the txn or mark it used:
    # session.delete(txn); session.commit()
    return {"ok": True}

@router.post("/resend")
def resend(payload: ResendIn, session: Session = Depends(get_session)):

    txn = session.exec(
        select(AuthTxn).where(AuthTxn.transaction_id == payload.transaction_id)
    ).first()
    if not txn:
        raise HTTPException(status_code=400, detail="Invalid transaction")

    # Optionally refresh OTP & expiry
    txn.otp_code = _make_otp()
    txn.expires_at = datetime.utcnow() + timedelta(minutes=10)
    txn.attempts = 0
    session.add(txn)
    session.commit()

    print(f"[DEBUG] Resend: SMTP_ENABLED={settings.SMTP_ENABLED}, Email={txn.email}")
    if settings.SMTP_ENABLED:
        print("[DEBUG] Resend: Sending OTP email (sync)")
        try:
            send_otp_email(txn.email, txn.otp_code)
        except Exception as e:
            print(f"[ERROR] Resend: Failed to send email: {e}")
    else:
        print("[DEBUG] Resend: SMTP disabled, skipping email")
    return {"status": "resent"}



