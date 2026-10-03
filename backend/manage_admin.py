#!/usr/bin/env python
"""
Admin Management CLI for ResumeAI Career Platform.

Usage:
  python manage_admin.py create [--email EMAIL] [--password PASSWORD] [--name NAME]
  python manage_admin.py promote --email EMAIL
  python manage_admin.py reset-password --email EMAIL [--password PASSWORD]
  python manage_admin.py list
  python manage_admin.py init-env
"""

import sys
import os
import argparse
import getpass

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from services.admin_service import (
    create_or_update_admin,
    promote_user_to_admin,
    reset_admin_password,
    list_admins,
    init_admin_from_env,
    has_any_admin,
)


def prompt_password(prompt="Enter Admin Password: ", confirm=True) -> str:
    """Prompt for password without echoing to console, with confirmation."""
    while True:
        pwd = getpass.getpass(prompt)
        if len(pwd) < 8:
            print("[ERROR] Password must be at least 8 characters long. Please try again.")
            continue
        if confirm:
            pwd_confirm = getpass.getpass("Confirm Admin Password: ")
            if pwd != pwd_confirm:
                print("[ERROR] Passwords do not match. Please try again.")
                continue
        return pwd


def cmd_create(args):
    db = SessionLocal()
    try:
        email = args.email
        if not email:
            email = input("Enter Admin Email: ").strip()

        password = args.password
        if not password:
            password = prompt_password()

        name = args.name or "Platform Administrator"

        user = create_or_update_admin(db, email=email, password=password, full_name=name)
        print(f"[SUCCESS] Admin account ready: ID={user.id}, Email={user.email}, Role={user.role}")
    except Exception as e:
        print(f"[ERROR] Failed to create admin: {e}")
        sys.exit(1)
    finally:
        db.close()


def cmd_promote(args):
    db = SessionLocal()
    try:
        email = args.email
        if not email:
            email = input("Enter User Email to promote: ").strip()

        user = promote_user_to_admin(db, email=email)
        print(f"[SUCCESS] User promoted to administrator: ID={user.id}, Email={user.email}, Role={user.role}")
    except Exception as e:
        print(f"[ERROR] Failed to promote user: {e}")
        sys.exit(1)
    finally:
        db.close()


def cmd_reset_password(args):
    db = SessionLocal()
    try:
        email = args.email
        if not email:
            email = input("Enter Admin Email: ").strip()

        password = args.password
        if not password:
            password = prompt_password(prompt="Enter New Password: ")

        user = reset_admin_password(db, email=email, new_password=password)
        print(f"[SUCCESS] Password updated for admin: {user.email}")
    except Exception as e:
        print(f"[ERROR] Failed to reset password: {e}")
        sys.exit(1)
    finally:
        db.close()


def cmd_list(args):
    db = SessionLocal()
    try:
        admins = list_admins(db)
        if not admins:
            print("[INFO] No administrator accounts found in database.")
            return

        print("\n" + "=" * 75)
        print(f"{'ID':<6} {'EMAIL':<32} {'NAME':<24} {'ACTIVE':<8}")
        print("=" * 75)
        for a in admins:
            active_str = "Yes" if a["is_active"] else "No"
            print(f"{a['id']:<6} {a['email']:<32} {a['full_name']:<24} {active_str:<8}")
        print("=" * 75 + "\n")
    finally:
        db.close()


def cmd_init_env(args):
    db = SessionLocal()
    try:
        admin = init_admin_from_env(db)
        if admin:
            print(f"[SUCCESS] Admin account verified/created from .env: {admin.email} (Role: {admin.role})")
        else:
            print("[WARNING] ADMIN_EMAIL or ADMIN_PASSWORD not configured (or placeholder) in .env.")
    except Exception as e:
        print(f"[ERROR] Failed to initialize admin from .env: {e}")
        sys.exit(1)
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(
        description="ResumeAI Platform Administrator Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # create
    p_create = subparsers.add_parser("create", help="Create a new admin account or update existing to admin")
    p_create.add_argument("--email", "-e", help="Administrator email address")
    p_create.add_argument("--password", "-p", help="Administrator password (min 8 characters)")
    p_create.add_argument("--name", "-n", default="Platform Administrator", help="Administrator full name")

    # promote
    p_promote = subparsers.add_parser("promote", help="Promote an existing user to administrator")
    p_promote.add_argument("--email", "-e", required=True, help="User email address to promote")

    # reset-password
    p_reset = subparsers.add_parser("reset-password", help="Reset password for an administrator")
    p_reset.add_argument("--email", "-e", required=True, help="Administrator email address")
    p_reset.add_argument("--password", "-p", help="New password (min 8 characters)")

    # list
    subparsers.add_parser("list", help="List all administrator accounts")

    # init-env
    subparsers.add_parser("init-env", help="Initialize/sync administrator account from .env variables")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    commands = {
        "create": cmd_create,
        "promote": cmd_promote,
        "reset-password": cmd_reset_password,
        "list": cmd_list,
        "init-env": cmd_init_env,
    }

    cmd_fn = commands.get(args.command)
    if cmd_fn:
        cmd_fn(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

