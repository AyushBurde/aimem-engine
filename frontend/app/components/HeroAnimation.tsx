"use client";

import { useEffect, useState } from "react";

// ─────────────────────────────────────────────────────────
// DATA
// ─────────────────────────────────────────────────────────

const SCENARIOS = [
  {
    oldFact: "User lives in Delhi",
    newMsg: "I just moved to Mumbai",
    newFact: "User lives in Mumbai",
    score: 0.92,
    cat: "location",
    oldDate: "Jan 2026",
    newDate: "Aug 2026",
  },
  {
    oldFact: "User works at Google",
    newMsg: "Started at OpenAI last week",
    newFact: "User works at OpenAI",
    score: 0.89,
    cat: "work",
    oldDate: "Mar 2025",
    newDate: "Oct 2026",
  },
  {
    oldFact: "Favorite lang is Python",
    newMsg: "I've been writing Rust lately",
    newFact: "User prefers Rust now",
    score: 0.85,
    cat: "preference",
    oldDate: "Jun 2025",
    newDate: "Sep 2026",
  },
];

// Constellation nodes (% positions within the container)
const NODES = [
  { x: 10, y: 12 },
  { x: 75, y: 8 },
  { x: 92, y: 48 },
  { x: 6, y: 62 },
  { x: 52, y: 92 },
  { x: 35, y: 10 },
  { x: 94, y: 82 },
  { x: 15, y: 90 },
  { x: 62, y: 14 },
  { x: 42, y: 78 },
  { x: 82, y: 25 },
  { x: 28, y: 55 },
];

// Connection lines between constellation nodes
const EDGES = [
  [0, 5], [5, 1], [1, 10], [10, 8], [8, 2],
  [0, 11], [11, 3], [3, 7], [7, 9], [9, 4], [4, 6], [2, 6],
];

// ─────────────────────────────────────────────────────────
// ANIMATION PHASES
// ─────────────────────────────────────────────────────────

const P = {
  ACTIVE: 0,       // Show the current active memory
  INPUT: 1,        // User message slides in
  SCAN: 2,         // Similarity scan + score counting up
  DETECT: 3,       // ⚡ CONTRADICTION DETECTED flash
  RESOLVE: 4,      // Old → superseded, New → active
  TIMELINE: 5,     // Temporal timeline appears
  FADE: 6,         // Fade out for next cycle
};

// How long each phase lasts (ms)
const DURATIONS = [2500, 1800, 2200, 1500, 2500, 2200, 1500];

// ─────────────────────────────────────────────────────────
// COMPONENT
// ─────────────────────────────────────────────────────────

export default function HeroAnimation() {
  const [phase, setPhase] = useState(P.ACTIVE);
  const [si, setSi] = useState(0);
  const [scoreText, setScoreText] = useState("0.00");
  const sc = SCENARIOS[si];

  // ── Phase state machine ──
  useEffect(() => {
    const timer = setTimeout(() => {
      if (phase >= P.FADE) {
        setSi((i) => (i + 1) % SCENARIOS.length);
        setPhase(P.ACTIVE);
      } else {
        setPhase((p) => p + 1);
      }
    }, DURATIONS[phase]);
    return () => clearTimeout(timer);
  }, [phase]);

  // ── Score counter animation during SCAN ──
  useEffect(() => {
    if (phase === P.SCAN) {
      const target = sc.score;
      const frames = 30;
      const interval = (DURATIONS[P.SCAN] * 0.75) / frames;
      let i = 0;
      setScoreText("0.00");
      const timer = setInterval(() => {
        i++;
        setScoreText(Math.min(target, (target * i) / frames).toFixed(2));
        if (i >= frames) clearInterval(timer);
      }, interval);
      return () => clearInterval(timer);
    }
  }, [phase, sc.score]);

  const fading = phase === P.FADE;

  return (
    <div
      className={`hero-engine ${fading ? "hero-engine--fading" : ""}`}
    >
      {/* ═══════════════════════════════════════════════════
          LAYER 1: Constellation Background (SVG)
          ═══════════════════════════════════════════════════ */}
      <svg
        className="absolute inset-0 w-full h-full pointer-events-none"
        style={{ zIndex: 0 }}
        viewBox="0 0 100 100"
        preserveAspectRatio="none"
      >
        {/* Connection lines */}
        {EDGES.map(([a, b], i) => (
          <line
            key={`edge-${i}`}
            x1={NODES[a].x}
            y1={NODES[a].y}
            x2={NODES[b].x}
            y2={NODES[b].y}
            stroke="rgba(16,185,129,0.07)"
            strokeWidth="0.15"
            className="constellation-edge"
            style={{ animationDelay: `${i * 0.3}s` }}
          />
        ))}
        {/* Nodes */}
        {NODES.map((n, i) => (
          <circle
            key={`node-${i}`}
            cx={n.x}
            cy={n.y}
            r="0.8"
            fill="rgba(16,185,129,0.35)"
            className="constellation-node"
            style={{ animationDelay: `${i * 0.5}s` }}
          />
        ))}
      </svg>

      {/* ═══════════════════════════════════════════════════
          HEADER BAR (terminal-style)
          ═══════════════════════════════════════════════════ */}
      <div
        className="relative z-10 flex items-center gap-2 px-5 py-3"
        style={{ borderBottom: "1px solid rgba(255,255,255,0.04)" }}
      >
        <span className="w-[7px] h-[7px] rounded-full bg-[#FF5F57]" />
        <span className="w-[7px] h-[7px] rounded-full bg-[#FEBC2E]" />
        <span className="w-[7px] h-[7px] rounded-full bg-[#28C840]" />
        <span
          className="ml-2 uppercase tracking-widest"
          style={{ fontSize: "9px", color: "rgba(255,255,255,0.2)", fontFamily: "var(--mono)" }}
        >
          aimem engine
        </span>
        {/* Live dot */}
        <span className="ml-auto flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 live-dot" />
          <span style={{ fontSize: "9px", color: "rgba(16,185,129,0.4)", fontFamily: "var(--mono)" }}>
            live
          </span>
        </span>
      </div>

      {/* ═══════════════════════════════════════════════════
          LAYER 2: Main Contradiction Flow
          ═══════════════════════════════════════════════════ */}
      <div className="relative z-10 flex flex-col px-5 pt-4 pb-3" style={{ height: "calc(100% - 40px)" }}>

        {/* ── Old Memory Card ── */}
        <div
          className="flow-element"
          style={{
            opacity: phase >= P.ACTIVE ? 1 : 0,
            transform: phase >= P.ACTIVE ? "translateY(0)" : "translateY(12px)",
          }}
        >
          <div
            className="mem-card"
            style={{
              borderColor: phase >= P.RESOLVE
                ? "rgba(255,255,255,0.05)"
                : "rgba(16,185,129,0.2)",
              background: phase >= P.RESOLVE
                ? "rgba(255,255,255,0.01)"
                : "rgba(16,185,129,0.04)",
              boxShadow: phase < P.RESOLVE
                ? "0 0 24px rgba(16,185,129,0.06)"
                : "none",
            }}
          >
            {/* Status badge + category */}
            <div className="flex items-center justify-between mb-1.5">
              <span
                className="mem-badge"
                style={{
                  color: phase >= P.RESOLVE
                    ? "rgba(248,113,113,0.5)"
                    : "rgba(52,211,153,0.7)",
                }}
              >
                {phase >= P.RESOLVE ? "✕ superseded" : "● active"}
              </span>
              <span className="mem-meta">{sc.cat}</span>
            </div>

            {/* Fact text */}
            <p
              className="mem-text"
              style={{
                color: phase >= P.RESOLVE ? "rgba(255,255,255,0.2)" : "rgba(255,255,255,0.8)",
                textDecoration: phase >= P.RESOLVE ? "line-through" : "none",
              }}
            >
              {sc.oldFact}
            </p>

            {/* Validity period (shown after supersede) */}
            <div
              className="mem-validity"
              style={{ opacity: phase >= P.RESOLVE ? 1 : 0 }}
            >
              valid: {sc.oldDate} → {sc.newDate}
            </div>
          </div>
        </div>

        {/* ── User Message ── */}
        <div
          className="flow-element"
          style={{
            opacity: phase >= P.INPUT ? 1 : 0,
            transform: phase >= P.INPUT ? "translateY(0)" : "translateY(12px)",
            marginTop: "14px",
          }}
        >
          <div className="flex items-start gap-2.5 px-1">
            <span className="user-label">USER</span>
            <p className="user-text">&quot;{sc.newMsg}&quot;</p>
          </div>
        </div>

        {/* ── Similarity Score Bar ── */}
        <div
          className="flow-element"
          style={{
            opacity: phase >= P.SCAN ? 1 : 0,
            transform: phase >= P.SCAN ? "translateY(0)" : "translateY(12px)",
            marginTop: "14px",
          }}
        >
          <div className="flex items-center gap-3 px-1">
            <span className="score-label">similarity</span>
            <div className="score-track">
              <div
                className="score-fill"
                style={{
                  width: phase >= P.SCAN ? `${sc.score * 100}%` : "0%",
                  transitionDuration: `${DURATIONS[P.SCAN] * 0.75}ms`,
                  background: sc.score >= 0.85
                    ? "linear-gradient(90deg, rgba(251,191,36,0.7), rgba(239,68,68,0.7))"
                    : "linear-gradient(90deg, rgba(52,211,153,0.7), rgba(251,191,36,0.7))",
                }}
              />
            </div>
            <span
              className="score-value"
              style={{
                color: phase >= P.DETECT
                  ? "rgba(248,113,113,0.8)"
                  : "rgba(251,191,36,0.6)",
              }}
            >
              {phase >= P.SCAN ? scoreText : "0.00"}
            </span>
          </div>
        </div>

        {/* ── Contradiction Alert ── */}
        <div
          className="flow-element"
          style={{
            opacity: phase >= P.DETECT ? 1 : 0,
            transform: phase >= P.DETECT ? "translateY(0) scale(1)" : "translateY(8px) scale(0.95)",
            marginTop: "12px",
            textAlign: "center",
          }}
        >
          <span
            className="contradiction-text"
            style={{
              color: phase >= P.RESOLVE
                ? "rgba(255,255,255,0.15)"
                : "rgba(248,113,113,0.85)",
              animation: phase === P.DETECT ? "pulse-text 0.8s ease-in-out 2" : "none",
            }}
          >
            ⚡ CONTRADICTION DETECTED
          </span>
          <span
            className="action-text"
            style={{
              opacity: phase >= P.DETECT ? 1 : 0,
              color: phase >= P.RESOLVE
                ? "rgba(255,255,255,0.1)"
                : "rgba(255,255,255,0.25)",
            }}
          >
            action: SUPERSEDE
          </span>
        </div>

        {/* ── New Memory Card ── */}
        <div
          className="flow-element"
          style={{
            opacity: phase >= P.RESOLVE ? 1 : 0,
            transform: phase >= P.RESOLVE ? "translateY(0) scale(1)" : "translateY(16px) scale(0.97)",
            marginTop: "14px",
          }}
        >
          <div className="mem-card mem-card--new">
            {/* Status badge */}
            <div className="flex items-center justify-between mb-1.5">
              <span className="mem-badge" style={{ color: "rgba(52,211,153,0.85)" }}>
                ● active ✓
              </span>
              <span className="mem-meta">{sc.cat}</span>
            </div>

            {/* Fact text */}
            <p className="mem-text" style={{ color: "rgba(255,255,255,0.85)" }}>
              {sc.newFact}
            </p>

            {/* Validity */}
            <div className="mem-validity" style={{ opacity: 1, color: "rgba(52,211,153,0.3)" }}>
              valid_from: {sc.newDate}
            </div>
          </div>
        </div>

        {/* ── Spacer ── */}
        <div style={{ flex: 1 }} />

        {/* ═══════════════════════════════════════════════════
            LAYER 3: Temporal Timeline
            ═══════════════════════════════════════════════════ */}
        <div
          className="flow-element"
          style={{
            opacity: phase >= P.TIMELINE ? 1 : 0,
            transform: phase >= P.TIMELINE ? "translateY(0)" : "translateY(10px)",
          }}
        >
          <div className="px-1">
            {/* Label */}
            <div className="flex items-center gap-2 mb-2.5">
              <span className="timeline-label">temporal history</span>
              <div className="timeline-label-line" />
            </div>

            {/* Bar */}
            <div className="timeline-track">
              {/* Fill */}
              <div
                className="timeline-fill"
                style={{
                  width: phase >= P.TIMELINE ? "100%" : "0%",
                }}
              />
              {/* Old version dot */}
              <div className="timeline-dot timeline-dot--old" style={{ left: "12%" }}>
                <div className="timeline-dot-ring" />
              </div>
              {/* New version dot (current) */}
              <div className="timeline-dot timeline-dot--new" style={{ right: "4%" }}>
                <div className="timeline-dot-ring timeline-dot-ring--active" />
              </div>
            </div>

            {/* Date labels */}
            <div className="flex justify-between mt-2 px-1">
              <span className="timeline-date">{sc.oldDate}</span>
              <span className="timeline-date" style={{ color: "rgba(52,211,153,0.5)" }}>
                {sc.newDate} → now
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* ── Scan line effect ── */}
      {phase === P.SCAN && (
        <div className="scan-line" />
      )}

      {/* ── Contradiction flash overlay ── */}
      {phase === P.DETECT && (
        <div className="contradiction-flash" />
      )}
    </div>
  );
}
