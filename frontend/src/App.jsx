import { useEffect, useMemo, useState } from "react";
import axios from "axios";
import "./App.css";

// Components
import { Sidebar } from "./components/Sidebar";
import { Topbar } from "./components/Topbar";
import { Toast } from "./components/Toast";
import { DashboardView } from "./components/DashboardView";
import { AnalyzerView } from "./components/AnalyzerView";
import { CoursesView } from "./components/CoursesView";
import { CourseDetailView } from "./components/CourseDetailView";
import { LessonView } from "./components/LessonView";
import { QuizView } from "./components/QuizView";
import { LearningView } from "./components/LearningView";
import { ProfileView } from "./components/ProfileView";
import { ReportsView } from "./components/ReportsView";

// Admin Sub-Views
import {
  AdminDashboardOverview,
  AdminUsersView,
  AdminPerformanceView,
  AdminCoursesView,
  AdminLearningPathsView,
  AdminTestsView,
  AdminQuestionsView,
  AdminBadgesView,
  AdminReportsView,
} from "./components/admin/AdminViews";

const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

function getToken() {
  return localStorage.getItem("resume_analyzer_token");
}

function apiError(error, fallback) {
  return error?.response?.data?.detail || fallback;
}

function parseRoute(path) {
  if (!path || path === "/" || path === "/dashboard") return { page: "dashboard" };
  if (path === "/analyzer" || path === "/resume") return { page: "analyzer" };
  if (path === "/courses") return { page: "courses" };
  if (path === "/learning") return { page: "learning" };
  if (path === "/profile") return { page: "profile" };
  if (path === "/reports") return { page: "reports" };

  // Admin routing
  if (path.startsWith("/admin")) {
    const sub = path.replace(/^\/admin\/?/, "");
    const validSections = [
      "dashboard",
      "users",
      "performance",
      "courses",
      "learning-paths",
      "tests",
      "questions",
      "badges",
      "reports",
    ];
    const section = validSections.includes(sub) ? sub : "dashboard";
    return { page: "admin", section };
  }

  const lessonMatch = path.match(/^\/courses\/(\d+)\/lessons\/(\d+)/);
  if (lessonMatch) {
    return { page: "lesson", courseId: Number(lessonMatch[1]), lessonId: Number(lessonMatch[2]) };
  }

  const quizMatch = path.match(/^\/courses\/(\d+)\/quizzes\/(\d+)/);
  if (quizMatch) {
    return { page: "quiz", courseId: Number(quizMatch[1]), quizId: Number(quizMatch[2]) };
  }

  const courseMatch = path.match(/^\/courses\/(\d+)/);
  if (courseMatch) {
    return { page: "course-detail", courseId: Number(courseMatch[1]) };
  }

  return { page: "dashboard" };
}

function AuthScreen({ mode, onModeChange, onAuthenticated }) {
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [adminStatus, setAdminStatus] = useState(null);

  const isRegister = mode === "register";
  const isAdminLogin = mode === "admin-login";

  useEffect(() => {
    if (isAdminLogin) {
      axios
        .get(`${API_URL}/api/auth/admin/status`)
        .then((res) => setAdminStatus(res.data))
        .catch(() => setAdminStatus(null));
    }
  }, [isAdminLogin]);

  const submit = async (event) => {
    event.preventDefault();
    setError("");

    if (isRegister && fullName.trim().length < 2) {
      setError("Please enter your full name.");
      return;
    }

    if (isRegister && password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);
    try {
      const endpoint = isRegister
        ? "/api/auth/register"
        : isAdminLogin
          ? "/api/auth/admin/login"
          : "/api/auth/login";
      const payload = isRegister
        ? { full_name: fullName.trim(), email, password }
        : { email, password };

      const response = await axios.post(`${API_URL}${endpoint}`, payload);
      localStorage.setItem("resume_analyzer_token", response.data.access_token);
      onAuthenticated(response.data.user);
    } catch (err) {
      const statusCode = err?.response?.status;
      const detail = err?.response?.data?.detail;
      if (statusCode === 403 && isAdminLogin) {
        setError(detail || "Admin access required. This account does not possess administrator privileges.");
      } else if (statusCode === 401) {
        setError(isAdminLogin ? "Invalid administrator credentials. Please check your email and password." : "Invalid email or password.");
      } else if (statusCode >= 500) {
        setError("Server error during authentication. Please verify the backend service is running.");
      } else {
        setError(apiError(err, "Unable to complete the request."));
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-brand">
        <div className="brand-mark">RA</div>
        <div>
          <strong>ResumeAI</strong>
          <span>Career & Learning Platform</span>
        </div>
      </div>

      <div className="auth-mode-switch" aria-label="Choose sign in type">
        <button
          className={!isAdminLogin ? "active" : ""}
          onClick={() => onModeChange("login")}
          type="button"
        >
          User Login
        </button>
        <button
          className={isAdminLogin ? "active admin" : ""}
          onClick={() => onModeChange("admin-login")}
          type="button"
        >
          Admin Login
        </button>
      </div>

      <div className="auth-layout">
        <section className="auth-hero">
          <span className="eyebrow">AI CAREER & LEARNING PLATFORM</span>
          <h1>Turn your resume into a stronger career profile.</h1>
          <p>
            Analyze ATS compatibility, compare your skills against job descriptions,
            bridge detected skill gaps through realistic courses, and track your verified learning progress.
          </p>

          <div className="feature-list">
            <div><span>✓</span> ATS Score & Job Description matching</div>
            <div><span>✓</span> Skill gap detection & course recommendations</div>
            <div><span>✓</span> Interactive lessons & certification quizzes</div>
            <div><span>✓</span> Executive PDF analysis report generation</div>
          </div>
        </section>

        <form className="auth-card" onSubmit={submit}>
          <div className="auth-card-header">
            <span className="mini-label">
              {isRegister ? "GET STARTED" : isAdminLogin ? "ADMIN PORTAL" : "WELCOME BACK"}
            </span>
            <h2>
              {isRegister
                ? "Create your account"
                : isAdminLogin
                  ? "Admin sign in"
                  : "Sign in to ResumeAI"}
            </h2>
            <p>
              {isRegister
                ? "Start accelerating your career in a few seconds."
                : isAdminLogin
                  ? "Manage the ResumeAI career platform."
                  : "Continue your career & learning journey."}
            </p>
          </div>

          {isAdminLogin && adminStatus && !adminStatus.has_admin && (
            <div
              style={{
                background: "rgba(245, 158, 11, 0.12)",
                border: "1px solid rgba(245, 158, 11, 0.3)",
                borderRadius: "10px",
                padding: "10px 14px",
                marginBottom: "16px",
                fontSize: "0.82rem",
                color: "#d97706",
                lineHeight: "1.4",
              }}
            >
              <strong>Notice:</strong> No platform administrator account found. Initialize an admin by running <code>python manage_admin.py create</code> or set <code>ADMIN_EMAIL</code> and <code>ADMIN_PASSWORD</code> in <code>backend/.env</code>.
            </div>
          )}

          {isRegister && (
            <label>
              Full name
              <input
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Your full name"
                autoComplete="name"
              />
            </label>
          )}

          <label>
            {isAdminLogin ? "Admin email" : "Email address"}
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              autoComplete="email"
            />
          </label>

          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={isRegister ? "At least 8 characters" : "Your password"}
              autoComplete={isRegister ? "new-password" : "current-password"}
            />
          </label>

          {isRegister && (
            <label>
              Confirm password
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Repeat your password"
                autoComplete="new-password"
              />
            </label>
          )}

          {error && <div className="form-error">{error}</div>}

          <button className="primary-button" disabled={loading}>
            {loading
              ? "Please wait..."
              : isRegister
                ? "Register"
                : isAdminLogin
                  ? "Admin sign in"
                  : "Sign in"}
          </button>

          <div className="auth-switch">
            {isRegister ? "Already have an account?" : isAdminLogin ? "Need a user account?" : "Don't have an account?"}
            <button
              type="button"
              className="link-button"
              onClick={() => {
                setError("");
                onModeChange(isRegister || isAdminLogin ? "login" : "register");
              }}
            >
              {isRegister || isAdminLogin ? "User Login" : "Register"}
            </button>
          </div>

          {!isRegister && !isAdminLogin && (
            <div className="auth-switch admin-switch">
              Platform administrator? <button type="button" className="link-button" onClick={() => onModeChange("admin-login")}>Admin Login</button>
            </div>
          )}
        </form>
      </div>
    </div>
  );
}

function AdminDashboard({
  user,
  currentPath,
  activeSection = "dashboard",
  onLogout,
  onNavigate,
  apiUrl,
  token,
  showToast,
}) {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchMetrics = () => {
    const authToken = token || getToken();
    if (!authToken) return;
    setLoading(true);
    setError(null);
    axios
      .get(`${apiUrl || API_URL}/api/admin/metrics`, {
        headers: { Authorization: `Bearer ${authToken}` },
      })
      .then((res) => {
        setMetrics(res.data);
        setError(null);
      })
      .catch((err) => {
        console.error("Admin metrics fetch error:", err);
        const detail = err?.response?.data?.detail;
        if (err?.response?.status === 403) {
          setError(detail || "Admin access required. You do not possess administrator permissions.");
        } else if (err?.response?.status === 401) {
          setError("Session expired or unauthorized. Please sign in again.");
        } else {
          setError("Failed to load administrator metrics. Server error occurred.");
        }
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    if (activeSection === "dashboard") {
      fetchMetrics();
    }
  }, [activeSection]);

  const adminSections = [
    { number: "01", id: "dashboard", title: "Dashboard", description: "Overview and activity", path: "/admin/dashboard" },
    { number: "02", id: "users", title: "Users", description: "Accounts and access", path: "/admin/users" },
    { number: "03", id: "performance", title: "Performance", description: "Scores and progress", path: "/admin/performance" },
    { number: "04", id: "courses", title: "Courses", description: "Learning content", path: "/admin/courses" },
    { number: "05", id: "learning-paths", title: "Learning Paths", description: "Career journeys", path: "/admin/learning-paths" },
    { number: "06", id: "tests", title: "Tests", description: "Assessments", path: "/admin/tests" },
    { number: "07", id: "questions", title: "Questions", description: "Question bank", path: "/admin/questions" },
    { number: "08", id: "badges", title: "Badges", description: "Achievements", path: "/admin/badges" },
    { number: "09", id: "reports", title: "Reports", description: "Platform insights", path: "/admin/reports" },
  ];

  const currentSectionMeta = adminSections.find((s) => s.id === activeSection) || adminSections[0];

  return (
    <div className="admin-dashboard">
      <aside className="admin-sidebar">
        <div className="admin-brand">
          <div className="brand-mark small">RA</div>
          <div><strong>ResumeAI</strong><span>Admin workspace</span></div>
        </div>
        <nav className="admin-nav">
          {adminSections.map((item) => {
            const isSelected =
              activeSection === item.id ||
              (item.id === "dashboard" && (currentPath === "/admin" || currentPath === "/admin/dashboard"));
            return (
              <button
                className={`admin-nav-item ${isSelected ? "selected" : ""}`}
                key={item.id}
                type="button"
                onClick={() => onNavigate(item.path)}
              >
                <span>{item.number}</span>
                <div>
                  <strong>{item.title}</strong>
                  <small>{item.description}</small>
                </div>
              </button>
            );
          })}
        </nav>
        <div style={{ marginTop: "auto", display: "flex", flexDirection: "column", gap: "8px" }}>
          <button
            className="secondary-button"
            style={{ width: "100%", justifyContent: "center", fontSize: "0.82rem", padding: "8px 12px" }}
            onClick={() => onNavigate("/dashboard")}
            type="button"
          >
            ← View User Portal
          </button>
          <button className="admin-logout" onClick={onLogout} type="button">Log out</button>
        </div>
      </aside>

      <main className="admin-main">
        <header className="admin-header">
          <div>
            <span className="eyebrow">CONTROL CENTER / {currentSectionMeta.title.toUpperCase()}</span>
            <h1>
              {activeSection === "dashboard"
                ? `Good morning, ${user.full_name.split(" ")[0]}.`
                : currentSectionMeta.title}
            </h1>
            <p>
              {activeSection === "dashboard"
                ? "Platform status and aggregated learning & resume analytics."
                : currentSectionMeta.description}
            </p>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <button
              className="quick-analyze-btn"
              onClick={() => onNavigate("/dashboard")}
              type="button"
              style={{ fontSize: "0.85rem", padding: "8px 14px" }}
            >
              Open User View →
            </button>
            <div className="admin-profile">
              <span className="admin-avatar">{user.full_name.charAt(0).toUpperCase()}</span>
              <div>
                <strong>{user.full_name}</strong>
                <small>Administrator</small>
              </div>
            </div>
          </div>
        </header>

        {activeSection === "dashboard" && (
          <AdminDashboardOverview
            metrics={metrics}
            loading={loading}
            error={error}
            onRetry={fetchMetrics}
            onNavigate={onNavigate}
          />
        )}
        {activeSection === "users" && (
          <AdminUsersView
            apiUrl={apiUrl || API_URL}
            token={token || getToken()}
            showToast={showToast}
            onNavigate={onNavigate}
          />
        )}
        {activeSection === "performance" && (
          <AdminPerformanceView
            apiUrl={apiUrl || API_URL}
            token={token || getToken()}
            showToast={showToast}
            onNavigate={onNavigate}
          />
        )}
        {activeSection === "courses" && (
          <AdminCoursesView
            apiUrl={apiUrl || API_URL}
            token={token || getToken()}
            showToast={showToast}
            onNavigate={onNavigate}
          />
        )}
        {activeSection === "learning-paths" && (
          <AdminLearningPathsView
            apiUrl={apiUrl || API_URL}
            token={token || getToken()}
            showToast={showToast}
            onNavigate={onNavigate}
          />
        )}
        {activeSection === "tests" && (
          <AdminTestsView
            apiUrl={apiUrl || API_URL}
            token={token || getToken()}
            showToast={showToast}
            onNavigate={onNavigate}
          />
        )}
        {activeSection === "questions" && (
          <AdminQuestionsView
            apiUrl={apiUrl || API_URL}
            token={token || getToken()}
            showToast={showToast}
            onNavigate={onNavigate}
          />
        )}
        {activeSection === "badges" && (
          <AdminBadgesView
            apiUrl={apiUrl || API_URL}
            token={token || getToken()}
            showToast={showToast}
            onNavigate={onNavigate}
          />
        )}
        {activeSection === "reports" && (
          <AdminReportsView
            apiUrl={apiUrl || API_URL}
            token={token || getToken()}
            showToast={showToast}
            onNavigate={onNavigate}
          />
        )}
      </main>
    </div>
  );
}

function App() {
  const [user, setUser] = useState(null);
  const [authMode, setAuthMode] = useState(
    window.location.pathname === "/register"
      ? "register"
      : window.location.pathname === "/admin/login"
        ? "admin-login"
        : "login"
  );
  const [checkingAuth, setCheckingAuth] = useState(() => Boolean(getToken()));
  const [currentPath, setCurrentPath] = useState(window.location.pathname || "/dashboard");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [toast, setToast] = useState({ message: "", type: "success" });
  const [streak, setStreak] = useState(0);
  const [refreshKey, setRefreshKey] = useState(0);

  const fetchStreak = () => {
    const token = getToken();
    if (!token) return;
    axios
      .get(`${API_URL}/api/learning/streak`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      .then((res) => {
        setStreak(res.data.current_streak || 0);
      })
      .catch((err) => {
        console.error("Streak fetch error:", err);
      });
  };

  const handleActivityCompleted = () => {
    fetchStreak();
    setRefreshKey((k) => k + 1);
  };

  const navigate = (path) => {
    window.history.pushState({}, "", path);
    setCurrentPath(path);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  useEffect(() => {
    const handlePopState = () => {
      setCurrentPath(window.location.pathname || "/dashboard");
    };
    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  // Handle email verification token in URL query params if clicked from email
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const verifyToken = params.get("verify_email_token") || params.get("token");
    if (verifyToken) {
      axios
        .post(`${API_URL}/api/auth/email/verify`, { token: verifyToken })
        .then((res) => {
          showToast(res.data.message || "Email address verified successfully!", "success");
          setUser((prev) => (prev ? { ...prev, is_email_verified: true } : prev));
          const cleanUrl = window.location.pathname;
          window.history.replaceState({}, document.title, cleanUrl);
        })
        .catch((err) => {
          const msg = err?.response?.data?.detail || "Email verification failed or link expired.";
          showToast(msg, "error");
        });
    }
  }, []);

  const handleAuthenticated = (authenticatedUser) => {
    setUser(authenticatedUser);
    fetchStreak();
    const dest = authenticatedUser.role === "admin" ? "/admin/dashboard" : "/dashboard";
    navigate(dest);
  };

  useEffect(() => {
    const token = getToken();
    if (!token) {
      setCheckingAuth(false);
      return;
    }

    axios
      .get(`${API_URL}/api/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      .then((response) => {
        setUser(response.data);
        fetchStreak();
        if (window.location.pathname === "/" || window.location.pathname === "/login") {
          navigate(response.data.role === "admin" ? "/admin/dashboard" : "/dashboard");
        }
      })
      .catch(() => {
        localStorage.removeItem("resume_analyzer_token");
        setUser(null);
      })
      .finally(() => setCheckingAuth(false));
  }, []);

  const logout = () => {
    localStorage.removeItem("resume_analyzer_token");
    setUser(null);
    setAuthMode("login");
    navigate("/login");
  };

  const showToast = (message, type = "success") => {
    setToast({ message, type });
  };

  if (checkingAuth) {
    return (
      <div className="full-loader">
        <div className="spinner" />
      </div>
    );
  }

  if (!user) {
    return (
      <AuthScreen
        mode={authMode}
        onModeChange={(mode) => {
          setAuthMode(mode);
          navigate(mode === "register" ? "/register" : mode === "admin-login" ? "/admin/login" : "/login");
        }}
        onAuthenticated={handleAuthenticated}
      />
    );
  }

  // If non-admin attempts to access /admin routes, redirect to user dashboard with informative toast
  if (user.role !== "admin" && currentPath.startsWith("/admin")) {
    showToast("Admin access required. Please sign in with an administrator account.", "error");
    navigate("/dashboard");
    return null;
  }

  if (user.role === "admin" && currentPath.startsWith("/admin")) {
    const adminRoute = parseRoute(currentPath);
    return (
      <AdminDashboard
        user={user}
        currentPath={currentPath}
        activeSection={adminRoute.section || "dashboard"}
        onLogout={logout}
        onNavigate={navigate}
        apiUrl={API_URL}
        token={getToken()}
        showToast={showToast}
      />
    );
  }

  // Parse Route for main authenticated platform
  const route = parseRoute(currentPath);

  const getPageInfo = () => {
    switch (route.page) {
      case "dashboard":
        return { title: "Career Dashboard", subtitle: "Overview of resume health & active learning" };
      case "analyzer":
        return { title: "Resume Analyzer", subtitle: "ATS compatibility & skill gap detection" };
      case "courses":
        return { title: "Course Catalog", subtitle: "Technical learning pathways to bridge career gaps" };
      case "course-detail":
        return { title: "Course Curriculum", subtitle: "Curriculum modules and quizzes" };
      case "lesson":
        return { title: "Lesson Room", subtitle: "Hands-on technical study" };
      case "quiz":
        return { title: "Course Assessment", subtitle: "Test your knowledge & validate skills" };
      case "learning":
        return { title: "My Learning", subtitle: "Track active courses, quizzes, and streaks" };
      case "profile":
        return { title: "Professional Profile", subtitle: "Personal info, verified skills, and portfolio" };
      case "reports":
        return { title: "Analysis Reports", subtitle: "Audit records and executive PDF reports" };
      default:
        return { title: "Career Platform", subtitle: "" };
    }
  };

  const pageInfo = getPageInfo();

  return (
    <div className="app-container">
      {/* Responsive Sidebar */}
      <Sidebar
        currentPath={currentPath}
        onNavigate={navigate}
        onLogout={logout}
        user={user}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      {/* Main Area */}
      <div className="app-main-area">
        <Topbar
          user={user}
          pageTitle={pageInfo.title}
          pageSubtitle={pageInfo.subtitle}
          onOpenSidebar={() => setSidebarOpen(true)}
          onNavigate={navigate}
          streak={streak}
        />

        <main className="app-content-body">
          {route.page === "dashboard" && (
            <DashboardView
              user={user}
              onNavigate={navigate}
              apiUrl={API_URL}
              token={getToken()}
              showToast={showToast}
              refreshKey={refreshKey}
              onActivityCompleted={handleActivityCompleted}
            />
          )}

          {route.page === "analyzer" && (
            <AnalyzerView
              apiUrl={API_URL}
              token={getToken()}
              onNavigate={navigate}
              showToast={showToast}
              onLogout={logout}
              onActivityCompleted={handleActivityCompleted}
            />
          )}

          {route.page === "courses" && (
            <CoursesView
              apiUrl={API_URL}
              token={getToken()}
              onNavigate={navigate}
              showToast={showToast}
            />
          )}

          {route.page === "course-detail" && (
            <CourseDetailView
              courseId={route.courseId}
              apiUrl={API_URL}
              token={getToken()}
              onNavigate={navigate}
              showToast={showToast}
              onActivityCompleted={handleActivityCompleted}
            />
          )}

          {route.page === "lesson" && (
            <LessonView
              courseId={route.courseId}
              lessonId={route.lessonId}
              apiUrl={API_URL}
              token={getToken()}
              onNavigate={navigate}
              showToast={showToast}
              onActivityCompleted={handleActivityCompleted}
            />
          )}

          {route.page === "quiz" && (
            <QuizView
              courseId={route.courseId}
              quizId={route.quizId}
              apiUrl={API_URL}
              token={getToken()}
              onNavigate={navigate}
              showToast={showToast}
              onActivityCompleted={handleActivityCompleted}
            />
          )}

          {route.page === "learning" && (
            <LearningView
              apiUrl={API_URL}
              token={getToken()}
              onNavigate={navigate}
              showToast={showToast}
              refreshKey={refreshKey}
              onActivityCompleted={handleActivityCompleted}
            />
          )}

          {route.page === "profile" && (
            <ProfileView
              apiUrl={API_URL}
              token={getToken()}
              onNavigate={navigate}
              showToast={showToast}
              onUserUpdated={(updated) => setUser((prev) => ({ ...prev, ...updated }))}
            />
          )}

          {route.page === "reports" && (
            <ReportsView
              apiUrl={API_URL}
              token={getToken()}
              onNavigate={navigate}
              showToast={showToast}
            />
          )}
        </main>
      </div>

      {/* Global Toast Notification */}
      <Toast
        message={toast.message}
        type={toast.type}
        onClose={() => setToast({ message: "", type: "success" })}
      />
    </div>
  );
}

export default App;

