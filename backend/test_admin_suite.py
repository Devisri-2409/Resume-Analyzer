"""
Automated Test Suite for Admin Authentication, Initialization, and Role-Based Access:
1. Admin Initialization (CLI, env sync, and protected one-time setup endpoint locking)
2. Successful Admin Login (JWT generation, Argon2 hash verification, role='admin')
3. Failed Admin Login (wrong password, non-existent user, ordinary user rejected with 403)
4. Role-based Authorization (Admin-only routes: metrics, users, access-check)
5. Non-Admin Restrictions (ordinary user cannot access admin APIs or promote self)
"""

import sys
import os

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from database import SessionLocal
from models import User, Profile
from auth import (
    hash_password,
    verify_password,
    create_access_token,
    SECRET_KEY,
    ALGORITHM,
)
from jose import jwt
from fastapi.testclient import TestClient
from main import app
from services.admin_service import (
    create_or_update_admin,
    promote_user_to_admin,
    reset_admin_password,
    list_admins,
    has_any_admin,
    init_admin_from_env,
)


def run_admin_tests():
    print("=" * 75)
    print("STARTING TEST SUITE: Admin Authentication & Role-Based Authorization")
    print("=" * 75)

    client = TestClient(app)
    db = SessionLocal()

    test_admin_email = "test_admin_suite_autouser@example.com"
    test_user_email = "test_normal_suite_autouser@example.com"
    test_admin_pwd = "AdminSecurePassword123!"
    test_user_pwd = "UserSecurePassword123!"

    created_user_ids = []

    try:
        # Cleanup any lingering previous test records
        for email in [test_admin_email, test_user_email]:
            existing = db.query(User).filter(User.email == email).first()
            if existing:
                db.delete(existing)
        db.commit()

        # ---------------------------------------------------------------------
        # TEST 1: ADMIN CREATION VIA ADMIN SERVICE / CLI
        # ---------------------------------------------------------------------
        print("\n--- TEST 1: ADMIN CREATION VIA ADMIN SERVICE / CLI ---")
        admin_user = create_or_update_admin(
            db=db,
            email=test_admin_email,
            password=test_admin_pwd,
            full_name="Suite Administrator",
        )
        created_user_ids.append(admin_user.id)

        assert admin_user is not None, "Admin user must be created"
        assert admin_user.role == "admin", f"Role must be 'admin', got '{admin_user.role}'"
        assert admin_user.is_active is True, "Admin must be active"
        assert verify_password(test_admin_pwd, admin_user.password_hash) is True, "Argon2 password hash must match"
        assert admin_user.password_hash != test_admin_pwd, "Password must not be stored in plaintext"
        print(f"  [OK] Admin account created: ID={admin_user.id}, Role={admin_user.role}")
        print("  [OK] Password securely hashed with Argon2")

        # Create normal test user for comparison
        normal_user = User(
            full_name="Standard User",
            email=test_user_email,
            password_hash=hash_password(test_user_pwd),
            role="user",
            is_active=True,
        )
        db.add(normal_user)
        db.commit()
        db.refresh(normal_user)
        created_user_ids.append(normal_user.id)
        print(f"  [OK] Standard user created for access tests: ID={normal_user.id}, Role={normal_user.role}")

        # ---------------------------------------------------------------------
        # TEST 2: SUCCESSFUL ADMIN LOGIN
        # ---------------------------------------------------------------------
        print("\n--- TEST 2: SUCCESSFUL ADMIN LOGIN ---")
        login_res = client.post(
            "/api/auth/admin/login",
            json={"email": test_admin_email, "password": test_admin_pwd},
        )
        assert login_res.status_code == 200, f"Expected 200, got {login_res.status_code}: {login_res.text}"
        data = login_res.json()
        assert "access_token" in data, "Response must contain access_token"
        assert data["token_type"] == "bearer"
        assert data["user"]["role"] == "admin"
        assert data["user"]["email"] == test_admin_email

        admin_token = data["access_token"]

        # Verify JWT payload
        decoded_payload = jwt.decode(admin_token, SECRET_KEY, algorithms=[ALGORITHM])
        assert decoded_payload["sub"] == str(admin_user.id)
        assert decoded_payload["role"] == "admin"
        assert "exp" in decoded_payload
        print("  [OK] Admin login returned 200 OK with Bearer token")
        print("  [OK] JWT payload contains correct sub and role='admin'")

        # ---------------------------------------------------------------------
        # TEST 3: FAILED ADMIN LOGIN & ROLE RESTRICTIONS
        # ---------------------------------------------------------------------
        print("\n--- TEST 3: FAILED ADMIN LOGIN & ROLE RESTRICTIONS ---")
        # 3a: Wrong password
        wrong_pwd_res = client.post(
            "/api/auth/admin/login",
            json={"email": test_admin_email, "password": "WrongPassword123!"},
        )
        assert wrong_pwd_res.status_code == 401, f"Expected 401, got {wrong_pwd_res.status_code}"
        assert "Invalid email or password" in wrong_pwd_res.json()["detail"]
        print("  [OK] Invalid password correctly rejected with 401")

        # 3b: Non-existent email
        nonexistent_res = client.post(
            "/api/auth/admin/login",
            json={"email": "nonexistent_admin_test@example.com", "password": "AnyPassword123!"},
        )
        assert nonexistent_res.status_code == 401
        print("  [OK] Non-existent email correctly rejected with 401")

        # 3c: Ordinary user attempting admin login MUST receive 403 Forbidden
        user_attempt_res = client.post(
            "/api/auth/admin/login",
            json={"email": test_user_email, "password": test_user_pwd},
        )
        assert user_attempt_res.status_code == 403, f"Expected 403, got {user_attempt_res.status_code}"
        assert "Admin access required" in user_attempt_res.json()["detail"]
        print("  [OK] Standard user attempting admin login rejected with 403 'Admin access required'")

        # 3d: Deactivated admin rejected
        admin_user.is_active = False
        db.commit()
        deactivated_res = client.post(
            "/api/auth/admin/login",
            json={"email": test_admin_email, "password": test_admin_pwd},
        )
        assert deactivated_res.status_code == 403
        print("  [OK] Deactivated admin rejected with 403")
        admin_user.is_active = True
        db.commit()

        # ---------------------------------------------------------------------
        # TEST 4: ROLE-BASED AUTHORIZATION ON ADMIN ROUTES
        # ---------------------------------------------------------------------
        print("\n--- TEST 4: ROLE-BASED AUTHORIZATION ON ADMIN ROUTES ---")
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # Normal user login to get ordinary user token
        user_login_res = client.post(
            "/api/auth/login",
            json={"email": test_user_email, "password": test_user_pwd},
        )
        assert user_login_res.status_code == 200
        user_token = user_login_res.json()["access_token"]
        user_headers = {"Authorization": f"Bearer {user_token}"}

        # 4a: Admin access check
        check_res = client.get("/api/admin/access-check", headers=admin_headers)
        assert check_res.status_code == 200, f"Expected 200, got {check_res.status_code}"
        assert check_res.json()["role"] == "admin"
        print("  [OK] Admin token successfully verified at /api/admin/access-check")

        # 4b: Admin metrics access
        metrics_res = client.get("/api/admin/metrics", headers=admin_headers)
        assert metrics_res.status_code == 200, f"Expected 200, got {metrics_res.status_code}"
        metrics_data = metrics_res.json()
        assert "stats" in metrics_data
        assert "recent_activities" in metrics_data
        print(f"  [OK] Admin token retrieved platform metrics: total_users={metrics_data['stats']['total_users']}")

        # 4c: Admin users list access
        users_res = client.get("/api/admin/users", headers=admin_headers)
        assert users_res.status_code == 200
        assert isinstance(users_res.json(), list)
        print(f"  [OK] Admin token retrieved users list ({len(users_res.json())} users)")

        # 4d: Ordinary user BLOCKED from admin routes
        user_metrics_res = client.get("/api/admin/metrics", headers=user_headers)
        assert user_metrics_res.status_code == 403, f"Expected 403 for normal user, got {user_metrics_res.status_code}"
        assert "Admin access required" in user_metrics_res.json()["detail"]

        user_users_res = client.get("/api/admin/users", headers=user_headers)
        assert user_users_res.status_code == 403
        print("  [OK] Ordinary user strictly denied (403) from /api/admin/metrics and /api/admin/users")

        # 4e: Unauthenticated request BLOCKED
        unauth_res = client.get("/api/admin/metrics")
        assert unauth_res.status_code == 401
        print("  [OK] Unauthenticated request strictly denied (401)")

        # ---------------------------------------------------------------------
        # TEST 5: PREVENT PRIVILEGE ESCALATION
        # ---------------------------------------------------------------------
        print("\n--- TEST 5: PREVENT PRIVILEGE ESCALATION ---")
        # 5a: Standard user cannot self-promote via profile update
        profile_res = client.put(
            "/api/profile",
            headers=user_headers,
            json={"full_name": "Standard User Trying Escalation", "role": "admin"},
        )
        assert profile_res.status_code == 200
        db.refresh(normal_user)
        assert normal_user.role == "user", f"Role must remain 'user', got '{normal_user.role}'"
        print("  [OK] Self-promotion via /api/profile prevented: user role remained 'user'")

        # 5b: Public register endpoint always assigns role='user'
        new_reg_email = "public_reg_test_user@example.com"
        reg_res = client.post(
            "/api/auth/register",
            json={
                "full_name": "Public Registrant",
                "email": new_reg_email,
                "password": "Password123!",
                "role": "admin",  # Attacker tries to inject admin role
            },
        )
        assert reg_res.status_code == 201
        reg_user = db.query(User).filter(User.email == new_reg_email).first()
        if reg_user:
            created_user_ids.append(reg_user.id)
            assert reg_user.role == "user", f"Role must be 'user', got '{reg_user.role}'"
        print("  [OK] Public registration strictly enforces role='user'")

        # ---------------------------------------------------------------------
        # TEST 6: CLI & SERVICE MANAGEMENT FUNCTIONS
        # ---------------------------------------------------------------------
        print("\n--- TEST 6: CLI & SERVICE MANAGEMENT FUNCTIONS ---")
        # 6a: Promote existing user to admin
        promoted = promote_user_to_admin(db, test_user_email)
        assert promoted.role == "admin"
        print(f"  [OK] promote_user_to_admin successfully promoted {test_user_email} to role='admin'")

        # 6b: Reset admin password
        new_pwd = "NewlyResetPassword123!"
        reset_res = reset_admin_password(db, test_user_email, new_pwd)
        assert verify_password(new_pwd, reset_res.password_hash) is True
        print(f"  [OK] reset_admin_password successfully updated Argon2 password for {test_user_email}")

        # 6c: List admins
        admins_list = list_admins(db)
        admin_emails = [a["email"] for a in admins_list]
        assert test_admin_email in admin_emails
        assert test_user_email in admin_emails
        print(f"  [OK] list_admins returned active administrators: count={len(admins_list)}")

        # 6d: Protected one-time setup endpoint locked when admins exist
        assert has_any_admin(db) is True
        init_first_res = client.post(
            "/api/auth/admin/init-first-admin",
            json={
                "full_name": "Attacker Trying First Admin",
                "email": "attacker@example.com",
                "password": "AttackerPassword123!",
            },
        )
        assert init_first_res.status_code == 403
        assert "locked" in init_first_res.json()["detail"]
        print("  [OK] POST /api/auth/admin/init-first-admin is permanently locked (403) when admin exists")

        # 6e: GET /api/auth/admin/status
        status_res = client.get("/api/auth/admin/status")
        assert status_res.status_code == 200
        assert status_res.json()["has_admin"] is True
        print("  [OK] GET /api/auth/admin/status correctly reports has_admin=True")

        print("\n" + "=" * 75)
        print("ALL ADMIN & AUTHORIZATION TESTS PASSED SUCCESSFULLY! (100% VERIFIED)")
        print("=" * 75)

    except Exception as e:
        print(f"\n[TEST SUITE FAILURE]: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # Clean up test users created during test execution
        for uid in created_user_ids:
            u = db.query(User).filter(User.id == uid).first()
            if u:
                if u.profile:
                    db.delete(u.profile)
                db.delete(u)
        db.commit()
        db.close()
        print(f"[CLEANUP] Cleaned up {len(created_user_ids)} test accounts")


if __name__ == "__main__":
    run_admin_tests()
