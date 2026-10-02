# AI-Powered Resume Analyzer & Career Learning Platform — Backend

High-performance FastAPI backend service providing RESTful APIs for resume analysis, ATS scoring, skill-gap detection, user profile management, course catalog delivery, lesson progress synchronization, quiz assessments, and executive PDF reporting.

---

## Overview

The backend service coordinates the core intelligence and persistence layers of the career-readiness ecosystem. It unifies resume diagnostics with an active career-learning workflow, mapping detected skill gaps to structured curriculum modules.

```text
User Registration / Login
        ↓
User Profile (Personal info, education, verified skills, projects, certifications)
        ↓
Upload Resume PDF + Target Job Description
        ↓
Resume Text Extraction (pypdf)
        ↓
Technical Skill Extraction & Catalog Matching
        ↓
ATS Compatibility Scoring
        ↓
Job Description Keyword & Requirement Comparison
        ↓
Matched Skills + Missing Skill Gap Detection
        ↓
AI-Powered Resume Feedback & Actionable Recommendations (Gemini API)
        ↓
Skill-Gap-Based Course Recommendations
        ↓
Enroll in Recommended Courses
        ↓
Study Technical Lessons & Code Examples
        ↓
Complete Lessons (Automatic Course Progress Updates)
        ↓
Take Course Quizzes & Validate Knowledge
        ↓
Track Learning Progress, Streaks & Quiz Scores
        ↓
Download Executive Analysis PDF Report & Improve Resume
```

---

## Implemented Backend Capabilities

### Authentication & Authorization
- **User Registration**: `POST /api/auth/register` assigns `role="user"`.
- **User Login**: `POST /api/auth/login` verifies credentials via Argon2 and issues JWT.
- **Admin Login**: `POST /api/auth/admin/login` enforces `role == "admin"`.
- **JWT Authorization**: Bearer token scheme (`HS256`) with automatic expiration.
- **Argon2 Password Hashing**: Cryptographically secure hashing with per-user salting.
- **Server-Side Security**: Protected endpoints enforce `get_current_user` and `require_admin`.
- **Notice on Administrator Registration**:
  > *Public admin registration is not implemented yet. Administrator accounts are currently handled separately and admin account creation will be added in a future version.*

### Resume Analyzer Engine
- **PDF Ingestion**: `POST /api/resume/analyze` parses text via `pypdf`.
- **Skill Engine**: Catalog comparison against 80+ programming languages, frameworks, and developer tools.
- **ATS Algorithm**: Weighted evaluation of keyword presence, length, and technical density.
- **Job Matching**: Identifies matched skills versus candidate skill gaps.
- **AI Feedback**: Google Gemini integration generating structured critique and action items.
- **Analysis Persistence**: Records stored in `resume_analyses`.
- **History & Latest**: `GET /api/resume/history` and `GET /api/resume/latest`.
- **Executive PDF Reporting**: `GET /api/resume/report/{id}` compiles multi-page PDF reports via `pymupdf`.

### User Profile Management
- **Profile Data**: `GET /api/profile` and `PUT /api/profile`.
- **Education Records**: `POST /api/profile/educations` and `DELETE /api/profile/educations/{id}`.
- **Skill Inventory**: `POST /api/profile/skills` and `DELETE /api/profile/skills/{skill_name}`.
- **Project Showcase**: `POST /api/profile/projects` and `DELETE /api/profile/projects/{id}`.
- **Certifications**: `POST /api/profile/certifications` and `DELETE /api/profile/certifications/{id}`.

### Courses, Lessons & Quizzes
- **Course Catalog**: `GET /api/courses` with search, difficulty, and skill filtering.
- **Course Details**: `GET /api/courses/{id}` providing curriculum hierarchy.
- **Enrollment**: `POST /api/courses/{id}/enroll` tracking user progress.
- **Lessons**: `GET /api/lessons/{id}` and `POST /api/lessons/{id}/complete` with automatic percentage recalculation.
- **Quizzes**: `GET /api/quizzes/{id}` and `POST /api/quizzes/{id}/submit` with instant score evaluation.

### Starter Courses Seeded
1. Python for Developers
2. Java Programming Fundamentals
3. SQL & Database Fundamentals
4. Data Structures & Algorithms
5. Web Development Fundamentals
6. React & Frontend Development
7. REST API Development
8. Git & GitHub
9. Docker Fundamentals
10. AWS Fundamentals

*(Original starter learning content seeded into PostgreSQL database via `seed_data.py`.)*

### Administrator API
- `GET /api/admin/access-check`: Validates admin authorization.
- `GET /api/admin/metrics`: Platform-wide stats (total users, active accounts, total courses, average ATS/quiz scores).
- `GET /api/admin/users`: Lists registered user accounts and roles.

---

## Technology Stack

- **Python 3.11+**
- **FastAPI**
- **SQLAlchemy 2.0**
- **PostgreSQL / Neon PostgreSQL** (`NullPool` connection resilience)
- **JWT (`python-jose`)**
- **Argon2 (`argon2-cffi`)**
- **pypdf** (PDF text extraction)
- **PyMuPDF** (`pymupdf`) (PDF report generation)
- **Google Gemini API** (`google-genai`)
- **python-dotenv**

---

## Database Models

The relational schema is defined in [`models.py`](models.py):

| Model | Table Name | Purpose |
|:---|:---|:---|
| `User` | `users` | Accounts, credentials, active status, role (`user`/`admin`). |
| `Profile` | `profiles` | Extended candidate profile, bio, social links. |
| `UserEducation` | `user_educations` | Academic qualifications. |
| `UserSkill` | `user_skills` | Technical competencies. |
| `UserProject` | `user_projects` | Technical portfolio projects. |
| `UserCertification` | `user_certifications` | Professional certificates. |
| `ResumeAnalysis` | `resume_analyses` | ATS scores, extracted skills, job match results, AI feedback. |
| `Course` | `courses` | Technical courses with metadata and skills covered. |
| `CourseModule` | `course_modules` | Syllabus sections within a course. |
| `Lesson` | `lessons` | Study units with explanations and code examples. |
| `LessonProgress` | `lesson_progress` | Completed lesson records per user. |
| `CourseEnrollment` | `course_enrollments` | Enrollment status and cumulative progress. |
| `Quiz` | `quizzes` | Assessments with passing score thresholds. |
| `QuizQuestion` | `quiz_questions` | Multiple-choice assessment questions. |
| `QuizOption` | `quiz_options` | Selectable answer options. |
| `QuizAttempt` | `quiz_attempts` | Attempt submissions with scores and percentage. |

---

## API Endpoint Reference

| Method | Endpoint | Description | Auth Required |
|:---|:---|:---|:---|
| `POST` | `/api/auth/register` | Register standard user | No |
| `POST` | `/api/auth/login` | Log in user or admin | No |
| `POST` | `/api/auth/admin/login` | Admin login | No |
| `GET` | `/api/auth/me` | Current user details | Yes (Bearer) |
| `GET` | `/api/profile` | Full profile + stats | Yes (Bearer) |
| `PUT` | `/api/profile` | Update profile info | Yes (Bearer) |
| `POST` | `/api/profile/educations` | Add education record | Yes (Bearer) |
| `DELETE` | `/api/profile/educations/{id}` | Delete education | Yes (Bearer) |
| `POST` | `/api/profile/skills` | Add skill tag | Yes (Bearer) |
| `DELETE` | `/api/profile/skills/{name}` | Delete skill tag | Yes (Bearer) |
| `POST` | `/api/profile/projects` | Add project record | Yes (Bearer) |
| `DELETE` | `/api/profile/projects/{id}` | Delete project | Yes (Bearer) |
| `POST` | `/api/profile/certifications` | Add certification | Yes (Bearer) |
| `DELETE` | `/api/profile/certifications/{id}` | Delete certification | Yes (Bearer) |
| `POST` | `/api/resume/analyze` | Analyze resume PDF + JD | Yes (Bearer) |
| `GET` | `/api/resume/history` | List analysis history | Yes (Bearer) |
| `GET` | `/api/resume/latest` | Latest analysis result | Yes (Bearer) |
| `GET` | `/api/resume/report/{id}` | Download PDF report | Yes (Bearer) |
| `GET` | `/api/courses` | List catalog courses | Optional |
| `GET` | `/api/courses/{id}` | Course syllabus | Optional |
| `POST` | `/api/courses/{id}/enroll` | Enroll in course | Yes (Bearer) |
| `GET` | `/api/lessons/{id}` | Get lesson content | Yes (Bearer) |
| `POST` | `/api/lessons/{id}/complete` | Mark lesson complete | Yes (Bearer) |
| `GET` | `/api/quizzes/{id}` | Get quiz questions | Yes (Bearer) |
| `POST` | `/api/quizzes/{id}/submit` | Submit quiz attempt | Yes (Bearer) |
| `GET` | `/api/quizzes/{id}/attempts` | Quiz attempt history | Yes (Bearer) |
| `GET` | `/api/learning/dashboard` | Learning hub overview | Yes (Bearer) |
| `GET` | `/api/learning/recommendations`| Missing skill course recs | Yes (Bearer) |
| `GET` | `/api/learning/progress` | User enrolled progress | Yes (Bearer) |
| `GET` | `/api/admin/access-check` | Admin authorization check | Admin Only |
| `GET` | `/api/admin/metrics` | Platform overview stats | Admin Only |
| `GET` | `/api/admin/users` | List platform users | Admin Only |

---

## Security

- **Argon2 Password Hashing**: Handled via `argon2-cffi`. Passwords are never stored in plaintext.
- **JWT Tokens**: Signed using `HS256` with expiration.
- **Strict Role Authorization**: Non-admin users attempting to call `/api/admin/*` receive **403 Forbidden**.
- **Notice on Administrator Provisioning**:
  > *Administrator registration is intentionally not exposed through the public registration flow. Admin account provisioning will be implemented separately.*

---

## Local Setup

```bash
# 1. Activate virtual environment
python -m venv venv
.\venv\Scripts\activate   # Windows
source venv/bin/activate  # macOS / Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment variables in .env
# DATABASE_URL=postgresql://...
# GEMINI_API_KEY=...
# JWT_SECRET_KEY=...

# 4. Seed starter courses
python seed_data.py

# 5. Run FastAPI development server
uvicorn main:app --reload
```
