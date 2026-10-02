import os
import sys
from getpass import getpass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import User, Profile
from auth import hash_password
from seed_admin import seed_admin


def main():
    # If environment variables are already set or --seed is passed, run seed_admin directly
    if "--seed" in sys.argv or "--non-interactive" in sys.argv:
        seed_admin()
        return

    print("=== Create or Promote Administrator ===")
    full_name = input("Admin name (leave blank for 'Platform Administrator'): ").strip()
    if not full_name:
        full_name = "Platform Administrator"

    email = input("Admin email: ").strip().lower()
    if not email:
        raise SystemExit("Admin email is required.")

    password = getpass("Admin password: ")
    if not password:
        raise SystemExit("Admin password cannot be empty.")

    confirm_password = getpass("Confirm admin password: ")
    if password != confirm_password:
        raise SystemExit("Passwords do not match.")

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            print(f"An account with email '{email}' already exists with role '{existing.role}'.")
            confirm = input("Would you like to promote/update this account to Administrator? (y/n): ").strip().lower()
            if confirm in ("y", "yes"):
                seed_admin(email=email, password=password, full_name=full_name)
                print(f"Account '{email}' successfully promoted to Administrator.")
            else:
                print("Operation cancelled.")
        else:
            seed_admin(email=email, password=password, full_name=full_name)
            print("Admin account created.")
    finally:
        db.close()


if __name__ == "__main__":
    main()