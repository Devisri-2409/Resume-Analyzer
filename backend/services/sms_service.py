import os
import secrets
import hashlib
import hmac
import base64
import urllib.request
import urllib.parse
from datetime import datetime, timedelta, timezone
from typing import Tuple, Dict, Any

SMS_PROVIDER = os.getenv("SMS_PROVIDER", "console").lower().strip()
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "").strip()
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "").strip()
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER", "").strip()

OTP_EXPIRY_MINUTES = 10
MAX_VERIFICATION_ATTEMPTS = 5
RESEND_COOLDOWN_SECONDS = 60


def mask_phone_number(phone: str) -> str:
    """Masks phone number for privacy and secure logging (e.g. +1234567890 -> +12****7890)."""
    clean = phone.strip()
    if len(clean) <= 4:
        return "****"
    return clean[:3] + "*" * (len(clean) - 6) + clean[-3:]


def generate_otp() -> str:
    """Generates a secure 6-digit numeric OTP."""
    return f"{secrets.randbelow(900000) + 100000}"


def hash_otp(user_id: int, otp: str, secret_key: str) -> str:
    """Computes a secure HMAC-SHA256 hash of user_id + otp to store in the database."""
    salt = f"{user_id}:{otp}"
    return hmac.new(secret_key.encode("utf-8"), salt.encode("utf-8"), hashlib.sha256).hexdigest()


def verify_otp_hash(user_id: int, submitted_otp: str, stored_hash: str, secret_key: str) -> bool:
    """Verifies submitted OTP against stored hash using constant-time comparison."""
    if not stored_hash or not submitted_otp:
        return False
    computed = hash_otp(user_id, submitted_otp.strip(), secret_key)
    return hmac.compare_digest(computed, stored_hash)


def send_sms_otp(phone_number: str, otp: str) -> Dict[str, Any]:
    """
    Sends an SMS OTP using Twilio if configured, or logs in development console mode.
    Never exposes provider credentials in error messages or logs.
    """
    masked = mask_phone_number(phone_number)
    message_body = f"Your ResumeAI verification code is: {otp}. Valid for {OTP_EXPIRY_MINUTES} minutes. Do not share this code."

    # If Twilio credentials are configured and SMS_PROVIDER is 'twilio'
    if SMS_PROVIDER == "twilio" and TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_FROM_NUMBER:
        url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"
        data = urllib.parse.urlencode({
            "To": phone_number,
            "From": TWILIO_FROM_NUMBER,
            "Body": message_body,
        }).encode("utf-8")

        auth_str = f"{TWILIO_ACCOUNT_SID}:{TWILIO_AUTH_TOKEN}"
        auth_bytes = base64.b64encode(auth_str.encode("utf-8")).decode("ascii")

        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Authorization": f"Basic {auth_bytes}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status in (200, 201):
                    return {
                        "status": "sent",
                        "provider": "twilio",
                        "recipient": masked,
                    }
                raise RuntimeError(f"Twilio returned status {resp.status}")
        except Exception as e:
            # Mask auth token and credentials
            sanitized = str(e).replace(TWILIO_AUTH_TOKEN, "******").replace(TWILIO_ACCOUNT_SID, "******")
            raise RuntimeError(f"SMS delivery failed: {sanitized}")

    # Fallback to dev mode if provider credentials are not configured
    print(f"[SMS SERVICE - DEV MODE] Verification OTP for {masked}: {otp}")
    return {
        "status": "dev_mode",
        "provider": "console",
        "message": f"Verification code generated (development mode). Code sent to {masked}",
        "recipient": masked,
    }

