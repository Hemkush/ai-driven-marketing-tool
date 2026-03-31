"""
Email sender — supports two modes:
  1. Resend API  (RESEND_API_KEY set)       — recommended, free, zero config
  2. SMTP        (SMTP_HOST + SMTP_USER set) — Gmail/Outlook fallback

Priority: Resend > SMTP > log warning and skip
"""
import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import httpx

logger = logging.getLogger(__name__)

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
SMTP_HOST      = os.getenv("SMTP_HOST", "")
SMTP_PORT      = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER      = os.getenv("SMTP_USER", "")
SMTP_PASSWORD  = os.getenv("SMTP_PASSWORD", "")
FROM_EMAIL     = os.getenv("FROM_EMAIL", SMTP_USER or "noreply@marketpilot.app")
APP_NAME       = os.getenv("APP_NAME", "MarketPilot")
FRONTEND_URL   = os.getenv("FRONTEND_URL", "http://localhost:5173")


def _build_html(verify_url: str) -> str:
    return f"""
    <div style="font-family:sans-serif;max-width:520px;margin:0 auto;padding:32px 24px;">
      <h2 style="color:#c72832;margin-bottom:8px;">{APP_NAME}</h2>
      <h3 style="margin-top:0;">Verify your email address</h3>
      <p>Thanks for signing up! Click the button below to verify your email and activate your account.</p>
      <a href="{verify_url}"
         style="display:inline-block;background:#c72832;color:#fff;padding:12px 28px;
                border-radius:6px;text-decoration:none;font-weight:700;margin:16px 0;">
        Verify Email →
      </a>
      <p style="color:#64748b;font-size:13px;">
        This link expires in <strong>24 hours</strong>.<br>
        If you didn't create an account, you can safely ignore this email.
      </p>
      <hr style="border:none;border-top:1px solid #e2e8f0;margin:24px 0;">
      <p style="color:#94a3b8;font-size:12px;">
        Or copy this link:<br>
        <a href="{verify_url}" style="color:#c72832;">{verify_url}</a>
      </p>
    </div>
    """


def _send_via_resend(to_email: str, subject: str, html: str) -> bool:
    try:
        resp = httpx.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"},
            json={"from": f"{APP_NAME} <{FROM_EMAIL}>", "to": [to_email], "subject": subject, "html": html},
            timeout=10,
        )
        resp.raise_for_status()
        logger.info("Verification email sent via Resend to %s", to_email)
        return True
    except Exception as exc:
        logger.error("Resend failed for %s: %s", to_email, exc)
        return False


def _send_via_smtp(to_email: str, subject: str, html: str) -> bool:
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{APP_NAME} <{FROM_EMAIL}>"
        msg["To"] = to_email
        msg.attach(MIMEText(html, "html"))
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(FROM_EMAIL, to_email, msg.as_string())
        logger.info("Verification email sent via SMTP to %s", to_email)
        return True
    except Exception as exc:
        logger.error("SMTP failed for %s: %s", to_email, exc)
        return False


def send_verification_email(to_email: str, token: str) -> bool:
    """Send a verification link. Returns True on success."""
    verify_url = f"{FRONTEND_URL}/verify-email?token={token}"
    subject = f"Verify your {APP_NAME} account"
    html = _build_html(verify_url)

    if RESEND_API_KEY:
        return _send_via_resend(to_email, subject, html)

    if SMTP_HOST and SMTP_USER and SMTP_PASSWORD:
        return _send_via_smtp(to_email, subject, html)

    # Neither configured — log the link so dev can verify manually
    logger.warning(
        "No email provider configured. Verification link for %s:\n%s\n"
        "Set RESEND_API_KEY (or SMTP_HOST/SMTP_USER/SMTP_PASSWORD) in .env",
        to_email, verify_url,
    )
    return False
