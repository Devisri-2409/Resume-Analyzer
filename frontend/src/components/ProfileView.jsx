import React, { useEffect, useState } from "react";
import axios from "axios";
import { AwardIcon, BookOpenIcon, CheckCircleIcon, ExternalLinkIcon, FireIcon, PlusIcon, TrashIcon } from "./Icons";

export function ProfileView({ apiUrl, token, onNavigate, showToast, onUserUpdated }) {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [savingPersonal, setSavingPersonal] = useState(false);

  // Form states
  const [personalForm, setPersonalForm] = useState({
    full_name: "",
    phone: "",
    location: "",
    github: "",
    linkedin: "",
    portfolio: "",
    bio: "",
    avatar: "avatar-1",
  });

  // Modal / Add form toggles
  const [showEduModal, setShowEduModal] = useState(false);
  const [eduForm, setEduForm] = useState({ degree: "", branch: "", college: "", graduation_year: "" });

  const [showProjModal, setShowProjModal] = useState(false);
  const [projForm, setProjForm] = useState({ name: "", description: "", technologies: "", github_url: "", live_url: "" });

  const [showCertModal, setShowCertModal] = useState(false);
  const [certForm, setCertForm] = useState({ name: "", issuing_organization: "", issue_date: "", credential_url: "" });

  const [newSkillInput, setNewSkillInput] = useState("");

  // Email verification state
  const [sendingEmail, setSendingEmail] = useState(false);
  const [showEmailModal, setShowEmailModal] = useState(false);
  const [emailTokenInput, setEmailTokenInput] = useState("");
  const [verifyingEmail, setVerifyingEmail] = useState(false);
  const [emailError, setEmailError] = useState("");
  const [emailCooldown, setEmailCooldown] = useState(0);

  // Phone verification state
  const [showPhoneModal, setShowPhoneModal] = useState(false);
  const [phoneOtpInput, setPhoneOtpInput] = useState("");
  const [sendingOtp, setSendingOtp] = useState(false);
  const [verifyingOtp, setVerifyingOtp] = useState(false);
  const [phoneError, setPhoneError] = useState("");
  const [phoneCooldown, setPhoneCooldown] = useState(0);
  const [attemptsRemaining, setAttemptsRemaining] = useState(5);

  // Cooldown timers
  useEffect(() => {
    if (emailCooldown <= 0) return;
    const timer = setInterval(() => setEmailCooldown((prev) => prev - 1), 1000);
    return () => clearInterval(timer);
  }, [emailCooldown]);

  useEffect(() => {
    if (phoneCooldown <= 0) return;
    const timer = setInterval(() => setPhoneCooldown((prev) => prev - 1), 1000);
    return () => clearInterval(timer);
  }, [phoneCooldown]);

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${apiUrl}/api/profile`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setProfile(res.data);
      const pi = res.data.personal_info;
      setPersonalForm({
        full_name: pi.full_name || "",
        phone: pi.phone || "",
        location: pi.location || "",
        github: pi.github || "",
        linkedin: pi.linkedin || "",
        portfolio: pi.portfolio || "",
        bio: pi.bio || "",
        avatar: pi.avatar || "avatar-1",
      });
    } catch (err) {
      console.error("Profile fetch error:", err);
      if (showToast) showToast("Could not load profile details.", "error");
    } finally {
      setLoading(false);
    }
  };

  const handleSavePersonal = async (e) => {
    e.preventDefault();
    setSavingPersonal(true);
    try {
      await axios.put(`${apiUrl}/api/profile`, personalForm, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (showToast) showToast("Personal profile updated successfully!", "success");
      if (onUserUpdated) onUserUpdated({ full_name: personalForm.full_name });
      fetchProfile();
    } catch (err) {
      console.error("Profile save error:", err);
      if (showToast) showToast("Failed to save personal profile.", "error");
    } finally {
      setSavingPersonal(false);
    }
  };

  const handleSendEmailVerification = async () => {
    if (sendingEmail || emailCooldown > 0) return;
    setSendingEmail(true);
    setEmailError("");
    try {
      const res = await axios.post(
        `${apiUrl}/api/auth/email/send-verification`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setEmailCooldown(60);
      if (showToast) showToast(res.data.message || "Verification email sent! Check your inbox.", "success");
    } catch (err) {
      const msg = err?.response?.data?.detail || "Failed to send verification email.";
      setEmailError(msg);
      if (showToast) showToast(msg, "error");
    } finally {
      setSendingEmail(false);
    }
  };

  const handleVerifyEmailToken = async (e) => {
    if (e) e.preventDefault();
    if (!emailTokenInput.trim()) return;
    setVerifyingEmail(true);
    setEmailError("");
    try {
      await axios.post(
        `${apiUrl}/api/auth/email/verify`,
        { token: emailTokenInput.trim() },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (showToast) showToast("Email successfully verified!", "success");
      setShowEmailModal(false);
      setEmailTokenInput("");
      setProfile((prev) => ({
        ...prev,
        personal_info: { ...prev?.personal_info, is_email_verified: true },
      }));
      if (onUserUpdated) onUserUpdated({ is_email_verified: true });
    } catch (err) {
      const msg = err?.response?.data?.detail || "Invalid or expired token.";
      setEmailError(msg);
      if (showToast) showToast(msg, "error");
    } finally {
      setVerifyingEmail(false);
    }
  };

  const handleSendPhoneOtp = async () => {
    const phoneNumber = personalForm.phone || profile?.personal_info?.phone;
    if (!phoneNumber || phoneNumber.trim().length < 8) {
      if (showToast) showToast("Please enter a valid phone number (at least 8 digits) first.", "error");
      return;
    }
    if (sendingOtp || phoneCooldown > 0) return;
    setSendingOtp(true);
    setPhoneError("");
    try {
      const res = await axios.post(
        `${apiUrl}/api/auth/phone/send-otp`,
        { phone_number: phoneNumber.trim() },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setPhoneCooldown(60);
      setAttemptsRemaining(5);
      setShowPhoneModal(true);
      if (showToast) showToast(res.data.message || "Verification code sent!", "success");
    } catch (err) {
      const msg = err?.response?.data?.detail || "Failed to send OTP code.";
      setPhoneError(msg);
      if (showToast) showToast(msg, "error");
    } finally {
      setSendingOtp(false);
    }
  };

  const handleVerifyPhoneOtp = async (e) => {
    if (e) e.preventDefault();
    const phoneNumber = personalForm.phone || profile?.personal_info?.phone;
    if (!phoneOtpInput.trim()) return;
    setVerifyingOtp(true);
    setPhoneError("");
    try {
      await axios.post(
        `${apiUrl}/api/auth/phone/verify-otp`,
        { phone_number: phoneNumber.trim(), otp: phoneOtpInput.trim() },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (showToast) showToast("Phone number verified successfully!", "success");
      setShowPhoneModal(false);
      setPhoneOtpInput("");
      setProfile((prev) => ({
        ...prev,
        personal_info: {
          ...prev?.personal_info,
          phone: phoneNumber.trim(),
          is_phone_verified: true,
        },
      }));
      if (onUserUpdated) onUserUpdated({ is_phone_verified: true, phone_number: phoneNumber.trim() });
    } catch (err) {
      const msg = err?.response?.data?.detail || "Incorrect verification code.";
      setPhoneError(msg);
      setAttemptsRemaining((prev) => Math.max(0, prev - 1));
      if (showToast) showToast(msg, "error");
    } finally {
      setVerifyingOtp(false);
    }
  };

  const handleAddSkill = async (e) => {
    e.preventDefault();
    const skill = newSkillInput.trim();
    if (!skill) return;
    try {
      await axios.post(
        `${apiUrl}/api/profile/skills`,
        { skill_name: skill },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setNewSkillInput("");
      if (showToast) showToast(`Added "${skill}" to skills!`, "success");
      fetchProfile();
    } catch (err) {
      console.error("Add skill error:", err);
      if (showToast) showToast("Could not add skill.", "error");
    }
  };

  const handleDeleteSkill = async (skillName) => {
    try {
      await axios.delete(`${apiUrl}/api/profile/skills/${encodeURIComponent(skillName)}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (showToast) showToast(`Removed "${skillName}".`, "info");
      fetchProfile();
    } catch (err) {
      console.error("Delete skill error:", err);
    }
  };

  const handleAddEducation = async (e) => {
    e.preventDefault();
    if (!eduForm.degree.trim()) return;
    try {
      await axios.post(`${apiUrl}/api/profile/education`, eduForm, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setShowEduModal(false);
      setEduForm({ degree: "", branch: "", college: "", graduation_year: "" });
      if (showToast) showToast("Education added successfully!", "success");
      fetchProfile();
    } catch (err) {
      console.error("Education add error:", err);
    }
  };

  const handleDeleteEducation = async (id) => {
    try {
      await axios.delete(`${apiUrl}/api/profile/education/${id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (showToast) showToast("Education entry removed.", "info");
      fetchProfile();
    } catch (err) {
      console.error("Education delete error:", err);
    }
  };

  const handleAddProject = async (e) => {
    e.preventDefault();
    if (!projForm.name.trim()) return;
    try {
      await axios.post(`${apiUrl}/api/profile/projects`, projForm, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setShowProjModal(false);
      setProjForm({ name: "", description: "", technologies: "", github_url: "", live_url: "" });
      if (showToast) showToast("Project added successfully!", "success");
      fetchProfile();
    } catch (err) {
      console.error("Project add error:", err);
    }
  };

  const handleDeleteProject = async (id) => {
    try {
      await axios.delete(`${apiUrl}/api/profile/projects/${id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (showToast) showToast("Project entry removed.", "info");
      fetchProfile();
    } catch (err) {
      console.error("Project delete error:", err);
    }
  };

  const handleAddCertification = async (e) => {
    e.preventDefault();
    if (!certForm.name.trim()) return;
    try {
      await axios.post(`${apiUrl}/api/profile/certifications`, certForm, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setShowCertModal(false);
      setCertForm({ name: "", issuing_organization: "", issue_date: "", credential_url: "" });
      if (showToast) showToast("Certification added successfully!", "success");
      fetchProfile();
    } catch (err) {
      console.error("Certification add error:", err);
    }
  };

  const handleDeleteCertification = async (id) => {
    try {
      await axios.delete(`${apiUrl}/api/profile/certifications/${id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (showToast) showToast("Certification removed.", "info");
      fetchProfile();
    } catch (err) {
      console.error("Certification delete error:", err);
    }
  };

  if (loading) {
    return (
      <div className="view-loading-state">
        <div className="spinner" />
        <p>Loading your career profile...</p>
      </div>
    );
  }

  const stats = profile?.learning_statistics || {
    courses_enrolled: 0,
    courses_completed: 0,
    quizzes_completed: 0,
    average_quiz_score: 0,
    skills_learned: 0,
    learning_streak: 1,
  };

  return (
    <div className="profile-view-content">
      <section className="page-heading">
        <div>
          <span className="eyebrow">PROFESSIONAL IDENTITY & ACHIEVEMENTS</span>
          <h1>Candidate Profile</h1>
          <p>
            Manage your personal background, validated technical skills, portfolio projects, and verified
            learning statistics.
          </p>
        </div>
      </section>

      {/* LEARNING STATISTICS CARDS */}
      <section className="profile-stats-grid">
        <div className="p-stat-card">
          <span className="stat-label">COURSES ENROLLED</span>
          <strong>{stats.courses_enrolled}</strong>
          <small>Active learning pathways</small>
        </div>

        <div className="p-stat-card accent">
          <span className="stat-label">COURSES COMPLETED</span>
          <strong>{stats.courses_completed}</strong>
          <small>100% curriculum finish</small>
        </div>

        <div className="p-stat-card">
          <span className="stat-label">QUIZZES COMPLETED</span>
          <strong>{stats.quizzes_completed}</strong>
          <small>Verified assessments</small>
        </div>

        <div className="p-stat-card">
          <span className="stat-label">AVERAGE QUIZ SCORE</span>
          <strong className="text-success">{stats.average_quiz_score}%</strong>
          <small>Assessment mastery</small>
        </div>

        <div className="p-stat-card">
          <span className="stat-label">SKILLS LEARNED</span>
          <strong>{profile?.skills?.length || 0}</strong>
          <small>Verified competencies</small>
        </div>

        <div className="p-stat-card streak-card">
          <div className="streak-icon-wrap">
            <FireIcon size={20} />
          </div>
          <span className="stat-label">LEARNING STREAK</span>
          <strong>{stats.learning_streak} {stats.learning_streak === 1 ? "Day" : "Days"}</strong>
          <small>Longest streak: {stats.longest_streak ?? stats.learning_streak ?? 0} days</small>
        </div>
      </section>

      {/* TWO COLUMN CONTENT */}
      <div className="profile-layout-grid">
        {/* LEFT COLUMN: Personal Info & Skills */}
        <div className="profile-column">
          {/* Personal Info Card */}
          <section className="profile-section-card">
            <div className="card-top-header">
              <div>
                <span className="section-kicker">ABOUT YOU</span>
                <h2>Personal Information</h2>
              </div>
            </div>

            <form onSubmit={handleSavePersonal} className="personal-info-form">
              <div className="form-row-two">
                <label>
                  Full name
                  <input
                    type="text"
                    value={personalForm.full_name}
                    onChange={(e) => setPersonalForm({ ...personalForm, full_name: e.target.value })}
                    required
                  />
                </label>
                <div>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                    <label style={{ margin: 0 }}>Email address</label>
                    {profile?.personal_info?.is_email_verified ? (
                      <span className="verify-status-badge verified">
                        <CheckCircleIcon size={12} /> Verified
                      </span>
                    ) : (
                      <div className="verify-badge-group">
                        <span className="verify-status-badge unverified">Unverified</span>
                        <button
                          type="button"
                          className="verify-action-btn"
                          onClick={handleSendEmailVerification}
                          disabled={sendingEmail || emailCooldown > 0}
                          title="Send verification email with token link"
                        >
                          {emailCooldown > 0 ? `Resend (${emailCooldown}s)` : "Send Verification"}
                        </button>
                        <button
                          type="button"
                          className="verify-action-btn subtle"
                          onClick={() => {
                            setEmailError("");
                            setShowEmailModal(true);
                          }}
                          title="Enter verification token manually"
                        >
                          Token
                        </button>
                      </div>
                    )}
                  </div>
                  <input
                    type="email"
                    value={profile?.personal_info?.email || ""}
                    disabled
                    className="disabled-input"
                  />
                </div>
              </div>

              <div className="form-row-two">
                <div>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                    <label style={{ margin: 0 }}>Phone number</label>
                    {profile?.personal_info?.is_phone_verified ? (
                      <span className="verify-status-badge verified">
                        <CheckCircleIcon size={12} /> Verified
                      </span>
                    ) : (
                      <div className="verify-badge-group">
                        <span className="verify-status-badge unverified">Unverified</span>
                        <button
                          type="button"
                          className="verify-action-btn"
                          onClick={handleSendPhoneOtp}
                          disabled={sendingOtp || phoneCooldown > 0}
                          title="Send 6-digit verification code via SMS"
                        >
                          {phoneCooldown > 0 ? `Resend (${phoneCooldown}s)` : "Verify via SMS"}
                        </button>
                      </div>
                    )}
                  </div>
                  <input
                    type="text"
                    placeholder="+91 98765 43210"
                    value={personalForm.phone}
                    onChange={(e) => setPersonalForm({ ...personalForm, phone: e.target.value })}
                  />
                </div>
                <label>
                  Location
                  <input
                    type="text"
                    placeholder="City, Country"
                    value={personalForm.location}
                    onChange={(e) => setPersonalForm({ ...personalForm, location: e.target.value })}
                  />
                </label>
              </div>

              <div className="form-row-two">
                <label>
                  GitHub Profile URL
                  <input
                    type="url"
                    placeholder="https://github.com/username"
                    value={personalForm.github}
                    onChange={(e) => setPersonalForm({ ...personalForm, github: e.target.value })}
                  />
                </label>
                <label>
                  LinkedIn Profile URL
                  <input
                    type="url"
                    placeholder="https://linkedin.com/in/username"
                    value={personalForm.linkedin}
                    onChange={(e) => setPersonalForm({ ...personalForm, linkedin: e.target.value })}
                  />
                </label>
              </div>

              <label>
                Portfolio Website
                <input
                  type="url"
                  placeholder="https://yourportfolio.dev"
                  value={personalForm.portfolio}
                  onChange={(e) => setPersonalForm({ ...personalForm, portfolio: e.target.value })}
                />
              </label>

              <label>
                Professional Bio / Summary
                <textarea
                  rows={3}
                  placeholder="Write a brief professional summary..."
                  value={personalForm.bio}
                  onChange={(e) => setPersonalForm({ ...personalForm, bio: e.target.value })}
                />
              </label>

              <div className="form-footer-action">
                <button type="submit" className="primary-button" disabled={savingPersonal}>
                  {savingPersonal ? "Saving..." : "Save Profile Changes"}
                </button>
              </div>
            </form>
          </section>

          {/* SKILLS SECTION */}
          <section className="profile-section-card">
            <div className="card-top-header">
              <div>
                <span className="section-kicker">COMPETENCIES</span>
                <h2>Technical Skills ({profile?.skills?.length || 0})</h2>
              </div>
            </div>

            {/* Add Skill Input */}
            <form onSubmit={handleAddSkill} className="add-skill-bar">
              <input
                type="text"
                placeholder="Add a new skill (e.g. Docker, Python, AWS)..."
                value={newSkillInput}
                onChange={(e) => setNewSkillInput(e.target.value)}
              />
              <button type="submit" className="primary-button small">
                <PlusIcon size={14} />
                <span>Add Skill</span>
              </button>
            </form>

            {/* Skills Chip Cloud */}
            <div className="chips profile-skills-cloud">
              {profile?.skills && profile.skills.length > 0 ? (
                profile.skills.map((skill) => (
                  <span key={skill} className="chip profile-chip">
                    <span>{skill}</span>
                    <button
                      type="button"
                      className="chip-remove"
                      onClick={() => handleDeleteSkill(skill)}
                      title={`Remove ${skill}`}
                    >
                      ×
                    </button>
                  </span>
                ))
              ) : (
                <span className="empty-state">
                  No skills listed yet. Add skills or analyze your resume to extract them automatically.
                </span>
              )}
            </div>
          </section>
        </div>

        {/* RIGHT COLUMN: Education, Projects, Certifications */}
        <div className="profile-column">
          {/* EDUCATION SECTION */}
          <section className="profile-section-card">
            <div className="card-top-header">
              <div>
                <span className="section-kicker">ACADEMIC BACKGROUND</span>
                <h2>Education</h2>
              </div>
              <button
                type="button"
                className="secondary-button small"
                onClick={() => setShowEduModal(true)}
              >
                <PlusIcon size={14} />
                <span>Add Education</span>
              </button>
            </div>

            {profile?.educations && profile.educations.length > 0 ? (
              <div className="items-stack">
                {profile.educations.map((edu) => (
                  <div key={edu.id} className="item-row-card">
                    <div className="item-left">
                      <strong>{edu.degree}</strong>
                      <span>{edu.branch ? `${edu.branch} • ` : ""}{edu.college}</span>
                      <small className="item-date">{edu.graduation_year || "Graduation Year"}</small>
                    </div>
                    <button
                      type="button"
                      className="icon-action-btn delete"
                      onClick={() => handleDeleteEducation(edu.id)}
                      title="Delete education"
                    >
                      <TrashIcon size={14} />
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-section-prompt">
                <p>No education records added yet.</p>
                <button
                  type="button"
                  className="link-button"
                  onClick={() => setShowEduModal(true)}
                >
                  + Add Degree & College
                </button>
              </div>
            )}
          </section>

          {/* PROJECTS SECTION */}
          <section className="profile-section-card">
            <div className="card-top-header">
              <div>
                <span className="section-kicker">PORTFOLIO</span>
                <h2>Projects</h2>
              </div>
              <button
                type="button"
                className="secondary-button small"
                onClick={() => setShowProjModal(true)}
              >
                <PlusIcon size={14} />
                <span>Add Project</span>
              </button>
            </div>

            {profile?.projects && profile.projects.length > 0 ? (
              <div className="items-stack">
                {profile.projects.map((proj) => (
                  <div key={proj.id} className="item-row-card">
                    <div className="item-left">
                      <strong>{proj.name}</strong>
                      <p className="item-desc">{proj.description}</p>
                      {proj.technologies && (
                        <div className="chips">
                          {proj.technologies.split(",").map((tech, idx) => (
                            <span key={idx} className="chip neutral small">
                              {tech.trim()}
                            </span>
                          ))}
                        </div>
                      )}
                      <div className="item-links">
                        {proj.github_url && (
                          <a href={proj.github_url} target="_blank" rel="noopener noreferrer">
                            GitHub <ExternalLinkIcon size={12} />
                          </a>
                        )}
                        {proj.live_url && (
                          <a href={proj.live_url} target="_blank" rel="noopener noreferrer">
                            Live Demo <ExternalLinkIcon size={12} />
                          </a>
                        )}
                      </div>
                    </div>
                    <button
                      type="button"
                      className="icon-action-btn delete"
                      onClick={() => handleDeleteProject(proj.id)}
                      title="Delete project"
                    >
                      <TrashIcon size={14} />
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-section-prompt">
                <p>No portfolio projects added yet.</p>
                <button
                  type="button"
                  className="link-button"
                  onClick={() => setShowProjModal(true)}
                >
                  + Add First Project
                </button>
              </div>
            )}
          </section>

          {/* CERTIFICATIONS SECTION */}
          <section className="profile-section-card">
            <div className="card-top-header">
              <div>
                <span className="section-kicker">CREDENTIALS</span>
                <h2>Certifications</h2>
              </div>
              <button
                type="button"
                className="secondary-button small"
                onClick={() => setShowCertModal(true)}
              >
                <PlusIcon size={14} />
                <span>Add Certification</span>
              </button>
            </div>

            {profile?.certifications && profile.certifications.length > 0 ? (
              <div className="items-stack">
                {profile.certifications.map((cert) => (
                  <div key={cert.id} className="item-row-card">
                    <div className="item-left">
                      <strong>{cert.name}</strong>
                      <span>{cert.issuing_organization}</span>
                      <small className="item-date">{cert.issue_date}</small>
                      {cert.credential_url && (
                        <div className="item-links">
                          <a href={cert.credential_url} target="_blank" rel="noopener noreferrer">
                            Verify Credential <ExternalLinkIcon size={12} />
                          </a>
                        </div>
                      )}
                    </div>
                    <button
                      type="button"
                      className="icon-action-btn delete"
                      onClick={() => handleDeleteCertification(cert.id)}
                      title="Delete certification"
                    >
                      <TrashIcon size={14} />
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-section-prompt">
                <p>No certifications added yet.</p>
                <button
                  type="button"
                  className="link-button"
                  onClick={() => setShowCertModal(true)}
                >
                  + Add Certification
                </button>
              </div>
            )}
          </section>
        </div>
      </div>

      {/* ADD EDUCATION MODAL */}
      {showEduModal && (
        <div className="modal-backdrop" onClick={() => setShowEduModal(false)}>
          <div className="modal-dialog" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Add Education</h3>
              <button type="button" className="close-btn" onClick={() => setShowEduModal(false)}>
                ✕
              </button>
            </div>
            <form onSubmit={handleAddEducation} className="modal-form">
              <label>
                Degree *
                <input
                  type="text"
                  placeholder="e.g. Bachelor of Technology (B.Tech)"
                  value={eduForm.degree}
                  onChange={(e) => setEduForm({ ...eduForm, degree: e.target.value })}
                  required
                />
              </label>
              <label>
                Branch / Specialization
                <input
                  type="text"
                  placeholder="e.g. Computer Science and Engineering"
                  value={eduForm.branch}
                  onChange={(e) => setEduForm({ ...eduForm, branch: e.target.value })}
                />
              </label>
              <label>
                College / University
                <input
                  type="text"
                  placeholder="e.g. National Institute of Technology"
                  value={eduForm.college}
                  onChange={(e) => setEduForm({ ...eduForm, college: e.target.value })}
                />
              </label>
              <label>
                Graduation Year
                <input
                  type="text"
                  placeholder="e.g. 2026"
                  value={eduForm.graduation_year}
                  onChange={(e) => setEduForm({ ...eduForm, graduation_year: e.target.value })}
                />
              </label>
              <div className="modal-actions">
                <button type="button" className="secondary-button" onClick={() => setShowEduModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="primary-button">
                  Save Education
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ADD PROJECT MODAL */}
      {showProjModal && (
        <div className="modal-backdrop" onClick={() => setShowProjModal(false)}>
          <div className="modal-dialog" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Add Portfolio Project</h3>
              <button type="button" className="close-btn" onClick={() => setShowProjModal(false)}>
                ✕
              </button>
            </div>
            <form onSubmit={handleAddProject} className="modal-form">
              <label>
                Project Name *
                <input
                  type="text"
                  placeholder="e.g. AI Resume Analyzer"
                  value={projForm.name}
                  onChange={(e) => setProjForm({ ...projForm, name: e.target.value })}
                  required
                />
              </label>
              <label>
                Description
                <textarea
                  rows={3}
                  placeholder="Describe the architecture, problem solved, and results..."
                  value={projForm.description}
                  onChange={(e) => setProjForm({ ...projForm, description: e.target.value })}
                />
              </label>
              <label>
                Technologies (comma separated)
                <input
                  type="text"
                  placeholder="e.g. React, FastAPI, Python, Docker, PostgreSQL"
                  value={projForm.technologies}
                  onChange={(e) => setProjForm({ ...projForm, technologies: e.target.value })}
                />
              </label>
              <label>
                GitHub Repository URL
                <input
                  type="url"
                  placeholder="https://github.com/username/project"
                  value={projForm.github_url}
                  onChange={(e) => setProjForm({ ...projForm, github_url: e.target.value })}
                />
              </label>
              <label>
                Live Demo URL
                <input
                  type="url"
                  placeholder="https://project-demo.com"
                  value={projForm.live_url}
                  onChange={(e) => setProjForm({ ...projForm, live_url: e.target.value })}
                />
              </label>
              <div className="modal-actions">
                <button type="button" className="secondary-button" onClick={() => setShowProjModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="primary-button">
                  Save Project
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ADD CERTIFICATION MODAL */}
      {showCertModal && (
        <div className="modal-backdrop" onClick={() => setShowCertModal(false)}>
          <div className="modal-dialog" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Add Certification</h3>
              <button type="button" className="close-btn" onClick={() => setShowCertModal(false)}>
                ✕
              </button>
            </div>
            <form onSubmit={handleAddCertification} className="modal-form">
              <label>
                Certification Name *
                <input
                  type="text"
                  placeholder="e.g. AWS Certified Cloud Practitioner"
                  value={certForm.name}
                  onChange={(e) => setCertForm({ ...certForm, name: e.target.value })}
                  required
                />
              </label>
              <label>
                Issuing Organization
                <input
                  type="text"
                  placeholder="e.g. Amazon Web Services (AWS)"
                  value={certForm.issuing_organization}
                  onChange={(e) => setCertForm({ ...certForm, issuing_organization: e.target.value })}
                />
              </label>
              <label>
                Issue Date
                <input
                  type="text"
                  placeholder="e.g. June 2026"
                  value={certForm.issue_date}
                  onChange={(e) => setCertForm({ ...certForm, issue_date: e.target.value })}
                />
              </label>
              <label>
                Credential Verification URL
                <input
                  type="url"
                  placeholder="https://www.credly.com/badges/..."
                  value={certForm.credential_url}
                  onChange={(e) => setCertForm({ ...certForm, credential_url: e.target.value })}
                />
              </label>
              <div className="modal-actions">
                <button type="button" className="secondary-button" onClick={() => setShowCertModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="primary-button">
                  Save Certification
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* EMAIL VERIFICATION TOKEN MODAL */}
      {showEmailModal && (
        <div className="modal-backdrop" onClick={() => setShowEmailModal(false)}>
          <div className="modal-dialog" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Verify Email Address</h3>
              <button type="button" className="close-btn" onClick={() => setShowEmailModal(false)}>
                ✕
              </button>
            </div>
            <form onSubmit={handleVerifyEmailToken} className="modal-form">
              <p className="modal-hint-text">
                Enter the verification token sent to <strong>{profile?.personal_info?.email}</strong>.
              </p>
              <label>
                Verification Token
                <input
                  type="text"
                  placeholder="Paste verification token here..."
                  value={emailTokenInput}
                  onChange={(e) => setEmailTokenInput(e.target.value)}
                  required
                  autoFocus
                />
              </label>
              {emailError && <div className="modal-error-text">{emailError}</div>}
              <div className="modal-actions">
                <button type="button" className="secondary-button" onClick={() => setShowEmailModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="primary-button" disabled={verifyingEmail || !emailTokenInput.trim()}>
                  {verifyingEmail ? "Verifying..." : "Confirm Verification"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* PHONE OTP VERIFICATION MODAL */}
      {showPhoneModal && (
        <div className="modal-backdrop" onClick={() => setShowPhoneModal(false)}>
          <div className="modal-dialog" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Verify Phone Number</h3>
              <button type="button" className="close-btn" onClick={() => setShowPhoneModal(false)}>
                ✕
              </button>
            </div>
            <form onSubmit={handleVerifyPhoneOtp} className="modal-form">
              <p className="modal-hint-text">
                We sent a 6-digit verification code to <strong>{personalForm.phone || profile?.personal_info?.phone}</strong>. Code expires in 10 minutes.
              </p>
              <label>
                6-Digit Security Code
                <input
                  type="text"
                  maxLength={6}
                  className="otp-box-input"
                  placeholder="123456"
                  value={phoneOtpInput}
                  onChange={(e) => setPhoneOtpInput(e.target.value.replace(/\D/g, ""))}
                  required
                  autoFocus
                />
              </label>
              {phoneError && <div className="modal-error-text">{phoneError}</div>}
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "0.82rem", color: "#64748b", margin: "8px 0" }}>
                <span>{attemptsRemaining} attempt{attemptsRemaining === 1 ? "" : "s"} remaining</span>
                <button
                  type="button"
                  className="verify-action-btn"
                  onClick={handleSendPhoneOtp}
                  disabled={sendingOtp || phoneCooldown > 0}
                >
                  {phoneCooldown > 0 ? `Resend code in ${phoneCooldown}s` : "Resend code"}
                </button>
              </div>
              <div className="modal-actions">
                <button type="button" className="secondary-button" onClick={() => setShowPhoneModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="primary-button" disabled={verifyingOtp || phoneOtpInput.length < 6}>
                  {verifyingOtp ? "Verifying..." : "Verify OTP"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

