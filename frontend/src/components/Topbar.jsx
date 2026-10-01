import React from "react";
import { FireIcon, ResumeIcon } from "./Icons";

export function Topbar({ user, pageTitle, pageSubtitle, onOpenSidebar, onNavigate, streak = 1 }) {
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
    <header className="app-topbar">
      <div className="topbar-left">
        <button
          type="button"
          className="mobile-menu-toggle"
          onClick={onOpenSidebar}
          aria-label="Open menu"
        >
          <span />
          <span />
          <span />
        </button>
        <div className="page-header-title">
          <h2>{pageTitle}</h2>
          {pageSubtitle && <p>{pageSubtitle}</p>}
        </div>
      </div>

      <div className="topbar-right">
        <div className="streak-badge" title="Consecutive active learning days">
          <FireIcon size={16} className="fire-icon" />
          <span>{streak} Day Streak</span>
        </div>

        <button
          type="button"
          className="quick-analyze-btn"
          onClick={() => onNavigate("/analyzer")}
        >
          <ResumeIcon size={15} />
          <span>Analyze Resume</span>
        </button>

        {user?.role === "admin" && (
          <button
            type="button"
            className="secondary-button"
            onClick={() => onNavigate("/admin/dashboard")}
            style={{
              fontSize: "0.82rem",
              padding: "6px 12px",
              background: "rgba(99, 102, 241, 0.15)",
              color: "#a5b4fc",
              border: "1px solid rgba(99, 102, 241, 0.3)",
              borderRadius: "6px",
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            🛡️ Admin Panel
          </button>
        )}

        <div className="topbar-user" onClick={() => onNavigate("/profile")} title="Go to Profile">
          <div className="avatar-circle">{getInitials(user?.full_name)}</div>
          <div className="topbar-user-name">
            <strong>{user?.full_name?.split(" ")[0]}</strong>
            <small>{user?.role === "admin" ? "Admin" : "Student"}</small>
          </div>
        </div>
      </div>
    </header>
  );
}

