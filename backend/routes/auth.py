import re
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from auth import create_access_token, get_current_user, hash_password, verify_password, SECRET_KEY
from database import get_db
from models import User, Profile
from schemas import (
    LoginRequest,
    RegisterRequest,
    EmailVerifyRequest,
    PhoneSendOtpRequest,
    PhoneVerifyOtpRequest,
    AdminInitRequest,
)
from services.admin_service import has_any_admin, create_or_update_admin
from services.email_service import generate_verification_token, send_verification_email
from services.sms_service import (
    generate_otp,
    hash_otp,
    verify_otp_hash,
    send_sms_otp,
    mask_phone_number,
    MAX_VERIFICATION_ATTEMPTS,
    OTP_EXPIRY_MINUTES,
    RESEND_COOLDOWN_SECONDS,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


def user_response(user: User) -> dict:
    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "role": user.role,
        "is_email_verified": bool(user.is_email_verified),
        "is_phone_verified": bool(user.is_phone_verified),
        "phone_number": user.phone_number or (user.profile.phone if user.profile else ""),
    }


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    email = payload.email.lower().strip()

    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    user = User(
        full_name=payload.full_name.strip(),
        email=email,
        password_hash=hash_password(payload.password),
        role="user",
        is_email_verified=False,
        is_phone_verified=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Automatically initialize empty profile
    profile = Profile(user_id=user.id)
    db.add(profile)
    db.commit()

    token = create_access_token(user.id, user.role)
    return {"access_token": token, "token_type": "bearer", "user": user_response(user)}


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    email = payload.email.lower().strip()
    user = db.query(User).filter(User.email == email).first()

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Please contact support.",
        )

    token = create_access_token(user.id, user.role)
    return {"access_token": token, "token_type": "bearer", "user": user_response(user)}


@router.post("/admin/login")
def admin_login(payload: LoginRequest, db: Session = Depends(get_db)):
    email = payload.email.lower().strip()
    user = db.query(User).filter(User.email == email).first()

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator account is deactivated.",
        )

    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required. This account does not possess administrator privileges.",
        )

    token = create_access_token(user.id, user.role)
    return {"access_token": token, "token_type": "bearer", "user": user_response(user)}


@router.get("/admin/status")
def get_admin_status(db: Session = Depends(get_db)):
    """
    Returns platform administrator status without exposing sensitive credentials.
    Used by the frontend to advise whether an admin account has been provisioned.
    """
    return {
        "has_admin": has_any_admin(db),
    }


@router.post("/admin/init-first-admin", status_code=status.HTTP_201_CREATED)
def init_first_admin(payload: AdminInitRequest, db: Session = Depends(get_db)):
    """
    Protected one-time setup endpoint to initialize the first platform administrator.
    Permanently locked (returns 403 Forbidden) once ANY active administrator account exists.
    """
    if has_any_admin(db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin initialization is locked: an administrator account already exists. Please use the CLI tool or contact an existing administrator.",
        )

    user = create_or_update_admin(
        db=db,
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
    )
    token = create_access_token(user.id, user.role)
    return {
        "message": "First platform administrator initialized successfully.",
        "access_token": token,
        "token_type": "bearer",
        "user": user_response(user),
    }


@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return user_response(current_user)


# =========================================================================
# Email Verification Flow
# =========================================================================

@router.post("/email/send-verification")
def send_email_verification(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.is_email_verified:
        return {"message": "Email is already verified.", "is_email_verified": True}

    now = datetime.now(timezone.utc)

    # Rate limiting: 60-second cooldown between resends
    if current_user.email_verification_sent_at:
        sent_at = current_user.email_verification_sent_at
        if sent_at.tzinfo is None:
            sent_at = sent_at.replace(tzinfo=timezone.utc)
        elapsed = (now - sent_at).total_seconds()
        if elapsed < 60:
            remaining = int(60 - elapsed)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Please wait {remaining} seconds before requesting another verification email.",
            )

    # Generate single-use, expiring token (24h)
    token, expires_at = generate_verification_token()
    current_user.email_verification_token = token
    current_user.email_verification_expires_at = expires_at
    current_user.email_verification_sent_at = now
    db.commit()

    try:
        send_verification_email(current_user.email, token, user_name=current_user.full_name)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to dispatch verification email. Please try again later.",
        )

    return {
        "message": f"Verification email sent to {current_user.email}.",
        "expires_in_hours": 24,
    }


@router.post("/email/verify")
def verify_email_post(
    payload: EmailVerifyRequest,
    db: Session = Depends(get_db),
):
    token = payload.token.strip()
    user = db.query(User).filter(User.email_verification_token == token).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or already used verification token.",
        )

    now = datetime.now(timezone.utc)
    exp = user.email_verification_expires_at
    if exp:
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if now > exp:
            # Token expired - invalidate it
            user.email_verification_token = None
            user.email_verification_expires_at = None
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification link has expired. Please request a new verification email.",
            )

    # Mark as verified and invalidate token
    user.is_email_verified = True
    user.email_verification_token = None
    user.email_verification_expires_at = None
    db.commit()
    db.refresh(user)

    return {
        "message": "Email address verified successfully!",
        "is_email_verified": True,
        "user": user_response(user),
    }


@router.get("/email/verify")
def verify_email_get(
    token: str = Query(...),
    db: Session = Depends(get_db),
):
    return verify_email_post(EmailVerifyRequest(token=token), db=db)


# =========================================================================
# Phone OTP Verification Flow
# =========================================================================

@router.post("/phone/send-otp")
def send_phone_otp(
    payload: PhoneSendOtpRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    raw_phone = payload.phone_number.strip()
    digits = re.sub(r"[^\d+]", "", raw_phone)
    if len(re.sub(r"\D", "", digits)) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide a valid phone number (at least 8 digits).",
        )

    now = datetime.now(timezone.utc)

    # Rate limiting: 60-second cooldown between OTP requests
    if current_user.phone_otp_sent_at:
        sent_at = current_user.phone_otp_sent_at
        if sent_at.tzinfo is None:
            sent_at = sent_at.replace(tzinfo=timezone.utc)
        elapsed = (now - sent_at).total_seconds()
        if elapsed < RESEND_COOLDOWN_SECONDS:
            remaining = int(RESEND_COOLDOWN_SECONDS - elapsed)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Please wait {remaining} seconds before requesting a new code.",
            )

    # Generate 6-digit numeric OTP and hash it
    otp = generate_otp()
    hashed = hash_otp(current_user.id, otp, SECRET_KEY)
    expires_at = now + timedelta(minutes=OTP_EXPIRY_MINUTES)

    # Save to user, resetting attempt counter and invalidating any prior OTP
    current_user.phone_number = digits
    current_user.phone_otp_hash = hashed
    current_user.phone_otp_expires_at = expires_at
    current_user.phone_otp_sent_at = now
    current_user.phone_otp_attempts = 0
    # Note: user is NEVER marked verified before OTP confirmation
    db.commit()

    try:
        send_sms_otp(digits, otp)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification SMS. Please check the phone number or try again later.",
        )

    return {
        "message": f"Verification code sent to {mask_phone_number(digits)}.",
        "phone_number": digits,
        "expires_in_minutes": OTP_EXPIRY_MINUTES,
    }


@router.post("/phone/verify-otp")
def verify_phone_otp(
    payload: PhoneVerifyOtpRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    submitted_phone = re.sub(r"[^\d+]", "", payload.phone_number.strip())
    submitted_otp = payload.otp.strip()

    if not current_user.phone_otp_hash or not current_user.phone_otp_expires_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No pending verification code found. Please request a new code.",
        )

    # Check attempt limit
    if current_user.phone_otp_attempts >= MAX_VERIFICATION_ATTEMPTS:
        # Invalidate OTP on too many attempts
        current_user.phone_otp_hash = None
        current_user.phone_otp_expires_at = None
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Maximum verification attempts exceeded. Please request a new code.",
        )

    # Check expiration
    now = datetime.now(timezone.utc)
    exp = current_user.phone_otp_expires_at
    if exp:
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if now > exp:
            current_user.phone_otp_hash = None
            current_user.phone_otp_expires_at = None
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification code has expired. Please request a new code.",
            )

    # Verify constant-time
    is_valid = verify_otp_hash(current_user.id, submitted_otp, current_user.phone_otp_hash, SECRET_KEY)

    if not is_valid:
        current_user.phone_otp_attempts += 1
        remaining_attempts = max(0, MAX_VERIFICATION_ATTEMPTS - current_user.phone_otp_attempts)
        db.commit()

        if remaining_attempts == 0:
            current_user.phone_otp_hash = None
            current_user.phone_otp_expires_at = None
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect code. Maximum attempts reached. Please request a new code.",
            )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Incorrect verification code. {remaining_attempts} attempt(s) remaining.",
        )

    # Successful verification
    current_user.is_phone_verified = True
    current_user.phone_number = submitted_phone
    current_user.phone_otp_hash = None
    current_user.phone_otp_expires_at = None
    current_user.phone_otp_attempts = 0

    # Also update profile phone
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if profile:
        profile.phone = submitted_phone
    else:
        profile = Profile(user_id=current_user.id, phone=submitted_phone)
        db.add(profile)

    db.commit()
    db.refresh(current_user)

    return {
        "message": "Phone number verified successfully!",
        "is_phone_verified": True,
        "phone_number": current_user.phone_number,
        "user": user_response(current_user),
    }

