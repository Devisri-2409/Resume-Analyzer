import io
import json
import pymupdf
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

print("--- 1. Testing Registration & Login ---")
reg_payload = {
    "full_name": "Aarav Sharma",
    "email": "aarav.sharma.test@example.com",
    "password": "SecurePassword2026!"
}
reg_res = client.post("/api/auth/register", json=reg_payload)
if reg_res.status_code == 409:
    login_res = client.post("/api/auth/login", json={"email": reg_payload["email"], "password": reg_payload["password"]})
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    token = login_res.json()["access_token"]
else:
    assert reg_res.status_code == 201, f"Register failed: {reg_res.text}"
    token = reg_res.json()["access_token"]

headers = {"Authorization": f"Bearer {token}"}
print("Token acquired successfully.")

print("--- 2. Testing Profile Endpoints ---")
prof_res = client.get("/api/profile", headers=headers)
assert prof_res.status_code == 200, f"Get profile failed: {prof_res.text}"
print("Profile GET OK:", prof_res.json()["personal_info"]["full_name"])

update_res = client.put("/api/profile", headers=headers, json={
    "phone": "+91 9988776655",
    "location": "Bengaluru, India",
    "github": "https://github.com/aaravsharma",
    "linkedin": "https://linkedin.com/in/aaravsharma",
    "bio": "Full-stack software developer focusing on Python and cloud architecture."
})
assert update_res.status_code == 200, f"Profile update failed: {update_res.text}"
print("Profile Update OK.")

# Skills
skill_res = client.post("/api/profile/skills", headers=headers, json={"skill_name": "Python"})
assert skill_res.status_code in [200, 201], f"Add skill failed: {skill_res.text}"
skill_res2 = client.post("/api/profile/skills", headers=headers, json={"skill_name": "Docker"})
del_skill = client.delete("/api/profile/skills/Docker", headers=headers)
assert del_skill.status_code == 200, f"Delete skill failed: {del_skill.text}"
print("Profile Skills OK.")

# Education
edu_res = client.post("/api/profile/education", headers=headers, json={
    "degree": "B.Tech",
    "branch": "Information Technology",
    "college": "IIT Delhi",
    "graduation_year": "2025"
})
assert edu_res.status_code == 201
print("Profile Education OK.")

# Projects
proj_res = client.post("/api/profile/projects", headers=headers, json={
    "name": "AI Resume Analyzer",
    "description": "End to end career platform with ATS intelligence.",
    "technologies": "Python, React, FastAPI, Docker",
    "github_url": "https://github.com/aarav/resume-ai"
})
assert proj_res.status_code == 201
print("Profile Project OK.")

# Certifications
cert_res = client.post("/api/profile/certifications", headers=headers, json={
    "name": "AWS Certified Cloud Practitioner",
    "issuing_organization": "Amazon Web Services",
    "issue_date": "2026"
})
assert cert_res.status_code == 201
print("Profile Certification OK.")

print("--- 3. Testing Courses, Lessons & Quizzes ---")
courses_res = client.get("/api/courses", headers=headers)
assert courses_res.status_code == 200
courses = courses_res.json()["courses"]
print(f"Courses count: {len(courses)}")
assert len(courses) >= 10, "Expected at least 10 courses"

c1 = courses[0]
enroll_res = client.post(f"/api/courses/{c1['id']}/enroll", headers=headers)
assert enroll_res.status_code == 200
print(f"Enrolled in course: {c1['title']}")

detail_res = client.get(f"/api/courses/{c1['id']}", headers=headers)
assert detail_res.status_code == 200
detail_data = detail_res.json()
first_lesson = detail_data["modules"][0]["lessons"][0]
print(f"First Lesson: {first_lesson['title']}")

# Fetch lesson
lesson_res = client.get(f"/api/lessons/{first_lesson['id']}", headers=headers)
assert lesson_res.status_code == 200
assert "explanation" in lesson_res.json()

# Complete lesson
comp_res = client.post(f"/api/lessons/{first_lesson['id']}/complete", headers=headers)
assert comp_res.status_code == 200
print(f"Lesson completed! Course progress now: {comp_res.json()['course_progress']}%")

# Quiz
quiz = detail_data["quizzes"][0]
quiz_res = client.get(f"/api/quizzes/{quiz['id']}", headers=headers)
assert quiz_res.status_code == 200
quiz_data = quiz_res.json()
q1 = quiz_data["questions"][0]
# Select first option
submit_res = client.post(f"/api/quizzes/{quiz['id']}/submit", headers=headers, json={
    "answers": {q1["id"]: q1["options"][0]["id"]}
})
assert submit_res.status_code == 200
sub_data = submit_res.json()
print(f"Quiz submitted! Score: {sub_data['score']}/{sub_data['total_questions']}, Percentage: {sub_data['percentage']}%, Passed: {sub_data['passed']}")

print("--- 4. Testing Learning Dashboard & Recommendations ---")
dash_res = client.get("/api/learning/dashboard", headers=headers)
assert dash_res.status_code == 200
print("Dashboard learning progress:", dash_res.json()["overall_progress"])

recs_res = client.get("/api/learning/recommendations", headers=headers)
assert recs_res.status_code == 200
print(f"Recommendations count: {len(recs_res.json()['recommendations'])}")

print("--- 5. Testing Resume Analyzer & PDF Report Generation ---")
doc = pymupdf.open()
page = doc.new_page()
resume_sample = """
Aarav Sharma
Software Engineer
Email: aarav@example.com
Education: Bachelor of Technology in Computer Science, 2025
Experience: Developed backend services using Python, Flask, and SQL. Built REST APIs.
Projects: Web application with Git and GitHub version control.
Skills: Python, Flask, SQL, Git, GitHub, REST API, HTML, CSS.
"""
page.insert_text((50, 72), resume_sample, fontsize=11)
pdf_bytes = doc.tobytes()
doc.close()

target_jd = """
Senior Backend Engineer Requirements:
We are looking for an engineer proficient in Python, SQL, Docker, AWS, and PostgreSQL.
Must have experience deploying containerized microservices and cloud infrastructure.
"""

analyze_res = client.post(
    "/api/resume/analyze",
    headers=headers,
    data={"job_description": target_jd},
    files={"file": ("sample_resume.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
)
assert analyze_res.status_code == 200, f"Resume analysis failed: {analyze_res.text}"
ana_data = analyze_res.json()
print(f"Analysis complete! ATS Score: {ana_data['ats_score']}, Match: {ana_data['job_match']['job_match_percentage']}%, Detected: {ana_data['detected_skills']}, Missing: {ana_data['job_match']['missing_skills']}")
assert "recommended_courses" in ana_data, "Expected course recommendations in analysis result"
print(f"Course recommendations linked to missing skills: {[c['title'] for c in ana_data['recommended_courses']]}")

analysis_id = ana_data["analysis_id"]

# PDF report generation
pdf_res = client.get(f"/api/resume/report/{analysis_id}/pdf", headers=headers)
assert pdf_res.status_code == 200
assert pdf_res.headers["content-type"] == "application/pdf"
assert len(pdf_res.content) > 500
print(f"PDF Report generated successfully! Size: {len(pdf_res.content)} bytes")

# Reports history
history_res = client.get("/api/resume/history", headers=headers)
assert history_res.status_code == 200
assert len(history_res.json()["history"]) > 0
print(f"Resume history count: {len(history_res.json()['history'])}")

print("\n====== ALL 15 VERIFICATION CHECKS PASSED PERFECTLY! ======")

