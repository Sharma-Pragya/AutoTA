/**
 * Instructor quiz control screens — Phase 2.3
 * Route: /instructor/quiz/:code
 * Covers: Pending → Live → Closed → Review
 */
import { useState, useEffect, useRef } from "react";
import { QRCodeSVG } from "qrcode.react";
import {
  getQuizMeta, getLiveStats, getResults,
  startQuiz, closeQuiz, setReview,
} from "../../quiz/quizApi";

// ── Styles (I = instructor desktop) ──────────────────────────────────────────
const I = {
  page: {
    minHeight: "100vh", background: "#f0f0f0",
    fontFamily: "'IBM Plex Sans', -apple-system, BlinkMacSystemFont, sans-serif",
  },
  hdr: {
    display: "flex", justifyContent: "space-between", alignItems: "center",
    padding: "12px 28px", background: "#1a1a1a", color: "#fff",
    position: "sticky", top: 0, zIndex: 50,
  },
  logo: { fontSize: 16, fontWeight: 700 },
  sep: { color: "#555", margin: "0 4px" },
  course: { fontWeight: 600 },
  content: { maxWidth: 1100, margin: "0 auto", padding: "20px 24px" },
  card: {
    background: "#fff", borderRadius: 8, padding: "18px 22px",
    boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
  },
  cardTitle: { fontSize: 14, fontWeight: 700, color: "#1a1a1a", margin: "0 0 12px" },
  readyCard: {
    background: "#fff", borderRadius: 12, padding: "40px",
    maxWidth: 580, margin: "40px auto", textAlign: "center",
    boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
  },
  startBtn: {
    padding: "16px 40px", background: "#2e7d32", color: "#fff",
    border: "none", borderRadius: 10, fontSize: 18, fontWeight: 700,
    cursor: "pointer",
  },
  endBtn: {
    padding: "8px 18px", background: "#c62828", color: "#fff",
    border: "none", borderRadius: 6, fontSize: 13, fontWeight: 600, cursor: "pointer",
  },
  reviewBtn: {
    padding: "8px 18px", background: "#2774AE", color: "#fff",
    border: "none", borderRadius: 6, fontSize: 13, fontWeight: 600, cursor: "pointer",
  },
  liveRow: { display: "flex", gap: 12, marginBottom: 20, flexWrap: "wrap" },
  liveCard: {
    flex: "1 1 140px", background: "#fff", borderRadius: 8, padding: "16px 20px",
    boxShadow: "0 1px 3px rgba(0,0,0,0.06)", textAlign: "center",
  },
  liveNum: {
    fontSize: 32, fontWeight: 700, color: "#1a1a1a", margin: "0 0 4px",
    fontFamily: "'IBM Plex Mono', monospace",
  },
  liveLbl: { fontSize: 12, color: "#888", margin: 0 },
  miniBar: { height: 4, background: "#e8e8e8", borderRadius: 2, marginTop: 8, overflow: "hidden" },
  miniFill: { height: "100%", background: "#2774AE", borderRadius: 2, transition: "width 0.5s" },
};

function fmt(s) {
  if (!s && s !== 0) return "--:--";
  s = Math.max(0, Math.floor(s));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}

function ScoreCell({ score }) {
  if (score === null || score === undefined) return <span style={{ color: "#ccc" }}>—</span>;
  const pct = Math.round(score * 100);
  const bg = pct >= 80 ? "#e8f5e9" : pct >= 50 ? "#fff8e1" : "#ffebee";
  const color = pct >= 80 ? "#2e7d32" : pct >= 50 ? "#f57f17" : "#c62828";
  return (
    <span style={{ background: bg, color, padding: "2px 8px", borderRadius: 4, fontSize: 13, fontWeight: 600, fontFamily: "'IBM Plex Mono', monospace" }}>
      {pct}%
    </span>
  );
}

// ── Pending screen ────────────────────────────────────────────────────────────

function QuizPending({ meta, code, onStarted }) {
  const [starting, setStarting] = useState(false);
  const studentUrl = `${window.location.origin}/quiz/${code}`;
  const timeLimitMins = Math.floor((meta?.time_limit_seconds || 600) / 60);

  async function handleStart() {
    setStarting(true);
    try {
      await startQuiz(code);
      onStarted();
    } catch (e) {
      alert("Could not start quiz: " + (e.message || "server error"));
    } finally {
      setStarting(false);
    }
  }

  return (
    <div style={I.page}>
      <div style={I.hdr}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span style={I.logo}>AutoTA</span>
          <span style={I.sep}>·</span>
          <span style={I.course}>ECE M16</span>
          <span style={I.sep}>·</span>
          <span style={{ color: "#aaa" }}>Quiz Control</span>
        </div>
        <span style={{ color: "#aaa", fontSize: 12 }}>Prof. Mani Srivastava</span>
      </div>
      <div style={I.content}>
        <div style={I.readyCard}>
          <h2 style={{ fontSize: 22, fontWeight: 700, margin: "0 0 8px" }}>
            {meta?.assignment_title || "Quiz"}
          </h2>
          <p style={{ fontSize: 14, color: "#666", margin: "0 0 24px" }}>
            {meta?.problem_count || "—"} problems · {timeLimitMins} min · Unlimited retries · {meta?.total_enrolled || "—"} enrolled
          </p>

          <div style={{ display: "flex", gap: 32, justifyContent: "center", alignItems: "flex-start", margin: "20px 0" }}>
            {/* QR Code */}
            <div style={{ textAlign: "center" }}>
              <div style={{
                background: "#fff", borderRadius: 8, padding: 12,
                border: "1px solid #eee", display: "inline-block",
              }}>
                <QRCodeSVG value={studentUrl} size={140} />
              </div>
              <p style={{ fontSize: 11, color: "#aaa", margin: "4px 0 0" }}>Students scan to join</p>
            </div>

            {/* Code display */}
            <div style={{ textAlign: "center" }}>
              <p style={{ fontSize: 13, color: "#888", margin: "0 0 4px" }}>Quiz Code</p>
              <p style={{
                fontSize: 36, fontWeight: 700, fontFamily: "'IBM Plex Mono', monospace",
                color: "#2774AE", margin: 0, letterSpacing: "0.05em",
              }}>
                {code}
              </p>
              <p style={{ fontSize: 12, color: "#aaa", margin: "4px 0 0" }}>
                {window.location.host}/quiz/{code}
              </p>
            </div>
          </div>

          {/* How it works */}
          <div style={{
            background: "#f0f7ff", borderRadius: 8, padding: "12px 16px",
            margin: "20px auto 24px", textAlign: "left", maxWidth: 380,
          }}>
            <p style={{ fontSize: 13, color: "#333", margin: "0 0 6px", fontWeight: 600 }}>How it works:</p>
            <p style={{ fontSize: 12, color: "#666", margin: "0 0 3px" }}>1. Students scan QR or enter code to join</p>
            <p style={{ fontSize: 12, color: "#666", margin: "0 0 3px" }}>2. Click Start — timer begins for everyone</p>
            <p style={{ fontSize: 12, color: "#666", margin: "0 0 3px" }}>3. Students submit → see score instantly → can retry</p>
            <p style={{ fontSize: 12, color: "#666", margin: 0 }}>4. Best score recorded when time expires</p>
          </div>

          <button style={{ ...I.startBtn, opacity: starting ? 0.6 : 1 }} onClick={handleStart} disabled={starting}>
            {starting ? "Starting…" : `▶ Start Quiz (${timeLimitMins} min)`}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Live screen ───────────────────────────────────────────────────────────────

function QuizLive({ code, meta, onClosed }) {
  const [stats, setStats] = useState(null);
  const [secsRemaining, setSecsRemaining] = useState(meta?.time_remaining_seconds ?? meta?.time_limit_seconds ?? 600);
  const timerRef = useRef(null);
  const pollRef = useRef(null);

  // Client-side countdown
  useEffect(() => {
    timerRef.current = setInterval(() => {
      setSecsRemaining(t => Math.max(0, t - 1));
    }, 1000);
    return () => clearInterval(timerRef.current);
  }, []);

  // Poll every 3s
  useEffect(() => {
    async function poll() {
      try {
        const data = await getLiveStats(code);
        setStats(data);
        if (data.time_remaining_seconds !== null) {
          setSecsRemaining(data.time_remaining_seconds);
        }
        if (data.status === "closed" || data.status === "review" || data.time_remaining_seconds === 0) {
          clearInterval(timerRef.current);
          clearInterval(pollRef.current);
          onClosed();
        }
      } catch (_) {}
    }
    poll();
    pollRef.current = setInterval(poll, 3000);
    return () => clearInterval(pollRef.current);
  }, [code, onClosed]);

  async function handleEndQuiz() {
    if (!window.confirm("End the quiz now for all students?")) return;
    try {
      await closeQuiz(code);
      clearInterval(timerRef.current);
      clearInterval(pollRef.current);
      onClosed();
    } catch (e) {
      alert("Error ending quiz.");
    }
  }

  const isUrgent = secsRemaining <= 60;
  const s = stats || {};
  const dist = s.score_distribution || Array(10).fill(0);
  const maxBin = Math.max(...dist, 1);
  const totalEnrolled = s.total_enrolled || meta?.total_enrolled || 1;
  const submittedCount = s.submitted_count || 0;

  return (
    <div style={I.page}>
      <div style={{ ...I.hdr, background: isUrgent ? "#b71c1c" : "#1a1a1a" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span style={I.logo}>AutoTA</span>
          <span style={I.sep}>·</span>
          <span style={I.course}>{meta?.assignment_title || "Quiz"}</span>
          <span style={I.sep}>·</span>
          <span style={{ color: "#4CAF50", fontWeight: 700 }}>● LIVE</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <span style={{
            fontSize: 28, fontWeight: 700, fontFamily: "'IBM Plex Mono', monospace",
            color: isUrgent ? "#FFCDD2" : "#fff",
          }}>
            {fmt(secsRemaining)}
          </span>
          <button style={I.endBtn} onClick={handleEndQuiz}>End Quiz</button>
        </div>
      </div>
      <div style={I.content}>
        {/* Live stats row */}
        <div style={I.liveRow}>
          <div style={I.liveCard}>
            <p style={I.liveNum}>
              {submittedCount}
              <span style={{ fontSize: 18, color: "#888" }}>/{totalEnrolled}</span>
            </p>
            <p style={I.liveLbl}>Submitted</p>
            <div style={I.miniBar}>
              <div style={{ ...I.miniFill, width: `${(submittedCount / totalEnrolled) * 100}%` }} />
            </div>
          </div>
          <div style={I.liveCard}>
            <p style={I.liveNum}>{s.retry_count ?? 0}</p>
            <p style={I.liveLbl}>Retries</p>
            <p style={{ fontSize: 11, color: "#aaa", margin: "4px 0 0" }}>
              {submittedCount > 0 ? Math.round((s.retry_count || 0) / submittedCount * 100) : 0}% retried
            </p>
          </div>
          <div style={I.liveCard}>
            <p style={I.liveNum}>
              {submittedCount > 0 ? `${Math.round((s.avg_best_score || 0) * 100)}%` : "—"}
            </p>
            <p style={I.liveLbl}>Avg Best</p>
            {s.avg_first_score > 0 && (
              <p style={{ fontSize: 11, color: "#aaa", margin: "4px 0 0" }}>
                First: {Math.round(s.avg_first_score * 100)}%
              </p>
            )}
          </div>
          <div style={I.liveCard}>
            <p style={I.liveNum}>{totalEnrolled - submittedCount}</p>
            <p style={I.liveLbl}>Still Working</p>
          </div>
        </div>

        <div style={{ display: "flex", gap: 16, marginBottom: 20, flexWrap: "wrap" }}>
          {/* Score distribution */}
          <div style={{ ...I.card, flex: "1 1 300px" }}>
            <p style={I.cardTitle}>Live Score Distribution (Best Attempts)</p>
            <div style={{ display: "flex", alignItems: "flex-end", gap: 4, height: 100 }}>
              {dist.map((c, i) => (
                <div key={i} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center" }}>
                  <span style={{ fontSize: 10, color: "#666", marginBottom: 2 }}>{c || ""}</span>
                  <div style={{
                    width: "100%", borderRadius: "3px 3px 0 0",
                    height: `${Math.max(3, (c / maxBin) * 80)}px`,
                    background: i >= 8 ? "#2774AE" : i >= 5 ? "#64B5F6" : i >= 3 ? "#FFD54F" : "#EF9A9A",
                    transition: "height 0.5s ease",
                  }} />
                  <span style={{ fontSize: 9, color: "#999", marginTop: 3 }}>{i * 10}%</span>
                </div>
              ))}
            </div>
          </div>

          {/* Recent activity */}
          <div style={{ ...I.card, flex: "1 1 240px" }}>
            <p style={I.cardTitle}>Recent Activity</p>
            <div style={{ maxHeight: 120, overflow: "auto" }}>
              {(s.recent_submissions || []).map((sub, i) => (
                <div key={i} style={{
                  display: "flex", justifyContent: "space-between",
                  padding: "4px 0", borderBottom: "1px solid #f5f5f5", fontSize: 12,
                }}>
                  <span style={{ color: "#333" }}>
                    {sub.name}
                    {sub.is_retry && (
                      <span style={{ fontSize: 10, color: "#7B1FA2", fontWeight: 600, marginLeft: 4 }}>RETRY</span>
                    )}
                  </span>
                  <ScoreCell score={sub.score} />
                </div>
              ))}
              {(s.recent_submissions || []).length === 0 && (
                <p style={{ fontSize: 12, color: "#aaa", textAlign: "center", padding: "16px 0" }}>
                  No submissions yet
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Haven't submitted yet */}
        <div style={I.card}>
          <p style={I.cardTitle}>
            Haven't Submitted Yet ({s.not_submitted_count ?? totalEnrolled - submittedCount})
          </p>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
            {(s.not_submitted || []).slice(0, 40).map((st, i) => (
              <span key={i} style={{
                fontSize: 11, padding: "3px 8px",
                background: "#f5f5f5", borderRadius: 4, color: "#666",
              }}>
                {st.name}
              </span>
            ))}
            {(s.not_submitted_count || 0) > 40 && (
              <span style={{ fontSize: 11, padding: "3px 8px", color: "#999" }}>
                +{s.not_submitted_count - 40} more
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Closed / Review screens ───────────────────────────────────────────────────

function QuizClosedReview({ code, initialStatus, meta }) {
  const [status, setStatus] = useState(initialStatus || "closed");
  const [results, setResults] = useState(null);
  const [settingReview, setSettingReview] = useState(false);

  useEffect(() => {
    getResults(code).then(setResults).catch(() => {});
  }, [code]);

  async function handleShowSolutions() {
    setSettingReview(true);
    try {
      await setReview(code);
      setStatus("review");
    } catch (_) {}
    finally { setSettingReview(false); }
  }

  const r = results || {};
  const dist = (() => {
    // reconstruct from results if we have per-student data
    return Array(10).fill(0); // server doesn't return dist in results; that's OK for closed view
  })();

  const fDist = dist;
  const fMax = Math.max(...fDist, 1);
  const submitted = r.submitted_count || 0;
  const totalEnrolled = meta?.total_enrolled || 0;

  return (
    <div style={I.page}>
      <div style={I.hdr}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span style={I.logo}>AutoTA</span>
          <span style={I.sep}>·</span>
          <span style={I.course}>{meta?.assignment_title || "Quiz"}</span>
          <span style={I.sep}>·</span>
          <span style={{ color: status === "review" ? "#FFD54F" : "#EF9A9A", fontWeight: 700 }}>
            {status === "review" ? "REVIEW" : "ENDED"}
          </span>
        </div>
        {status === "closed" && (
          <button
            style={{ ...I.reviewBtn, opacity: settingReview ? 0.6 : 1 }}
            onClick={handleShowSolutions}
            disabled={settingReview}
          >
            Show Solutions →
          </button>
        )}
      </div>
      <div style={I.content}>
        {/* Final stats row */}
        <div style={I.liveRow}>
          <div style={I.liveCard}>
            <p style={I.liveNum}>{submitted}<span style={{ fontSize: 18, color: "#888" }}>/{totalEnrolled}</span></p>
            <p style={I.liveLbl}>Submitted</p>
          </div>
          <div style={I.liveCard}>
            <p style={I.liveNum}>{submitted > 0 ? `${Math.round((r.avg_best_score || 0) * 100)}%` : "—"}</p>
            <p style={I.liveLbl}>Avg Best</p>
            {r.avg_first_score > 0 && (
              <p style={{ fontSize: 11, color: "#aaa", margin: "4px 0 0" }}>
                First avg: {Math.round(r.avg_first_score * 100)}%
              </p>
            )}
          </div>
          <div style={I.liveCard}>
            <p style={I.liveNum}>{submitted > 0 ? `${Math.round((r.median_best_score || 0) * 100)}%` : "—"}</p>
            <p style={I.liveLbl}>Median</p>
          </div>
          <div style={I.liveCard}>
            <p style={I.liveNum}>{r.retry_count || 0}</p>
            <p style={I.liveLbl}>Retried</p>
            <p style={{ fontSize: 11, color: "#2e7d32", margin: "4px 0 0" }}>
              {Math.round((r.improvement_rate || 0) * 100)}% improved
            </p>
          </div>
        </div>

        {/* Review: per-problem breakdown */}
        {status === "review" && (r.problems || []).map(p => {
          const pct = Math.round((p.pct_correct || 0) * 100);
          return (
            <div key={p.id} style={{ ...I.card, marginBottom: 16 }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 12 }}>
                <div>
                  <span style={{ fontSize: 16, fontWeight: 700, color: "#2774AE", marginRight: 8 }}>{p.label}</span>
                  <span style={{ fontSize: 13, color: "#999" }}>{p.points} pts</span>
                </div>
                <span style={{ fontSize: 13, color: "#888" }}>
                  {p.correct_count}/{submitted} correct ({pct}%)
                </span>
              </div>
              <p style={{ fontSize: 14, color: "#333", margin: "0 0 8px", lineHeight: 1.5 }}>{p.text}</p>

              {/* Minterms */}
              <div style={{ background: "#f0f7ff", borderRadius: 6, padding: "10px 14px", marginBottom: 10 }}>
                <p style={{ fontSize: 11, fontWeight: 700, color: "#999", margin: "0 0 4px", textTransform: "uppercase" }}>Minterms</p>
                <p style={{ fontSize: 14, fontFamily: "'IBM Plex Mono', monospace", color: "#333", margin: 0 }}>
                  {p.minterms || "—"}
                </p>
                {p.dont_cares && (
                  <>
                    <p style={{ fontSize: 11, fontWeight: 700, color: "#999", margin: "8px 0 4px", textTransform: "uppercase" }}>Don't-cares</p>
                    <p style={{ fontSize: 14, fontFamily: "'IBM Plex Mono', monospace", color: "#333", margin: 0 }}>{p.dont_cares}</p>
                  </>
                )}
              </div>

              {/* Correct answer */}
              <div style={{ background: "#e8f5e9", borderRadius: 6, padding: "10px 14px", marginBottom: 10 }}>
                <p style={{ fontSize: 11, fontWeight: 700, color: "#2e7d32", margin: "0 0 4px", textTransform: "uppercase" }}>
                  Correct Answer
                </p>
                <p style={{ fontSize: 18, fontFamily: "'IBM Plex Mono', monospace", fontWeight: 700, color: "#2e7d32", margin: 0 }}>
                  {p.correct_answer || "—"}
                </p>
              </div>

              {/* Common wrong answers */}
              {p.common_errors?.length > 0 && (
                <div>
                  <p style={{ fontSize: 12, fontWeight: 700, color: "#999", margin: "0 0 6px", textTransform: "uppercase" }}>
                    Common Wrong Answers
                  </p>
                  {p.common_errors.map((err, i) => (
                    <div key={i} style={{
                      display: "flex", justifyContent: "space-between",
                      padding: "4px 8px", background: i % 2 === 0 ? "#fff" : "#fafafa",
                      borderRadius: 4, marginBottom: 2,
                    }}>
                      <span style={{ fontSize: 13, fontFamily: "'IBM Plex Mono', monospace", color: "#c62828" }}>
                        {err.answer}
                      </span>
                      <span style={{ fontSize: 12, color: "#999" }}>{err.count} students</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}

        {status === "closed" && !results && (
          <div style={{ ...I.card, textAlign: "center", color: "#888" }}>Loading results…</div>
        )}
      </div>
    </div>
  );
}

// ── Root controller ───────────────────────────────────────────────────────────

export default function InstructorQuiz({ code }) {
  const [meta, setMeta] = useState(null);
  const [screen, setScreen] = useState(null); // pending | active | closed | review | loading | error

  useEffect(() => {
    getQuizMeta(code)
      .then(data => {
        setMeta(data);
        setScreen(data.status);
      })
      .catch(() => setScreen("error"));
  }, [code]);

  if (!screen || screen === "loading") {
    return (
      <div style={{ ...I.page, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <p style={{ color: "#888" }}>Loading quiz…</p>
      </div>
    );
  }

  if (screen === "error") {
    return (
      <div style={{ ...I.page, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <div style={{ textAlign: "center" }}>
          <h2 style={{ color: "#c62828" }}>Quiz Not Found</h2>
          <p style={{ color: "#888" }}>Check the quiz code and try again.</p>
        </div>
      </div>
    );
  }

  if (screen === "pending") {
    return (
      <QuizPending
        meta={meta}
        code={code}
        onStarted={() => {
          // Re-fetch meta to get started_at / time_remaining
          getQuizMeta(code).then(d => {
            setMeta(d);
            setScreen("active");
          });
        }}
      />
    );
  }

  if (screen === "active") {
    return (
      <QuizLive
        code={code}
        meta={meta}
        onClosed={() => {
          getQuizMeta(code).then(d => {
            setMeta(d);
            setScreen("closed");
          });
        }}
      />
    );
  }

  // closed or review
  return <QuizClosedReview code={code} initialStatus={screen} meta={meta} />;
}
