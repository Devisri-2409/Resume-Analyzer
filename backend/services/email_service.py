import os
import secrets
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta, timezone
from typing import Tuple, Dict, Any, Optional

SMTP_HOST = os.getenv("SMTP_HOST", "").strip()
SMTP_PORT = int(os.getenv("SMTP_PORT", "587").strip() or "587")
SMTP_USER = os.getenv("SMTP_USER", "").strip()
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "").strip()
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "").strip() or SMTP_USER or "noreply@resumeai.com"
SMTP_TLS = os.getenv("SMTP_TLS", "true").lower() in ("true", "1", "yes")

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")


def generate_verification_token() -> Tuple[str, datetime]:
    """
    Generates a cryptographically secure, single-use verification token
    with an expiration timestamp of 24 hours in UTC.
    """
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
    return token, expires_at


def send_verification_email(email: str, token: str, user_name: str = "") -> Dict[str, Any]:
    """
    Sends an email verification link to the user using the configured SMTP provider.
    If SMTP credentials are not configured, runs safely in development mode and logs
    the verification link for testing without throwing an error.
    """
    verify_url = f"{FRONTEND_URL}/verify-email?token={token}"

    # Check if SMTP is configured
    if not SMTP_HOST or not SMTP_USER or not SMTP_PASSWORD:
        # Development fallback mode
        print(f"[EMAIL SERVICE - DEV MODE] Email verification for {email}: {verify_url}")
        return {
            "status": "dev_mode",
            "message": "Verification link generated (development mode).",
            "recipient": email,
        }

    # Production SMTP delivery
    subject = "Verify your email - ResumeAI Career Platform"
    recipient_name = user_name or "ResumeAI Member"

    html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>{subject}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #0b1120; color: #f1f5f9; padding: 24px; margin: 0; }}
    .container {{ max-width: 540px; margin: 0 auto; background: #111c34; border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 32px; }}
    .brand {{ font-size: 20px; font-weight: 700; color: #0f8a5b; margin-bottom: 20px; }}
    h1 {{ font-size: 22px; color: #ffffff; margin-bottom: 12px; }}
    p {{ font-size: 15px; line-height: 1.6; color: #94a3b8; margin-bottom: 24px; }}
    .btn {{ display: inline-block; background-color: #0f8a5b; color: #ffffff; text-decoration: none; font-weight: 600; padding: 12px 28px; border-radius: 6px; font-size: 15px; }}
    .token-box {{ margin-top: 24px; padding: 12px; background: rgba(0,0,0,0.3); border-radius: 6px; font-family: monospace; font-size: 13px; color: #cbd5e1; word-break: break-all; }}
    .footer {{ font-size: 12px; color: #64748b; margin-top: 32px; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 16px; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="brand">ResumeAI Platform</div>
    <h1>Verify your email address</h1>
    <p>Hi {recipient_name},</p>
    <p>Please confirm your email address to secure your account and verify your professional profile.</p>
    <p><a href="{verify_url}" class="btn" target="_blank">Verify Email Address</a></p>
    <p>Or copy and paste this verification URL into your browser:</p>
    <div class="token-box">{verify_url}</div>
    <div class="footer">
      This link expires in 24 hours. If you did not create an account on ResumeAI, please ignore this email.
    </div>
  </div>
</body>
</html>"""

    plain_content = f"""ResumeAI Career Platform
Verify your email address

Hi {recipient_name},

Please confirm your email address by visiting this link:
{verify_url}

This link expires in 24 hours. If you did not request this, please ignore this email.
"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = SMTP_FROM_EMAIL
    msg["To"] = email

    msg.attach(MIMEText(plain_content, "plain"))
    msg.attach(MIMEText(html_content, "html"))

    try:
        if SMTP_PORT == 465:
            server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=15)
        else:
            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15)
            if SMTP_TLS:
                server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_FROM_EMAIL, [email], msg.as_string())
        server.quit()
        return {"status": "sent", "message": "Verification email sent.", "recipient": email}
    except Exception as e:
        # Avoid leaking SMTP passwords in error messages
        sanitized_err = str(e).replace(SMTP_PASSWORD, "******") if SMTP_PASSWORD else str(e)
        raise RuntimeError(f"Email delivery failed: {sanitized_err}")

