/**
 * QuizApp — student-facing quiz UI
 * Route: /quiz/:code?sid=UID...
 * Mobile-first, matches docs/autota-quiz-prototype.jsx exactly.
 */
import { useState, useEffect, useRef, useCallback } from "react";
import { joinQuiz, pollQuizStatus, submitQuiz } from "./quizApi";

// ── Style objects (M = mobile) ────────────────────────────────────────────────
const M = {
  page: {
    minHeight: "100vh",
    background: "#f5f5f5",
    fontFamily: "'IBM Plex Sans', -apple-system, BlinkMacSystemFont, sans-serif",
    maxWidth: "100vw",
    overflowX: "hidden",
  },
  topBar: {
    display: "flex", justifyContent: "space-between", alignItems: "center",
    padding: "10px 16px", background: "#2774AE", color: "#fff",
  },
  topLogo: { fontSize: 15, fontWeight: 700 },
  topCourse: { fontSize: 12, color: "rgba(255,255,255,0.8)" },
  entryContainer: {
    display: "flex", flexDirection: "column", alignItems: "center",
    padding: "60px 24px",
  },
  codeInput: {
    fontSize: 28, fontWeight: 700,
    fontFamily: "'IBM Plex Mono', monospace",
    textAlign: "center", padding: "12px 20px",
    border: "2px solid #2774AE", borderRadius: 10, outline: "none",
    width: 200, letterSpacing: "0.1em", color: "#1a1a1a", boxSizing: "border-box",
  },
  joinBtn: {
    marginTop: 20, padding: "14px 40px",
    background: "#2774AE", color: "#fff", border: "none",
    borderRadius: 10, fontSize: 16, fontWeight: 600, cursor: "pointer",
    width: 240, minHeight: 44,
  },
  timerBar: {
    display: "flex", justifyContent: "space-between", alignItems: "center",
    padding: "10px 16px", color: "#fff",
    position: "sticky", top: 0, zIndex: 10,
  },
  bestBanner: {
    display: "flex", justifyContent: "space-between", alignItems: "center",
    padding: "8px 16px", background: "#E8F5E9", fontSize: 13, color: "#2e7d32",
  },
  progressDots: {
    display: "flex", justifyContent: "center", gap: 8, padding: "12px 16px",
    background: "#fff", borderBottom: "1px solid #e8e8e8",
  },
  dot: {
    width: 40, height: 40, borderRadius: 20, border: "none",
    fontSize: 12, fontWeight: 700, cursor: "pointer",
    display: "flex", alignItems: "center", justifyContent: "center",
    minHeight: 44,
  },
  questionArea: { padding: "16px 16px 100px" },
  mintermBox: {
    background: "#f0f7ff", borderRadius: 8,
    padding: "12px 14px", marginBottom: 16,
  },
  mintermLabel: {
    fontSize: 11, fontWeight: 700, color: "#999",
    textTransform: "uppercase", margin: "0 0 4px",
  },
  mintermVal: {
    fontSize: 15, fontFamily: "'IBM Plex Mono', monospace",
    color: "#1a1a1a", margin: "0 0 8px", fontWeight: 600,
  },
  answerInput: {
    width: "100%", boxSizing: "border-box", padding: "12px 14px",
    fontSize: 16, fontFamily: "'IBM Plex Mono', monospace",
    border: "2px solid #d0d0d0", borderRadius: 8, outline: "none",
    resize: "none", marginBottom: 8,
  },
  checkBtn: {
    flex: 1, padding: "12px", background: "#f5f5f5", color: "#333",
    border: "1px solid #d0d0d0", borderRadius: 8, fontSize: 14,
    fontWeight: 500, cursor: "pointer", minHeight: 44,
  },
  nextBtn: {
    flex: 1, padding: "12px", background: "#2774AE", color: "#fff",
    border: "none", borderRadius: 8, fontSize: 14,
    fontWeight: 600, cursor: "pointer", minHeight: 44,
  },
  submitBtn: {
    flex: 1, padding: "12px", background: "#2e7d32", color: "#fff",
    border: "none", borderRadius: 8, fontSize: 14,
    fontWeight: 600, cursor: "pointer", minHeight: 44,
  },
  retryBtn: {
    padding: "14px 32px", background: "#2774AE", color: "#fff",
    border: "none", borderRadius: 10, fontSize: 15, fontWeight: 600,
    cursor: "pointer", minHeight: 44,
  },
  backLink: {
    display: "block", marginTop: 12, background: "none", border: "none",
    color: "#2774AE", fontSize: 13, fontWeight: 600, cursor: "pointer", padding: 0,
  },
  overlay: {
    position: "fixed", top: 0, left: 0, right: 0, bottom: 0,
    background: "rgba(0,0,0,0.5)", display: "flex",
    alignItems: "center", justifyContent: "center", zIndex: 50,
  },
  confirmBox: {
    background: "#fff", borderRadius: 12, padding: "24px",
    maxWidth: 320, width: "90%", textAlign: "center",
  },
  confirmCancel: {
    flex: 1, padding: "10px", background: "#f5f5f5", color: "#333",
    border: "1px solid #d0d0d0", borderRadius: 8, fontSize: 14,
    fontWeight: 500, cursor: "pointer", minHeight: 44,
  },
  confirmSubmit: {
    flex: 1, padding: "10px", background: "#2e7d32", color: "#fff",
    border: "none", borderRadius: 8, fontSize: 14,
    fontWeight: 600, cursor: "pointer", minHeight: 44,
  },
  resultContainer: {
    display: "flex", flexDirection: "column", alignItems: "center",
    padding: "40px 24px", textAlign: "center",
  },
  bestScoreBadge: {
    display: "flex", flexDirection: "column", alignItems: "center",
    gap: 2, marginTop: 12, padding: "16px 24px",
    background: "#f8f8f8", borderRadius: 12,
  },
};

// ── Helpers ───────────────────────────────────────────────────────────────────

function fmt(s) {
  if (s === null || s === undefined) return "--:--";
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}

function ScoreCell({ score }) {
  if (score === null || score === undefined) return <span style={{ color: "#ccc" }}>—</span>;
  const pct = Math.round(score * 100);
  const bg = pct >= 80 ? "#e8f5e9" : pct >= 50 ? "#fff8e1" : "#ffebee";
  const color = pct >= 80 ? "#2e7d32" : pct >= 50 ? "#f57f17" : "#c62828";
  return (
    <span style={{
      background: bg, color, padding: "2px 8px", borderRadius: 4,
      fontSize: 13, fontWeight: 600,
      fontFamily: "'IBM Plex Mono', monospace",
    }}>
      {pct}%
    </span>
  );
}

// TODO: Replace with server-side format validation once answer correctness is
// fully integrated. Current check is purely syntactic (character whitelist +
// balanced parens) and does not verify logical equivalence or canonical form.
function checkFormat(answer) {
  if (!answer.trim()) return { ok: false, msg: "No answer entered." };
  const invalid = answer.replace(/[A-Da-d'()+\s·*01]/g, "");
  if (invalid) return { ok: false, msg: `Invalid characters: "${invalid}"` };
  const open = (answer.match(/\(/g) || []).length;
  const close = (answer.match(/\)/g) || []).length;
  if (open !== close) return { ok: false, msg: "Mismatched parentheses." };
  return { ok: true, msg: "Format looks good ✓" };
}

// ── Entry screen ──────────────────────────────────────────────────────────────

function QuizEntry({ urlCode, studentId, onJoined, onError }) {
  const [code, setCode] = useState(urlCode || "");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  // Auto-join if code already in URL
  useEffect(() => {
    if (urlCode && studentId) {
      handleJoin(urlCode);
    }
  }, []); // eslint-disable-line

  async function handleJoin(c) {
    const cleaned = (c || code).toUpperCase().replace(/[^A-Z0-9]/g, "");
    if (cleaned.length < 4) { setError("Code too short."); return; }
    setLoading(true);
    setError("");
    try {
      const data = await joinQuiz(cleaned, studentId);
      onJoined(cleaned, data);
    } catch (e) {
      if (e.status === 403) setError("This quiz is already closed.");
      else if (e.status === 404) setError("Invalid quiz code. Check the code on screen.");
      else setError("Could not connect to server. Try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={M.page}>
      <div style={M.topBar}>
        <span style={M.topLogo}>AutoTA</span>
        <span style={M.topCourse}>ECE M16</span>
      </div>
      <div style={M.entryContainer}>
        <div style={{ fontSize: 48, marginBottom: 16 }}>📝</div>
        <h1 style={{ fontSize: 24, fontWeight: 700, margin: "0 0 8px", color: "#1a1a1a" }}>Join Quiz</h1>
        <p style={{ fontSize: 14, color: "#888", margin: "0 0 24px" }}>
          Enter the code shown on the projector
        </p>
        <input
          style={M.codeInput}
          value={code}
          onChange={e => { setCode(e.target.value.toUpperCase()); setError(""); }}
          placeholder="QZ5A3F"
          maxLength={8}
          autoFocus
          onKeyDown={e => e.key === "Enter" && handleJoin()}
        />
        {error && <p style={{ fontSize: 13, color: "#c62828", margin: "8px 0 0" }}>{error}</p>}
        {!studentId && (
          <p style={{ fontSize: 12, color: "#c62828", margin: "8px 0 0" }}>
            ⚠ No student ID — append ?sid=UID... to the URL
          </p>
        )}
        <button
          style={{ ...M.joinBtn, opacity: (code.length < 4 || loading || !studentId) ? 0.5 : 1 }}
          onClick={() => handleJoin()}
          disabled={code.length < 4 || loading || !studentId}
        >
          {loading ? "Joining…" : "Join Quiz →"}
        </button>
        <p style={{ fontSize: 12, color: "#aaa", marginTop: 16 }}>Or scan the QR code on screen</p>
      </div>
    </div>
  );
}

// ── Waiting screen ────────────────────────────────────────────────────────────

function QuizWaiting({ code, quizTitle, onActive, onClosed }) {
  useEffect(() => {
    const id = setInterval(async () => {
      try {
        const data = await pollQuizStatus(code);
        if (data.status === "active") onActive(data.time_remaining_seconds);
        else if (data.status === "closed" || data.status === "review") onClosed();
      } catch (_) {}
    }, 2000);
    return () => clearInterval(id);
  }, [code, onActive, onClosed]);

  return (
    <div style={M.page}>
      <div style={M.topBar}>
        <span style={M.topLogo}>AutoTA</span>
        <span style={M.topCourse}>ECE M16</span>
      </div>
      <div style={M.entryContainer}>
        <div style={{ fontSize: 48, marginBottom: 16 }}>⏳</div>
        <h1 style={{ fontSize: 22, fontWeight: 700, margin: "0 0 8px", color: "#1a1a1a" }}>
          Waiting for quiz to start…
        </h1>
        <p style={{ fontSize: 14, color: "#888", margin: "0 0 20px" }}>{quizTitle}</p>
        <div style={{
          background: "#f0f7ff", borderRadius: 10, padding: "14px 24px",
          fontFamily: "'IBM Plex Mono', monospace", fontSize: 28, fontWeight: 700,
          color: "#2774AE", letterSpacing: "0.1em",
        }}>
          {code}
        </div>
        <p style={{ fontSize: 12, color: "#aaa", marginTop: 20 }}>
          This page will update automatically when the instructor starts the quiz.
        </p>
      </div>
    </div>
  );
}

// ── Active answering + result + closed ────────────────────────────────────────

function QuizActive({ code, studentId, problems, initialSecsRemaining, initialBestScores }) {
  const [answers, setAnswers] = useState({});
  const [currentQ, setCurrentQ] = useState(0);
  const [secsRemaining, setSecsRemaining] = useState(initialSecsRemaining ?? 600);
  const [quizOpen, setQuizOpen] = useState(true);
  const [showConfirm, setShowConfirm] = useState(false);
  const [formatMsg, setFormatMsg] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [attempts, setAttempts] = useState(0);
  const [bestScores, setBestScores] = useState(initialBestScores || {}); // {pid: score}
  const [bestScoreDetails, setBestScoreDetails] = useState({}); // {pid: {score,correct,feedback}}
  const [bestTotal, setBestTotal] = useState(null);
  const [lastResult, setLastResult] = useState(null);
  const [showResult, setShowResult] = useState(false);
  const timerRef = useRef(null);

  // Server-authoritative countdown: tick client-side, resync via poll
  useEffect(() => {
    timerRef.current = setInterval(() => {
      setSecsRemaining(t => {
        if (t <= 1) { clearInterval(timerRef.current); setQuizOpen(false); return 0; }
        return t - 1;
      });
    }, 1000);
    return () => clearInterval(timerRef.current);
  }, []);

  // Poll server every 10s to re-sync remaining time
  useEffect(() => {
    const id = setInterval(async () => {
      try {
        const data = await pollQuizStatus(code);
        if (data.status === "closed" || data.status === "review") {
          clearInterval(timerRef.current);
          setQuizOpen(false);
          setSecsRemaining(0);
        } else if (data.time_remaining_seconds !== null) {
          setSecsRemaining(data.time_remaining_seconds);
        }
      } catch (_) {}
    }, 10000);
    return () => clearInterval(id);
  }, [code]);

  const handleSubmit = useCallback(async () => {
    setShowConfirm(false);
    setSubmitting(true);
    try {
      const result = await submitQuiz(code, studentId, answers);
      setLastResult(result);
      setAttempts(result.attempt_number);
      setBestScores(result.best_scores);
      setBestScoreDetails(result.best_score_details || {});
      setBestTotal(result.best_total_score);
      // Resync timer
      if (result.time_remaining_seconds !== null) {
        setSecsRemaining(result.time_remaining_seconds);
      }
      setShowResult(true);
    } catch (e) {
      if (e.status === 403 || e.message === "quiz_closed") {
        clearInterval(timerRef.current);
        setQuizOpen(false);
      } else {
        alert("Submission error. Check connection and try again.");
      }
    } finally {
      setSubmitting(false);
    }
  }, [code, studentId, answers]);

  const tryAgain = () => { setShowResult(false); setCurrentQ(0); setFormatMsg(null); };
  const isUrgent = secsRemaining <= 60;
  const p = problems[currentQ];
  const totalPts = problems.reduce((s, pr) => s + pr.points, 0);

  // ── TIME'S UP ──
  if (!quizOpen) {
    return (
      <div style={M.page}>
        <div style={{ ...M.timerBar, background: "#333" }}>
          <span style={{ fontSize: 13, fontWeight: 500 }}>Quiz Closed</span>
          <span style={{ fontSize: 14, fontWeight: 600, color: "#EF9A9A" }}>TIME'S UP</span>
        </div>
        <div style={M.resultContainer}>
          <div style={{ fontSize: 48, marginBottom: 12 }}>⏰</div>
          <h2 style={{ fontSize: 20, fontWeight: 700, margin: "0 0 4px", color: "#1a1a1a" }}>Quiz Closed</h2>
          {bestTotal !== null ? (
            <>
              <div style={M.bestScoreBadge}>
                <span style={{ fontSize: 11, color: "#888" }}>Your Best Score</span>
                <span style={{
                  fontSize: 32, fontWeight: 700,
                  color: bestTotal >= 0.8 ? "#2e7d32" : bestTotal >= 0.5 ? "#F57F17" : "#c62828",
                  fontFamily: "'IBM Plex Mono', monospace",
                }}>
                  {Math.round(bestTotal * 100)}%
                </span>
                <span style={{ fontSize: 12, color: "#999" }}>{attempts} attempt{attempts !== 1 ? "s" : ""}</span>
              </div>
              <div style={{ width: "100%", maxWidth: 340, marginTop: 16 }}>
                {problems.map(prob => (
                  <div key={prob.id} style={{
                    display: "flex", justifyContent: "space-between", alignItems: "center",
                    padding: "10px 0", borderBottom: "1px solid #f0f0f0",
                  }}>
                    <div>
                      <span style={{ fontSize: 14, fontWeight: 600, color: "#2774AE" }}>{prob.label}</span>
                      <span style={{ fontSize: 12, color: "#999", marginLeft: 6 }}>{prob.points} pts</span>
                    </div>
                    <ScoreCell score={bestScores[prob.id] ?? null} />
                  </div>
                ))}
              </div>
            </>
          ) : (
            <p style={{ fontSize: 14, color: "#c62828", marginTop: 12 }}>You didn't submit any answers.</p>
          )}
          <p style={{ fontSize: 13, color: "#aaa", marginTop: 20 }}>
            Your instructor will review the solutions now.
          </p>
        </div>
      </div>
    );
  }

  // ── RESULT VIEW ──
  if (showResult && lastResult) {
    const thisTotal = lastResult.total_score;
    return (
      <div style={M.page}>
        <div style={{ ...M.timerBar, background: isUrgent ? "#c62828" : "#2774AE" }}>
          <span style={{ fontSize: 13, fontWeight: 500 }}>Attempt {attempts} Result</span>
          <span style={{ fontSize: 18, fontWeight: 700, fontFamily: "'IBM Plex Mono', monospace" }}>
            {fmt(secsRemaining)}
          </span>
        </div>
        <div style={M.resultContainer}>
          <div style={{ fontSize: 48, marginBottom: 8 }}>
            {thisTotal >= 0.8 ? "🎉" : thisTotal >= 0.5 ? "📊" : "💪"}
          </div>
          <p style={{ fontSize: 13, color: "#888", margin: "0 0 4px" }}>This Attempt</p>
          <p style={{
            fontSize: 36, fontWeight: 700, fontFamily: "'IBM Plex Mono', monospace",
            margin: "0 0 8px",
            color: thisTotal >= 0.8 ? "#2e7d32" : thisTotal >= 0.5 ? "#F57F17" : "#c62828",
          }}>
            {Math.round(thisTotal * 100)}%
          </p>
          {bestTotal !== null && bestTotal > thisTotal && (
            <p style={{ fontSize: 14, color: "#2e7d32", fontWeight: 600, margin: "0 0 12px" }}>
              ✓ Best score: {Math.round(bestTotal * 100)}%
            </p>
          )}
          <div style={{ width: "100%", maxWidth: 340, marginBottom: 20 }}>
            {problems.map(prob => {
              const res = lastResult.scores[prob.id];
              const best = bestScoreDetails[prob.id];
              return (
                <div key={prob.id} style={{ padding: "12px 0", borderBottom: "1px solid #f0f0f0" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
                    <div>
                      <span style={{ fontSize: 14, fontWeight: 600, color: "#2774AE" }}>{prob.label}</span>
                      <span style={{ fontSize: 12, color: "#999", marginLeft: 6 }}>{prob.points} pts</span>
                    </div>
                    <ScoreCell score={res?.score ?? null} />
                  </div>
                  <p style={{ fontSize: 13, color: res?.correct ? "#2e7d32" : "#888", margin: "2px 0 0" }}>
                    {res?.feedback}
                  </p>
                  {best && res && best.score > res.score && (
                    <p style={{ fontSize: 12, color: "#2e7d32", margin: "2px 0 0" }}>
                      Best: {Math.round(best.score * 100)}%
                    </p>
                  )}
                </div>
              );
            })}
          </div>
          {thisTotal < 1.0 ? (
            <div style={{ textAlign: "center" }}>
              <p style={{ fontSize: 14, color: "#333", margin: "0 0 12px", fontWeight: 500 }}>
                {secsRemaining > 30 ? "You can fix your answers and resubmit!" : "Hurry — less than 30 seconds left!"}
              </p>
              <button style={M.retryBtn} onClick={tryAgain}>✏️ Edit & Resubmit</button>
              <p style={{ fontSize: 12, color: "#aaa", marginTop: 8 }}>
                Best score is recorded · {fmt(secsRemaining)} remaining
              </p>
            </div>
          ) : (
            <div style={{ textAlign: "center" }}>
              <p style={{ fontSize: 16, color: "#2e7d32", fontWeight: 700, margin: "0 0 8px" }}>🎉 Perfect score!</p>
              <p style={{ fontSize: 13, color: "#888" }}>You can relax — your best score has been recorded.</p>
            </div>
          )}
        </div>
      </div>
    );
  }

  // ── ANSWERING VIEW ──
  return (
    <div style={M.page}>
      {/* Timer bar */}
      <div style={{ ...M.timerBar, background: isUrgent ? "#c62828" : "#2774AE" }}>
        <span style={{ fontSize: 13, fontWeight: 500 }}>
          {problems[0]?.quizTitle || "Quiz"}{attempts > 0 ? ` · Attempt ${attempts + 1}` : ""}
        </span>
        <span style={{ fontSize: 18, fontWeight: 700, fontFamily: "'IBM Plex Mono', monospace" }}>
          {fmt(secsRemaining)}
        </span>
      </div>

      {/* Best score banner (after first submit) */}
      {bestTotal !== null && (
        <div style={M.bestBanner}>
          <span>Current best: <strong>{Math.round(bestTotal * 100)}%</strong></span>
          <span style={{ fontSize: 11, color: "#888" }}>Best score is kept</span>
        </div>
      )}

      {/* Progress dots */}
      <div style={M.progressDots}>
        {problems.map((prob, i) => {
          const isPerfect = (bestScores[prob.id] ?? 0) >= 1.0;
          const hasAnswer = !!answers[prob.id];
          return (
            <button
              key={prob.id}
              onClick={() => { setCurrentQ(i); setFormatMsg(null); }}
              style={{
                ...M.dot,
                background: i === currentQ ? "#2774AE" : isPerfect ? "#4CAF50" : hasAnswer ? "#64B5F6" : "#e0e0e0",
                color: (i === currentQ || isPerfect || hasAnswer) ? "#fff" : "#999",
              }}
            >
              {isPerfect ? "✓" : prob.label}
            </button>
          );
        })}
      </div>

      {/* Question area */}
      <div style={M.questionArea}>
        {/* Perfect banner */}
        {(bestScores[p.id] ?? 0) >= 1.0 && (
          <div style={{
            background: "#e8f5e9", borderRadius: 8, padding: "10px 14px",
            marginBottom: 12, display: "flex", alignItems: "center", gap: 8,
          }}>
            <span style={{ fontSize: 16 }}>✅</span>
            <span style={{ fontSize: 13, color: "#2e7d32", fontWeight: 600 }}>
              You already got this one right!
            </span>
          </div>
        )}

        {/* Previous best banner */}
        {bestScores[p.id] !== undefined && bestScores[p.id] < 1.0 && (
          <div style={{
            background: "#FFF8E1", borderRadius: 8, padding: "10px 14px",
            marginBottom: 12, display: "flex", justifyContent: "space-between", alignItems: "center",
          }}>
            <span style={{ fontSize: 13, color: "#F57F17" }}>
              Previous best: {Math.round(bestScores[p.id] * 100)}%
            </span>
            <span style={{ fontSize: 12, color: "#999" }}>Try to improve!</span>
          </div>
        )}

        {/* Problem header */}
        <div style={{ fontSize: 18, fontWeight: 700, color: "#2774AE", marginBottom: 8 }}>
          {p.label} <span style={{ fontWeight: 400, color: "#999" }}>· {p.points} pts</span>
        </div>
        <p style={{ fontSize: 14, color: "#333", lineHeight: 1.6, margin: "0 0 12px" }}>{p.text}</p>

        {/* Minterms box */}
        <div style={M.mintermBox}>
          <p style={M.mintermLabel}>Minterms</p>
          <p style={M.mintermVal}>{p.minterms || "—"}</p>
          {p.dont_cares && (
            <>
              <p style={M.mintermLabel}>Don't-cares</p>
              <p style={M.mintermVal}>{p.dont_cares}</p>
            </>
          )}
        </div>

        {/* Answer input */}
        <textarea
          style={M.answerInput}
          placeholder={p.placeholder || "e.g. A'B + CD'"}
          value={answers[p.id] || ""}
          onChange={e => { setAnswers({ ...answers, [p.id]: e.target.value }); setFormatMsg(null); }}
          rows={2}
        />
        {formatMsg && (
          <p style={{ fontSize: 13, color: formatMsg.ok ? "#2e7d32" : "#c62828", margin: "4px 0 0", fontWeight: 500 }}>
            {formatMsg.msg}
          </p>
        )}

        {/* Buttons */}
        <div style={{ display: "flex", gap: 10, marginTop: 8 }}>
          <button style={M.checkBtn} onClick={() => setFormatMsg(checkFormat(answers[p.id] || ""))}>
            Check Format
          </button>
          {currentQ < problems.length - 1 ? (
            <button style={M.nextBtn} onClick={() => { setCurrentQ(currentQ + 1); setFormatMsg(null); }}>
              Next →
            </button>
          ) : (
            <button
              style={{ ...M.submitBtn, opacity: submitting ? 0.6 : 1 }}
              onClick={() => setShowConfirm(true)}
              disabled={submitting}
            >
              {submitting ? "Grading…" : attempts > 0 ? "Resubmit" : "Submit Quiz"}
            </button>
          )}
        </div>
        {currentQ > 0 && (
          <button style={M.backLink} onClick={() => { setCurrentQ(currentQ - 1); setFormatMsg(null); }}>
            ← Previous
          </button>
        )}
      </div>

      {/* Confirm modal */}
      {showConfirm && (
        <div style={M.overlay}>
          <div style={M.confirmBox}>
            <h3 style={{ fontSize: 17, fontWeight: 700, margin: "0 0 8px" }}>
              {attempts > 0 ? "Resubmit?" : "Submit quiz?"}
            </h3>
            <p style={{ fontSize: 14, color: "#666", margin: "0 0 4px" }}>
              {problems.filter(pr => answers[pr.id]).length} of {problems.length} answered.
            </p>
            {problems.some(pr => !answers[pr.id]) && (
              <p style={{ fontSize: 13, color: "#c62828", margin: "0 0 8px", fontWeight: 500 }}>
                ⚠ Unanswered questions will score 0.
              </p>
            )}
            <p style={{ fontSize: 13, color: "#2e7d32", margin: "0 0 16px" }}>
              ✓ You'll see your score and can retry if time remains.
            </p>
            <div style={{ display: "flex", gap: 10 }}>
              <button style={M.confirmCancel} onClick={() => setShowConfirm(false)}>Go Back</button>
              <button style={M.confirmSubmit} onClick={handleSubmit}>
                {attempts > 0 ? "Resubmit" : "Submit"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ── QuizApp root ──────────────────────────────────────────────────────────────

export default function QuizApp({ code: urlCode, studentId }) {
  const [screen, setScreen] = useState("entry"); // entry | waiting | active | error
  const [quizCode, setQuizCode] = useState(urlCode || "");
  const [joinData, setJoinData] = useState(null);
  const [errorMsg, setErrorMsg] = useState("");

  function handleJoined(code, data) {
    setQuizCode(code);
    setJoinData(data);
    if (data.status === "active") setScreen("active");
    else if (data.status === "pending") setScreen("waiting");
    else setScreen("error");
  }

  if (screen === "error") {
    return (
      <div style={M.page}>
        <div style={M.topBar}><span style={M.topLogo}>AutoTA</span></div>
        <div style={M.entryContainer}>
          <div style={{ fontSize: 48, marginBottom: 12 }}>🚫</div>
          <h2 style={{ fontSize: 18, fontWeight: 700 }}>Quiz Not Available</h2>
          <p style={{ color: "#888" }}>{errorMsg || "This quiz is closed or unavailable."}</p>
        </div>
      </div>
    );
  }

  if (screen === "waiting") {
    return (
      <QuizWaiting
        code={quizCode}
        quizTitle={joinData?.quiz_title || "Quiz"}
        onActive={(secs) => {
          // Re-join to get problems freshly or use cached
          if (joinData?.problems?.length) {
            setJoinData(d => ({ ...d, status: "active", time_remaining_seconds: secs }));
            setScreen("active");
          } else {
            joinQuiz(quizCode, studentId).then(data => {
              setJoinData(data);
              setScreen("active");
            }).catch(() => setScreen("error"));
          }
        }}
        onClosed={() => setScreen("error")}
      />
    );
  }

  if (screen === "active" && joinData) {
    return (
      <QuizActive
        code={quizCode}
        studentId={studentId}
        problems={joinData.problems || []}
        initialSecsRemaining={joinData.time_remaining_seconds}
        initialBestScores={joinData.best_scores || {}}
      />
    );
  }

  return (
    <QuizEntry
      urlCode={urlCode}
      studentId={studentId}
      onJoined={handleJoined}
    />
  );
}
