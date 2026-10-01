import React, { useEffect, useState } from "react";
import axios from "axios";
import { BookOpenIcon, ClockIcon, SearchIcon } from "./Icons";

export function CoursesView({ apiUrl, token, onNavigate, showToast }) {
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selectedDifficulty, setSelectedDifficulty] = useState("all");
  const [enrollingId, setEnrollingId] = useState(null);

  useEffect(() => {
    fetchCourses();
  }, [search, selectedDifficulty]);

  const fetchCourses = async () => {
    setLoading(true);
    try {
      const params = {};
      if (search.trim()) params.search = search.trim();
      if (selectedDifficulty !== "all") params.difficulty = selectedDifficulty;

      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      const res = await axios.get(`${apiUrl}/api/courses`, { headers, params });
      setCourses(res.data.courses || []);
    } catch (err) {
      console.error("Courses fetch error:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleEnrollOrContinue = async (course) => {
    if (course.is_enrolled) {
      onNavigate(`/courses/${course.id}`);
      return;
    }

    setEnrollingId(course.id);
    try {
      await axios.post(
        `${apiUrl}/api/courses/${course.id}/enroll`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (showToast) {
        showToast(`Enrolled in "${course.title}" successfully!`, "success");
      }
      onNavigate(`/courses/${course.id}`);
    } catch (err) {
      console.error("Enroll error:", err);
      if (showToast) {
        showToast("Could not complete enrollment. Please try again.", "error");
      }
    } finally {
      setEnrollingId(null);
    }
  };

  return (
    <div className="courses-view-content">
      <section className="page-heading">
        <div>
          <span className="eyebrow">CAREER SKILLS CURRICULUM</span>
          <h1>Course Catalog</h1>
          <p>
            Explore hands-on technical courses designed to bridge skill gaps identified in your resume
            and elevate your job readiness.
          </p>
        </div>
      </section>

      {/* Filter and Search Bar */}
      <section className="courses-toolbar">
        <div className="search-input-wrap">
          <SearchIcon size={16} className="search-icon" />
          <input
            type="text"
            placeholder="Search by course title, topic, or skill (e.g. Python, Docker, SQL)..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          {search && (
            <button type="button" className="clear-search-btn" onClick={() => setSearch("")}>
              ✕
            </button>
          )}
        </div>

        <div className="filter-pill-group">
          {["all", "Beginner", "Intermediate"].map((diff) => (
            <button
              key={diff}
              type="button"
              className={`filter-pill ${selectedDifficulty === diff ? "active" : ""}`}
              onClick={() => setSelectedDifficulty(diff)}
            >
              {diff === "all" ? "All Levels" : diff}
            </button>
          ))}
        </div>
      </section>

      {/* Courses Grid */}
      {loading ? (
        <div className="view-loading-state">
          <div className="spinner" />
          <p>Loading course catalog...</p>
        </div>
      ) : courses.length > 0 ? (
        <div className="courses-grid">
          {courses.map((course) => {
            const isEnrolled = course.is_enrolled;
            const progress = course.progress_percentage || 0;

            return (
              <div key={course.id} className="course-card">
                <div className="course-card-header">
                  <span className="badge-category">{course.category}</span>
                  <span className="badge-difficulty">{course.difficulty}</span>
                </div>

                <div className="course-card-body">
                  <h3>{course.title}</h3>
                  <p className="course-desc-text">{course.description}</p>

                  <div className="course-skills-list">
                    {course.skills_covered.slice(0, 4).map((skill) => (
                      <span key={skill} className="chip neutral small">
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="course-card-meta">
                  <div className="meta-badge">
                    <ClockIcon size={13} />
                    <span>{course.estimated_duration}</span>
                  </div>
                  <div className="meta-badge">
                    <BookOpenIcon size={13} />
                    <span>{course.total_lessons} lessons</span>
                  </div>
                  <div className="meta-badge">
                    <span>{course.total_quizzes} quiz</span>
                  </div>
                </div>

                {isEnrolled && (
                  <div className="course-card-progress">
                    <div className="progress-labels">
                      <span>Progress</span>
                      <strong>{progress}%</strong>
                    </div>
                    <div className="horizontal-progress-bar small">
                      <div className="bar-fill" style={{ width: `${progress}%` }} />
                    </div>
                  </div>
                )}

                <div className="course-card-footer">
                  <button
                    type="button"
                    className={`enroll-btn ${isEnrolled ? "continue" : "primary-button"}`}
                    onClick={() => handleEnrollOrContinue(course)}
                    disabled={enrollingId === course.id}
                  >
                    {enrollingId === course.id
                      ? "Enrolling..."
                      : isEnrolled
                      ? "Continue Course →"
                      : "Enroll Now →"}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="empty-card-prompt">
          <h3>No courses found</h3>
          <p>Try adjusting your search criteria or difficulty filter.</p>
          <button
            type="button"
            className="secondary-button"
            onClick={() => {
              setSearch("");
              setSelectedDifficulty("all");
            }}
          >
            Reset Filters
          </button>
        </div>
      )}
    </div>
  );
}

