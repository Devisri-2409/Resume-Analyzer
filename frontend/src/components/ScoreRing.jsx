import React from "react";

export function ScoreRing({ value, label, size = 100, color = "#18a66d", sublabel = "/ 100" }) {
  const safeValue = Math.max(0, Math.min(100, Number(value) || 0));
  const strokeWidth = 8;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (safeValue / 100) * circumference;

  return (
    <div className="score-ring-wrap" style={{ width: size, minWidth: size }}>
      <div className="score-ring-svg-container" style={{ width: size, height: size }}>
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
          {/* Background track */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="transparent"
            stroke="#e7efe9"
            strokeWidth={strokeWidth}
          />
          {/* Progress arc */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="transparent"
            stroke={color}
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            transform={`rotate(-90 ${size / 2} ${size / 2})`}
            style={{ transition: "stroke-dashoffset 0.8s ease" }}
          />
        </svg>
        <div className="score-ring-inner-text">
          <strong style={{ fontSize: size * 0.25 }}>{safeValue}</strong>
          {sublabel && <span style={{ fontSize: size * 0.1 }}>{sublabel}</span>}
        </div>
      </div>
      {label && <span className="score-label">{label}</span>}
    </div>
  );
}

