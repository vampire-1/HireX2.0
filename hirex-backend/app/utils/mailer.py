# app/utils/mailer.py
from dotenv import load_dotenv
load_dotenv()

import os
import re
import smtplib
import ssl
from email.message import EmailMessage
from typing import Optional



def _env(name: str, default: str = "") -> str:
    # Trim to avoid invisible spaces/newlines from .env/panels
    return (os.getenv(name, default) or "").strip()

SMTP_HOST = _env("SMTP_HOST", "smtp-relay.brevo.com")
SMTP_PORT = int(_env("SMTP_PORT", "587"))     # 587 (STARTTLS) or 465 (SSL)
SMTP_USER = _env("SMTP_USER")                 # Brevo account email (username)
SMTP_PASS = _env("SMTP_PASS")                 # Brevo SMTP key (NOT API key)
FROM_NAME = _env("SMTP_FROM_NAME", "HireX")
FROM_EMAIL = _env("SMTP_FROM_EMAIL", SMTP_USER or "no-reply@hirex.dev")
FROM_ADDR = f"{FROM_NAME} <{FROM_EMAIL}>"

MAIL_DEBUG = _env("MAIL_DEBUG", "false").lower() == "true"

def _send_email(to: str, subject: str, html: Optional[str] = None, text: Optional[str] = None):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = FROM_ADDR
    msg["To"] = to

    if not text and html:
        text = re.sub(r"<[^>]+>", "", html or "").strip()

    # 1) text first
    msg.set_content(text or " ")

    # 2) html alternative
    if html:
        msg.add_alternative(html, subtype="html")

    if MAIL_DEBUG:
        # Hide most of the password; show part of username to ensure it's what you expect
        print(f"[MAIL_DEBUG] SMTP_HOST={SMTP_HOST} PORT={SMTP_PORT} USER={SMTP_USER[:3]}***@*** PASS=***")
        print(f"[MAIL_DEBUG] FROM={FROM_ADDR} TO={to} SUBJECT={subject}")

    if SMTP_PORT == 465:
        # SSL
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as s:
            code, hello = s.ehlo()
            if MAIL_DEBUG: print("[MAIL_DEBUG] EHLO(SSL):", code, hello)
            s.login(SMTP_USER, SMTP_PASS)
            s.send_message(msg)
    else:
        # STARTTLS (recommended for Brevo on 587)
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
            code, hello = s.ehlo()
            if MAIL_DEBUG: print("[MAIL_DEBUG] EHLO(plain):", code, hello)
            s.starttls(context=ssl.create_default_context())
            code, hello = s.ehlo()
            if MAIL_DEBUG: print("[MAIL_DEBUG] EHLO(TLS):", code, hello)
            s.login(SMTP_USER, SMTP_PASS)
            s.send_message(msg)

def send_otp_email(to: str, code: str):
    subject = "Your HireX verification code"
    html = f"""
    <html>
      <body style="font-family:Arial,sans-serif; line-height:1.6; color:#111">
        <p>Hi,</p>
        <p>Your HireX verification code is:</p>
        <h2 style="letter-spacing:4px; margin:8px 0;">{code}</h2>
        <p>This code will expire in 10 minutes.</p>
      </body>
    </html>
    """
    text = f"Your HireX code is: {code}\nThis code will expire in 10 minutes."
    _send_email(to, subject, html=html, text=text)
