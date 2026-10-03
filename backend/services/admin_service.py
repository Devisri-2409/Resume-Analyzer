import os
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from auth import hash_password, verify_password
from models import User, Profile


def has_any_admin(db: Session) -> bool:
    """Checks if there is at least one active administrator in the database."""
    return (
        db.query(User)
        .filter(User.role == "admin", User.is_active.is_(True))
        .count()
        > 0
    )


def list_admins(db: Session) -> List[Dict[str, Any]]:
    """Returns a list of all active administrator accounts."""
    admins = (
        db.query(User)
        .filter(User.role == "admin")
        .order_by(User.id.asc())
        .all()
    )
    return [
        {
            "id": u.id,
            "email": u.email,
            "full_name": u.full_name,
            "is_active": u.is_active,
            "is_email_verified": u.is_email_verified,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in admins
    ]


def create_or_update_admin(
    db: Session,
    email: str,
    password: str,
    full_name: str = "Platform Administrator",
) -> User:
    """
    Creates a new administrator account, or updates an existing account to admin role.
    Securely hashes the password with Argon2 and initializes an empty profile if needed.
    """
    clean_email = email.lower().strip()
    if not clean_email or "@" not in clean_email:
        raise ValueError("A valid email address is required.")

    if not password or len(password) < 8:
        raise ValueError("Password must be at least 8 characters long.")

    clean_name = full_name.strip() if full_name else "Platform Administrator"

    user = db.query(User).filter(User.email == clean_email).first()

    if user:
        user.role = "admin"
        user.password_hash = hash_password(password)
        user.is_active = True
        user.is_email_verified = True
        if clean_name:
            user.full_name = clean_name
    else:
        user = User(
            full_name=clean_name,
            email=clean_email,
            password_hash=hash_password(password),
            role="admin",
            is_active=True,
            is_email_verified=True,
            is_phone_verified=False,
        )
        db.add(user)
        db.flush()

        # Initialize profile if not present
        if not user.profile:
            profile = Profile(user_id=user.id)
            db.add(profile)

    db.commit()
    db.refresh(user)
    return user


def promote_user_to_admin(db: Session, email: str) -> User:
    """
    Promotes an existing registered user to role='admin'.
    """
    clean_email = email.lower().strip()
    user = db.query(User).filter(User.email == clean_email).first()
    if not user:
        raise ValueError(f"User with email '{clean_email}' not found.")

    user.role = "admin"
    user.is_active = True
    db.commit()
    db.refresh(user)
    return user


def reset_admin_password(db: Session, email: str, new_password: str) -> User:
    """
    Resets the password of an administrator account.
    """
    clean_email = email.lower().strip()
    if not new_password or len(new_password) < 8:
        raise ValueError("New password must be at least 8 characters long.")

    user = db.query(User).filter(User.email == clean_email).first()
    if not user:
        raise ValueError(f"User with email '{clean_email}' not found.")

    if user.role != "admin":
        raise ValueError(f"User '{clean_email}' is not an administrator.")

    user.password_hash = hash_password(new_password)
    user.is_active = True
    db.commit()
    db.refresh(user)
    return user


def init_admin_from_env(db: Session) -> Optional[User]:
    """
    Initializes or syncs the administrator account defined in environment variables
    (ADMIN_EMAIL, ADMIN_PASSWORD, ADMIN_NAME) on startup.
    Ignores placeholders like 'your_admin_password_here'.
    """
    admin_email = os.getenv("ADMIN_EMAIL", "").strip()
    admin_password = os.getenv("ADMIN_PASSWORD", "").strip()
    admin_name = os.getenv("ADMIN_NAME", "Platform Administrator").strip()

    if not admin_email or not admin_password:
        return None

    # Don't seed dummy template placeholders
    placeholders = ("your_admin_password_here", "changeme", "password", "")
    if admin_password.lower() in placeholders:
        return None

    # Check if an admin with this email already exists and password matches
    existing = db.query(User).filter(User.email == admin_email.lower()).first()
    if existing:
        if existing.role != "admin":
            existing.role = "admin"
            db.commit()
            db.refresh(existing)
        return existing

    # Create admin if it does not exist
    return create_or_update_admin(
        db=db,
        email=admin_email,
        password=admin_password,
        full_name=admin_name,
    )

