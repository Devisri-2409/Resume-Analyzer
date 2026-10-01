import React from "react";
import {
  DashboardIcon,
  ResumeIcon,
  CoursesIcon,
  LearningIcon,
  ProfileIcon,
  ReportsIcon,
  LogoutIcon,
} from "./Icons";

export function Sidebar({ currentPath, onNavigate, onLogout, user, isOpen, onClose }) {
  const navItems = [
    { label: "Dashboard", path: "/dashboard", icon: DashboardIcon },
    { label: "Resume Analyzer", path: "/analyzer", icon: ResumeIcon },
    { label: "Courses", path: "/courses", icon: CoursesIcon },
    { label: "My Learning", path: "/learning", icon: LearningIcon },
    { label: "Profile", path: "/profile", icon: ProfileIcon },
    { label: "Reports", path: "/reports", icon: ReportsIcon },
  ];

  const handleItemClick = (path) => {
    onNavigate(path);
    if (onClose) onClose();
  };

  const getInitials = (name) => {
    if (!name) return "U";
    return name
      .split(" ")
      .map((part) => part[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);
  };

  return (
    <>
      {isOpen && <div className="sidebar-backdrop" onClick={onClose} />}
      <aside className={`app-sidebar ${isOpen ? "open" : ""}`}>
        <div className="sidebar-brand">
          <div className="brand-mark small">RA</div>
          <div className="brand-text">
            <strong>ResumeAI</strong>
            <span>Career & Learning</span>
          </div>
        </div>

        <div className="sidebar-section-label">MAIN MENU</div>
        <nav className="sidebar-nav">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive =
              currentPath === item.path ||
              (item.path !== "/dashboard" && currentPath.startsWith(item.path));
            return (
              <button
                key={item.path}
                type="button"
                className={`sidebar-nav-item ${isActive ? "active" : ""}`}
                onClick={() => handleItemClick(item.path)}
              >
                <span className="nav-icon-wrap">
                  <Icon size={18} />
                </span>
                <span className="nav-label">{item.label}</span>
                {isActive && <span className="nav-active-pill" />}
              </button>
            );
          })}
        </nav>

        {user?.role === "admin" && (
          <div style={{ padding: "0 1rem 0.75rem 1rem" }}>
            <button
              type="button"
              onClick={() => handleItemClick("/admin/dashboard")}
              style={{
                width: "100%",
                padding: "8px 12px",
                background: "linear-gradient(135deg, #4f46e5, #7c3aed)",
                color: "#ffffff",
                border: "none",
                borderRadius: "8px",
                fontWeight: 600,
                fontSize: "0.82rem",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: "8px",
                boxShadow: "0 2px 8px rgba(79, 70, 229, 0.3)",
              }}
            >
              <span>🛡️</span>
              <span>Admin Workspace</span>
            </button>
          </div>
        )}

        <div className="sidebar-footer">
          <div className="user-mini-card" onClick={() => handleItemClick("/profile")}>
            <div className="user-avatar-badge">{getInitials(user?.full_name)}</div>
            <div className="user-mini-info">
              <strong>{user?.full_name || "User"}</strong>
              <small>{user?.email || ""}</small>
            </div>
          </div>
          <button type="button" className="sidebar-logout-btn" onClick={onLogout} title="Log out">
            <LogoutIcon size={16} />
            <span>Log out</span>
          </button>
        </div>
      </aside>
    </>
  );
}

