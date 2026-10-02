import os
import sys
from dotenv import load_dotenv

# Ensure backend directory is on the module search path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import User, Profile
from auth import hash_password

load_dotenv()

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@resumeai.com").strip().lower()
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "AdminSecurePass2026!")
ADMIN_NAME = os.getenv("ADMIN_NAME", "Platform Administrator").strip()


def seed_admin(email: str = None, password: str = None, full_name: str = None) -> dict:
    """
    Idempotent admin seed script.
    - Creates initial administrator if one does not exist.
    - If user exists with role != 'admin', safely promotes to 'admin' (Requirement 12).
    - If user exists with role == 'admin', updates password hash and ensures account is active.
    - Never stores plaintext passwords; hashes with Argon2.
    - Never creates duplicate administrator accounts with the same email.
    """
    target_email = (email or ADMIN_EMAIL).strip().lower()
    target_password = password or ADMIN_PASSWORD
    target_name = (full_name or ADMIN_NAME).strip()

    if not target_email:
        raise ValueError("ADMIN_EMAIL is required.")
    if not target_password:
        raise ValueError("ADMIN_PASSWORD is required.")
    if not target_name:
        target_name = "Platform Administrator"

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == target_email).first()
        hashed = hash_password(target_password)

        if user:
            promoted = user.role != "admin"
            user.role = "admin"
            user.is_active = True
            user.password_hash = hashed
            if target_name and user.full_name != target_name:
                user.full_name = target_name

            # Ensure user profile exists
            if not user.profile:
                profile = Profile(
                    user_id=user.id,
                    avatar="avatar-1",
                    location="Headquarters",
                    bio="Platform Administrator",
                )
                db.add(profile)

            db.commit()
            db.refresh(user)

            action = "promoted and updated" if promoted else "verified and updated"
            print(f"[SUCCESS] Admin account '{target_email}' {action} successfully (ID: {user.id}, role: {user.role}).")
            return {
                "status": "updated",
                "email": user.email,
                "role": user.role,
                "user_id": user.id,
                "promoted": promoted,
            }
        else:
            new_admin = User(
                full_name=target_name,
                email=target_email,
                password_hash=hashed,
                role="admin",
                is_active=True,
            )
            db.add(new_admin)
            db.commit()
            db.refresh(new_admin)

            # Create profile for new admin
            profile = Profile(
                user_id=new_admin.id,
                avatar="avatar-1",
                location="Headquarters",
                bio="Platform Administrator",
            )
            db.add(profile)
            db.commit()

            print(f"[SUCCESS] Initial admin account '{target_email}' created successfully (ID: {new_admin.id}, role: {new_admin.role}).")
            return {
                "status": "created",
                "email": new_admin.email,
                "role": new_admin.role,
                "user_id": new_admin.id,
                "promoted": False,
            }
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Failed to seed admin account: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_admin()
