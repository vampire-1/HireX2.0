# app/services/auth.py
import os
import secrets
from datetime import datetime, timedelta
from typing import Optional

from jose import jwt
from passlib.context import CryptContext
from sqlmodel import Session, select

from ..config import settings
from ..db import engine
from ..models_auth import User, AuthTxn

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

JWT_SECRET = getattr(settings, "JWT_SECRET", None) or os.environ.get("JWT_SECRET", "dev-secret-change-me")
JWT_ALG = "HS256"
JWT_TTL_MIN = int(os.environ.get("JWT_TTL_MIN", "1440"))  # 24h

def hash_pwd(p: str) -> str:
    return pwd_ctx.hash(p)

def verify_pwd(p: str, h: str) -> bool:
    return pwd_ctx.verify(p, h)

def gen_otp() -> str:
    # 6-digit numeric
    return f"{secrets.randbelow(1_000_000):06d}"

def gen_txn_id() -> str:
    return secrets.token_urlsafe(24)

def send_otp(email: str, code: str, purpose: str):
    # Replace with SMTP/Ses/etc. For now log to console.
    print(f"[OTP] ({purpose}) to {email}: {code}")

def create_jwt(user: User) -> str:
    now = datetime.utcnow()
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=JWT_TTL_MIN)).timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)

def set_session_cookie(response, token: str):
    # httpOnly cookie for browser auth
    response.set_cookie(
        key="hirex_session",
        value=token,
        httponly=True,
        secure=False,        # set True behind HTTPS
        samesite="lax",
        max_age=JWT_TTL_MIN * 60,
        path="/",
    )

def start_signup(email: str, password: str) -> str:
    with Session(engine) as s:
        code = gen_otp()
        txn = AuthTxn(
            transaction_id=gen_txn_id(),
            email=email,
            password_hash=hash_pwd(password),
            purpose="signup",
            otp_code=code,
            expires_at=AuthTxn.expiry(),
        )
        s.add(txn); s.commit()
        send_otp(email, code, "signup")
        return txn.transaction_id

def start_login(email: str, password: str) -> str:
    with Session(engine) as s:
        user = s.exec(select(User).where(User.email == email)).first()
        if not user or not verify_pwd(password, user.password_hash):
            # Do not reveal which part failed
            raise ValueError("Invalid credentials")
        code = gen_otp()
        txn = AuthTxn(
            transaction_id=gen_txn_id(),
            email=email,
            purpose="login",
            otp_code=code,
            expires_at=AuthTxn.expiry(),
        )
        s.add(txn); s.commit()
        send_otp(email, code, "login")
        return txn.transaction_id

def verify_otp_and_issue_session(transaction_id: str, code: str) -> Optional[User]:
    with Session(engine) as s:
        txn = s.exec(select(AuthTxn).where(AuthTxn.transaction_id == transaction_id)).first()
        if not txn:
            raise ValueError("Transaction not found")
        if txn.expires_at < datetime.utcnow():
            raise ValueError("Code expired")
        if txn.attempts >= 5:
            raise ValueError("Too many attempts")
        # bump attempts
        txn.attempts += 1
        s.add(txn); s.commit(); s.refresh(txn)

        if txn.otp_code != code:
            raise ValueError("Invalid code")

        # success: complete flow
        user = s.exec(select(User).where(User.email == txn.email)).first()
        if txn.purpose == "signup":
            if user is None:
                user = User(email=txn.email, password_hash=txn.password_hash or "")
                s.add(user); s.commit(); s.refresh(user)
        else:
            if user is None:
                raise ValueError("Invalid credentials")  # should not happen

        # cleanup txn
        s.delete(txn); s.commit()
        return user

def resend_otp(transaction_id: str):
    with Session(engine) as s:
        txn = s.exec(select(AuthTxn).where(AuthTxn.transaction_id == transaction_id)).first()
        if not txn:
            raise ValueError("Transaction not found")
        if txn.expires_at < datetime.utcnow():
            # regenerate new code + extend expiry
            txn.otp_code = gen_otp()
            txn.expires_at = AuthTxn.expiry()
        else:
            # refresh code anyway
            txn.otp_code = gen_otp()
        s.add(txn); s.commit()
        send_otp(txn.email, txn.otp_code, txn.purpose)
