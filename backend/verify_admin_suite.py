"""
Comprehensive verification test script for Admin Authentication & Role-Based Access Control.
Covers Requirements A through K and Requirement 12.
"""

import sys
import uuid
import requests

BASE_URL = "http://127.0.0.1:8000"

ADMIN_EMAIL = "admin@resumeai.com"
ADMIN_PASSWORD = "AdminSecurePass2026!"

passed_tests = []
failed_tests = []


def assert_test(name: str, condition: bool, details: str = ""):
    if condition:
        print(f"[PASS] {name}")
        passed_tests.append(name)
    else:
        print(f"[FAIL] {name} - Details: {details}")
        failed_tests.append((name, details))


def main():
    print("=" * 60)
    print("AI RESUME ANALYZER - ADMIN AUTH & RBAC VERIFICATION SUITE")
    print("=" * 60)

    # 1. Unauthenticated checks
    print("\n--- 1. Testing Unauthenticated Access ---")
    r = requests.get(f"{BASE_URL}/api/admin/access-check")
    assert_test(
        "Unauthenticated /api/admin/access-check returns 401",
        r.status_code == 401 and "Authentication required" in r.text,
        f"status: {r.status_code}, body: {r.text}",
    )

    r = requests.get(f"{BASE_URL}/api/admin/metrics")
    assert_test(
        "Unauthenticated /api/admin/metrics returns 401",
        r.status_code == 401 and "Authentication required" in r.text,
        f"status: {r.status_code}, body: {r.text}",
    )

    # 2. Invalid credentials check
    print("\n--- 2. Testing Invalid Credentials ---")
    r = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "nonexistent_user_999@example.com", "password": "wrongpassword123"},
    )
    assert_test(
        "Invalid login returns 401",
        r.status_code == 401 and "Invalid email or password" in r.text,
        f"status: {r.status_code}, body: {r.text}",
    )

    r = requests.post(
        f"{BASE_URL}/api/auth/admin/login",
        json={"email": ADMIN_EMAIL, "password": "completelywrongpassword!"},
    )
    assert_test(
        "Invalid admin password returns 401",
        r.status_code == 401 and "Invalid email or password" in r.text,
        f"status: {r.status_code}, body: {r.text}",
    )

    # 3. Test A: Create normal user through /api/auth/register
    print("\n--- 3. Testing Normal User Registration (Test A) ---")
    random_suffix = uuid.uuid4().hex[:6]
    test_user_email = f"testuser_{random_suffix}@example.com"
    test_user_password = "UserPassword123!"
    test_user_name = f"Test User {random_suffix}"

    r = requests.post(
        f"{BASE_URL}/api/auth/register",
        json={
            "full_name": test_user_name,
            "email": test_user_email,
            "password": test_user_password,
        },
    )
    assert_test(
        "Test A: Normal user registration succeeds (201 Created)",
        r.status_code == 201,
        f"status: {r.status_code}, body: {r.text}",
    )
    user_reg_data = r.json()
    assert_test(
        "Normal registration assigns role='user'",
        user_reg_data.get("user", {}).get("role") == "user",
        f"role returned: {user_reg_data.get('user', {}).get('role')}",
    )

    # 4. Test B: Normal user login succeeds
    print("\n--- 4. Testing Normal User Login (Test B) ---")
    r = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": test_user_email, "password": test_user_password},
    )
    assert_test(
        "Test B: Normal user login succeeds (200 OK)",
        r.status_code == 200 and "access_token" in r.json(),
        f"status: {r.status_code}, body: {r.text}",
    )
    normal_token = r.json()["access_token"]
    normal_headers = {"Authorization": f"Bearer {normal_token}"}

    # 5. Test C: Normal user cannot access admin endpoints
    print("\n--- 5. Testing Normal User Admin Access Restriction (Test C) ---")
    r = requests.get(f"{BASE_URL}/api/admin/access-check", headers=normal_headers)
    assert_test(
        "Test C1: Normal user blocked from /api/admin/access-check (403 Forbidden)",
        r.status_code == 403 and "Admin access required" in r.text,
        f"status: {r.status_code}, body: {r.text}",
    )

    r = requests.get(f"{BASE_URL}/api/admin/metrics", headers=normal_headers)
    assert_test(
        "Test C2: Normal user blocked from /api/admin/metrics (403 Forbidden)",
        r.status_code == 403 and "Admin access required" in r.text,
        f"status: {r.status_code}, body: {r.text}",
    )

    r = requests.post(
        f"{BASE_URL}/api/auth/admin/login",
        json={"email": test_user_email, "password": test_user_password},
    )
    assert_test(
        "Test C3: Normal user blocked from /api/auth/admin/login (403 Admin access required)",
        r.status_code == 403 and "Admin access required" in r.text,
        f"status: {r.status_code}, body: {r.text}",
    )

    # 6. Test D: Seed admin account
    print("\n--- 6. Testing Admin Seed Script (Test D) ---")
    from seed_admin import seed_admin

    seed_result = seed_admin(ADMIN_EMAIL, ADMIN_PASSWORD, "Platform Administrator")
    assert_test(
        "Test D: Seed admin runs cleanly without crashing",
        seed_result.get("role") == "admin" and seed_result.get("email") == ADMIN_EMAIL,
        f"seed_result: {seed_result}",
    )

    # 7. Test E: Admin login succeeds (both normal and admin endpoints)
    print("\n--- 7. Testing Admin Login (Test E) ---")
    r_admin_direct = requests.post(
        f"{BASE_URL}/api/auth/admin/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    assert_test(
        "Test E1: Admin login via /api/auth/admin/login succeeds (200 OK)",
        r_admin_direct.status_code == 200 and "access_token" in r_admin_direct.json(),
        f"status: {r_admin_direct.status_code}, body: {r_admin_direct.text}",
    )

    r_admin_general = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    assert_test(
        "Test E2: Admin login via standard /api/auth/login succeeds (200 OK)",
        r_admin_general.status_code == 200 and "access_token" in r_admin_general.json(),
        f"status: {r_admin_general.status_code}, body: {r_admin_general.text}",
    )

    admin_token = r_admin_direct.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 8. Test F: Admin JWT/authentication identifies admin correctly
    print("\n--- 8. Testing Admin Token & Identity Resolution (Test F) ---")
    r_me = requests.get(f"{BASE_URL}/api/auth/me", headers=admin_headers)
    me_data = r_me.json()
    assert_test(
        "Test F: /api/auth/me correctly resolves role='admin'",
        r_me.status_code == 200 and me_data.get("role") == "admin",
        f"status: {r_me.status_code}, me_data: {me_data}",
    )

    # 9. Test G & H: Admin-only API endpoints return 200 for admin
    print("\n--- 9. Testing Admin-Only API Endpoints (Tests G & H) ---")
    r_check = requests.get(f"{BASE_URL}/api/admin/access-check", headers=admin_headers)
    assert_test(
        "Test H1: Admin access check returns 200 and role='admin'",
        r_check.status_code == 200 and r_check.json().get("role") == "admin",
        f"status: {r_check.status_code}, body: {r_check.text}",
    )

    r_metrics = requests.get(f"{BASE_URL}/api/admin/metrics", headers=admin_headers)
    assert_test(
        "Test H2: Admin metrics returns 200 and stats object",
        r_metrics.status_code == 200 and "stats" in r_metrics.json(),
        f"status: {r_metrics.status_code}, body: {r_metrics.text}",
    )

    r_users = requests.get(f"{BASE_URL}/api/admin/users", headers=admin_headers)
    assert_test(
        "Test H3: Admin users list returns 200 and list of accounts",
        r_users.status_code == 200 and isinstance(r_users.json(), list),
        f"status: {r_users.status_code}, count: {len(r_users.json()) if isinstance(r_users.json(), list) else 0}",
    )

    # 10. Test I: Existing user authentication still works
    print("\n--- 10. Testing Existing User Authentication Integrity (Test I) ---")
    r_normal_me = requests.get(f"{BASE_URL}/api/auth/me", headers=normal_headers)
    assert_test(
        "Test I: Standard user /api/auth/me resolves role='user'",
        r_normal_me.status_code == 200 and r_normal_me.json().get("role") == "user",
        f"status: {r_normal_me.status_code}, body: {r_normal_me.text}",
    )

    # 11. Test J: Resume analyzer endpoints still work
    print("\n--- 11. Testing Resume Analyzer Integrity (Test J) ---")
    r_history = requests.get(f"{BASE_URL}/api/resume/history", headers=normal_headers)
    assert_test(
        "Test J1: /api/resume/history returns 200 for user",
        r_history.status_code == 200 and "history" in r_history.json(),
        f"status: {r_history.status_code}, body: {r_history.text}",
    )

    r_latest = requests.get(f"{BASE_URL}/api/resume/latest", headers=normal_headers)
    assert_test(
        "Test J2: /api/resume/latest returns 200 for user",
        r_latest.status_code == 200 and "latest" in r_latest.json(),
        f"status: {r_latest.status_code}, body: {r_latest.text}",
    )

    # 12. Test K: Profile, Courses, Learning, Quizzes functionality still works
    print("\n--- 12. Testing Profile, Courses & Learning Integrity (Test K) ---")
    r_profile = requests.get(f"{BASE_URL}/api/profile", headers=normal_headers)
    assert_test(
        "Test K1: /api/profile returns 200 with personal_info",
        r_profile.status_code == 200 and "personal_info" in r_profile.json(),
        f"status: {r_profile.status_code}",
    )

    r_courses = requests.get(f"{BASE_URL}/api/courses")
    courses_data = r_courses.json()
    course_list = courses_data.get("courses", [])
    assert_test(
        "Test K2: /api/courses returns 200 and >= 10 starter courses",
        r_courses.status_code == 200 and len(course_list) >= 10,
        f"status: {r_courses.status_code}, count: {len(course_list)}",
    )

    r_learning = requests.get(f"{BASE_URL}/api/learning/dashboard", headers=normal_headers)
    learning_data = r_learning.json()
    assert_test(
        "Test K3: /api/learning/dashboard returns 200 with quiz_performance",
        r_learning.status_code == 200 and "quiz_performance" in learning_data,
        f"status: {r_learning.status_code}",
    )

    # 13. Test Requirement 12: Safe migration / promotion of existing normal user to admin
    print("\n--- 13. Testing Requirement 12: Safe Promotion Mechanism ---")
    promo_email = f"user_to_promote_{uuid.uuid4().hex[:6]}@example.com"
    promo_pw = "InitialPass123!"
    requests.post(
        f"{BASE_URL}/api/auth/register",
        json={"full_name": "Future Admin", "email": promo_email, "password": promo_pw},
    )
    # Now run seed_admin on this email with a new admin password
    new_admin_pw = "PromotedAdminSecure2026!"
    promo_result = seed_admin(promo_email, new_admin_pw, "Promoted Admin")
    assert_test(
        "Requirement 12: Existing standard user is safely promoted without duplicate",
        promo_result.get("promoted") is True and promo_result.get("role") == "admin",
        f"promo_result: {promo_result}",
    )

    # Verify logging in with promoted credentials
    r_promo_login = requests.post(
        f"{BASE_URL}/api/auth/admin/login",
        json={"email": promo_email, "password": new_admin_pw},
    )
    assert_test(
        "Requirement 12: Promoted account logs in via /api/auth/admin/login (200 OK)",
        r_promo_login.status_code == 200 and r_promo_login.json()["user"]["role"] == "admin",
        f"status: {r_promo_login.status_code}, body: {r_promo_login.text}",
    )

    print("\n" + "=" * 60)
    print(f"VERIFICATION SUMMARY: {len(passed_tests)} Passed, {len(failed_tests)} Failed")
    print("=" * 60)
    if failed_tests:
        print("\nFailed Tests:")
        for name, details in failed_tests:
            print(f" - {name}: {details}")
        sys.exit(1)
    else:
        print("\nALL VERIFICATION TESTS A THROUGH K PASSED SUCCESSFULLY!")
        sys.exit(0)


if __name__ == "__main__":
    main()
