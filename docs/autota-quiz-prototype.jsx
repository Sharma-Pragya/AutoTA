import { useState, useEffect, useRef, useMemo } from "react";

// ── MOCK DATA ──

const QUIZ = {
  id: "QZ-5A3F",
  title: "Quiz 3 — K-Map Simplification",
  course: "ECE M16",
  instructor: "Prof. Mani Srivastava",
  timeLimitSeconds: 600,
};

const QUIZ_PROBLEMS = [
  {
    id: "quiz3_1", label: "Q1", points: 10,
    text: "Simplify the Boolean function F(A,B,C,D) defined by the following minterms. Express your answer as a minimal sum-of-products (SOP).",
    minterms: "m(0, 2, 5, 7, 8, 10, 13, 15)", dont_cares: "d(1, 6)",
    answer_format: "boolean_expression", placeholder: "e.g. A'B + CD'",
    correct_answer: "B'D' + BD",
  },
  {
    id: "quiz3_2", label: "Q2", points: 10,
    text: "Find the minimal SOP expression for the following function.",
    minterms: "m(1, 3, 4, 5, 6, 7, 12, 14)", dont_cares: null,
    answer_format: "boolean_expression", placeholder: "e.g. A'C + B'D",
    correct_answer: "A'B + BC' + ACD'",
  },
];

const TOTAL_PTS = QUIZ_PROBLEMS.reduce((s, p) => s + p.points, 0);

function generateStudentSubmissions(count) {
  const firstNames = ["Alex","Ben","Carmen","Diana","Ethan","Fiona","George","Hannah","Ivan","Julia","Kevin","Lily","Marco","Nina","Oscar","Priya","Quinn","Rosa","Sam","Tara","Uma","Victor","Wendy","Xavier","Yuki","Zara"];
  const lastNames = ["Chen","Kim","Rivera","Patel","Park","Nguyen","Wu","Lee","Petrov","Santos","Tran","Zhang","Silva","Kowalski","Mendez","Gupta","O'Brien","Martinez","Nakamura","Singh","Reddy","Huang","Cho","Diaz","Tanaka","Ahmed"];
  const students = [];
  for (let i = 0; i < count; i++) {
    const fn = firstNames[i % firstNames.length];
    const ln = lastNames[i % lastNames.length];
    const name = `${fn} ${ln}`;
    const uid = `UID${String(100000000 + i).slice(0, 9)}`;
    const section = i % 2 === 0 ? "1A" : "1B";
    const ability = Math.random();
    const didSubmit = Math.random() < 0.92;
    const firstSubmitSec = didSubmit ? Math.floor(120 + Math.random() * 300) : null;
    const q1First = ability > 0.3 ? (Math.random() < 0.5 ? 1.0 : +(0.3 + Math.random() * 0.6).toFixed(2)) : +(Math.random() * 0.4).toFixed(2);
    const q2First = ability > 0.4 ? (Math.random() < 0.4 ? 1.0 : +(0.3 + Math.random() * 0.5).toFixed(2)) : +(Math.random() * 0.3).toFixed(2);
    const firstScore = (q1First * QUIZ_PROBLEMS[0].points + q2First * QUIZ_PROBLEMS[1].points) / TOTAL_PTS;
    const didRetry = didSubmit && firstScore < 1.0 && Math.random() < 0.6;
    const retrySubmitSec = didRetry ? Math.floor(firstSubmitSec + 60 + Math.random() * 180) : null;
    const q1Retry = didRetry ? Math.min(1.0, q1First + (1.0 - q1First) * (0.3 + Math.random() * 0.5)) : null;
    const q2Retry = didRetry ? Math.min(1.0, q2First + (1.0 - q2First) * (0.3 + Math.random() * 0.5)) : null;
    const retryScore = didRetry ? (q1Retry * QUIZ_PROBLEMS[0].points + q2Retry * QUIZ_PROBLEMS[1].points) / TOTAL_PTS : null;
    const bestScore = didRetry ? Math.max(firstScore, retryScore) : (didSubmit ? firstScore : null);
    const totalAttempts = didRetry ? 2 : (didSubmit ? 1 : 0);
    const wrongAnswers = [["AB + CD", "A'B", "BD + AC", "B'D"], ["AB' + C", "A'C + BD", "BC + AD'"]];
    students.push({
      name, uid, section, didSubmit,
      firstSubmitSec, retrySubmitSec,
      firstScore: didSubmit ? +firstScore.toFixed(3) : null,
      bestScore: bestScore !== null ? +bestScore.toFixed(3) : null,
      totalAttempts,
      answers: didSubmit ? {
        quiz3_1: { answer: q1First === 1.0 ? "B'D' + BD" : wrongAnswers[0][Math.floor(Math.random()*4)], score: q1First, bestScore: didRetry ? q1Retry : q1First },
        quiz3_2: { answer: q2First === 1.0 ? "A'B + BC' + ACD'" : wrongAnswers[1][Math.floor(Math.random()*3)], score: q2First, bestScore: didRetry ? q2Retry : q2First },
      } : null,
    });
  }
  return students;
}

const ALL_STUDENTS = generateStudentSubmissions(200);

// ── SHARED ──

function ScoreCell({ score }) {
  if (score === null || score === undefined) return <span style={{ color: "#ccc" }}>—</span>;
  const pct = Math.round(score * 100);
  const bg = pct >= 80 ? "#e8f5e9" : pct >= 50 ? "#fff8e1" : "#ffebee";
  const color = pct >= 80 ? "#2e7d32" : pct >= 50 ? "#f57f17" : "#c62828";
  return <span style={{ background: bg, color, padding: "2px 8px", borderRadius: 4, fontSize: 13, fontWeight: 600, fontFamily: "'IBM Plex Mono', monospace" }}>{pct}%</span>;
}

// ── STUDENT MOBILE VIEW ──

function StudentQuizEntry({ onJoin }) {
  const [code, setCode] = useState("");
  const [error, setError] = useState("");
  const handleJoin = () => {
    const cleaned = code.toUpperCase().replace(/[^A-Z0-9]/g, "");
    if (cleaned === "QZ5A3F") onJoin();
    else setError("Invalid quiz code. Check the code on screen.");
  };
  return (
    <div style={M.page}>
      <div style={M.topBar}><span style={M.topLogo}>AutoTA</span><span style={M.topCourse}>ECE M16</span></div>
      <div style={M.entryContainer}>
        <div style={{ fontSize: 48, marginBottom: 16 }}>📝</div>
        <h1 style={{ fontSize: 24, fontWeight: 700, margin: "0 0 8px", color: "#1a1a1a" }}>Join Quiz</h1>
        <p style={{ fontSize: 14, color: "#888", margin: "0 0 24px" }}>Enter the code shown on the projector</p>
        <input style={M.codeInput} value={code} onChange={e => { setCode(e.target.value.toUpperCase()); setError(""); }} placeholder="QZ-5A3F" maxLength={8} autoFocus />
        {error && <p style={{ fontSize: 13, color: "#c62828", margin: "8px 0 0" }}>{error}</p>}
        <button style={{ ...M.joinBtn, opacity: code.length < 4 ? 0.5 : 1 }} onClick={handleJoin} disabled={code.length < 4}>Join Quiz →</button>
        <p style={{ fontSize: 12, color: "#aaa", marginTop: 16 }}>Or scan the QR code on screen</p>
      </div>
    </div>
  );
}

function StudentQuizActive() {
  const [answers, setAnswers] = useState({});
  const [currentQ, setCurrentQ] = useState(0);
  const [timeLeft, setTimeLeft] = useState(QUIZ.timeLimitSeconds);
  const [quizOpen, setQuizOpen] = useState(true);
  const [showConfirm, setShowConfirm] = useState(false);
  const [formatMsg, setFormatMsg] = useState(null);
  const [attempts, setAttempts] = useState(0);
  const [bestScores, setBestScores] = useState({});
  const [bestTotal, setBestTotal] = useState(null);
  const [lastResult, setLastResult] = useState(null);
  const [showResult, setShowResult] = useState(false);

  useEffect(() => {
    const timer = setInterval(() => {
      setTimeLeft(t => { if (t <= 1) { clearInterval(timer); setQuizOpen(false); return 0; } return t - 1; });
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const simulateGrade = () => {
    const scores = {};
    QUIZ_PROBLEMS.forEach(p => {
      const ans = (answers[p.id] || "").trim();
      if (!ans) { scores[p.id] = { score: 0, correct: false, feedback: "No answer submitted." }; return; }
      const normalized = ans.replace(/\s/g, "").toUpperCase();
      const correctNorm = p.correct_answer.replace(/\s/g, "").toUpperCase();
      if (normalized === correctNorm) {
        scores[p.id] = { score: 1.0, correct: true, feedback: "Correct!" };
      } else {
        const partial = +(0.1 + Math.random() * 0.4).toFixed(2);
        scores[p.id] = { score: partial, correct: false, feedback: "Partially correct. Some rows mismatch the expected truth table." };
      }
    });
    const total = +(QUIZ_PROBLEMS.reduce((s, p) => s + scores[p.id].score * p.points, 0) / TOTAL_PTS).toFixed(3);
    return { scores, total };
  };

  const handleSubmit = () => {
    setShowConfirm(false);
    const result = simulateGrade();
    setLastResult(result);
    setAttempts(a => a + 1);
    setShowResult(true);
    const newBest = { ...bestScores };
    QUIZ_PROBLEMS.forEach(p => {
      const prev = newBest[p.id]?.score || 0;
      if (result.scores[p.id].score > prev) newBest[p.id] = result.scores[p.id];
    });
    setBestScores(newBest);
    setBestTotal(+(QUIZ_PROBLEMS.reduce((s, p) => s + (newBest[p.id]?.score || 0) * p.points, 0) / TOTAL_PTS).toFixed(3));
  };

  const tryAgain = () => { setShowResult(false); setCurrentQ(0); setFormatMsg(null); };

  const checkFormat = () => {
    const ans = answers[QUIZ_PROBLEMS[currentQ].id] || "";
    if (!ans.trim()) { setFormatMsg({ ok: false, msg: "No answer entered." }); return; }
    const invalid = ans.replace(/[A-Da-d'()+\s·*01]/g, "");
    if (invalid) { setFormatMsg({ ok: false, msg: `Invalid characters: ${invalid}` }); return; }
    if ((ans.match(/\(/g) || []).length !== (ans.match(/\)/g) || []).length) { setFormatMsg({ ok: false, msg: "Mismatched parentheses." }); return; }
    setFormatMsg({ ok: true, msg: "Format looks good ✓" });
  };

  const fmt = (s) => `${Math.floor(s/60)}:${String(s%60).padStart(2, "0")}`;
  const isUrgent = timeLeft <= 60;
  const p = QUIZ_PROBLEMS[currentQ];

  // ── TIME'S UP ──
  if (!quizOpen) {
    return (
      <div style={M.page}>
        <div style={{ ...M.timerBar, background: "#333" }}>
          <span style={{ fontSize: 13, fontWeight: 500 }}>{QUIZ.title}</span>
          <span style={{ fontSize: 14, fontWeight: 600, color: "#EF9A9A" }}>TIME'S UP</span>
        </div>
        <div style={M.resultContainer}>
          <div style={{ fontSize: 48, marginBottom: 12 }}>⏰</div>
          <h2 style={{ fontSize: 20, fontWeight: 700, margin: "0 0 4px", color: "#1a1a1a" }}>Quiz Closed</h2>
          {bestTotal !== null ? (
            <>
              <div style={M.bestScoreBadge}>
                <span style={{ fontSize: 11, color: "#888" }}>Your Best Score</span>
                <span style={{ fontSize: 32, fontWeight: 700, color: bestTotal >= 0.8 ? "#2e7d32" : bestTotal >= 0.5 ? "#F57F17" : "#c62828", fontFamily: "'IBM Plex Mono', monospace" }}>
                  {Math.round(bestTotal * 100)}%
                </span>
                <span style={{ fontSize: 12, color: "#999" }}>{attempts} attempt{attempts !== 1 ? "s" : ""}</span>
              </div>
              <div style={{ width: "100%", maxWidth: 340, marginTop: 16 }}>
                {QUIZ_PROBLEMS.map(prob => (
                  <div key={prob.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "10px 0", borderBottom: "1px solid #f0f0f0" }}>
                    <div><span style={{ fontSize: 14, fontWeight: 600, color: "#2774AE" }}>{prob.label}</span><span style={{ fontSize: 12, color: "#999", marginLeft: 6 }}>{prob.points} pts</span></div>
                    <ScoreCell score={bestScores[prob.id]?.score} />
                  </div>
                ))}
              </div>
            </>
          ) : (
            <p style={{ fontSize: 14, color: "#c62828", marginTop: 12 }}>You didn't submit any answers.</p>
          )}
          <p style={{ fontSize: 13, color: "#aaa", marginTop: 20 }}>Your instructor will review the solutions now.</p>
        </div>
      </div>
    );
  }

  // ── RESULT VIEW ──
  if (showResult && lastResult) {
    return (
      <div style={M.page}>
        <div style={{ ...M.timerBar, background: isUrgent ? "#c62828" : "#2774AE" }}>
          <span style={{ fontSize: 13, fontWeight: 500 }}>Attempt {attempts} Result</span>
          <span style={{ fontSize: 18, fontWeight: 700, fontFamily: "'IBM Plex Mono', monospace" }}>{fmt(timeLeft)}</span>
        </div>
        <div style={M.resultContainer}>
          <div style={{ fontSize: 48, marginBottom: 8 }}>{lastResult.total >= 0.8 ? "🎉" : lastResult.total >= 0.5 ? "📊" : "💪"}</div>
          <p style={{ fontSize: 13, color: "#888", margin: "0 0 4px" }}>This Attempt</p>
          <p style={{ fontSize: 36, fontWeight: 700, fontFamily: "'IBM Plex Mono', monospace", margin: "0 0 8px",
            color: lastResult.total >= 0.8 ? "#2e7d32" : lastResult.total >= 0.5 ? "#F57F17" : "#c62828" }}>
            {Math.round(lastResult.total * 100)}%
          </p>
          {bestTotal !== null && bestTotal > lastResult.total && (
            <p style={{ fontSize: 14, color: "#2e7d32", fontWeight: 600, margin: "0 0 12px" }}>✓ Best score: {Math.round(bestTotal * 100)}%</p>
          )}
          <div style={{ width: "100%", maxWidth: 340, marginBottom: 20 }}>
            {QUIZ_PROBLEMS.map(prob => {
              const res = lastResult.scores[prob.id];
              const best = bestScores[prob.id];
              return (
                <div key={prob.id} style={{ padding: "12px 0", borderBottom: "1px solid #f0f0f0" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
                    <div><span style={{ fontSize: 14, fontWeight: 600, color: "#2774AE" }}>{prob.label}</span><span style={{ fontSize: 12, color: "#999", marginLeft: 6 }}>{prob.points} pts</span></div>
                    <ScoreCell score={res.score} />
                  </div>
                  <p style={{ fontSize: 13, color: res.correct ? "#2e7d32" : "#888", margin: "2px 0 0" }}>{res.feedback}</p>
                  {best && best.score > res.score && <p style={{ fontSize: 12, color: "#2e7d32", margin: "2px 0 0" }}>Best: {Math.round(best.score * 100)}%</p>}
                </div>
              );
            })}
          </div>
          {lastResult.total < 1.0 ? (
            <div style={{ textAlign: "center" }}>
              <p style={{ fontSize: 14, color: "#333", margin: "0 0 12px", fontWeight: 500 }}>
                {timeLeft > 30 ? "You can fix your answers and resubmit!" : "Hurry — less than 30 seconds left!"}
              </p>
              <button style={M.retryBtn} onClick={tryAgain}>✏️ Edit & Resubmit</button>
              <p style={{ fontSize: 12, color: "#aaa", marginTop: 8 }}>Best score is recorded · {fmt(timeLeft)} remaining</p>
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
      <div style={{ ...M.timerBar, background: isUrgent ? "#c62828" : "#2774AE" }}>
        <span style={{ fontSize: 13, fontWeight: 500 }}>{QUIZ.title}{attempts > 0 ? ` · Attempt ${attempts + 1}` : ""}</span>
        <span style={{ fontSize: 18, fontWeight: 700, fontFamily: "'IBM Plex Mono', monospace" }}>{fmt(timeLeft)}</span>
      </div>
      {bestTotal !== null && (
        <div style={M.bestBanner}><span>Current best: <strong>{Math.round(bestTotal * 100)}%</strong></span><span style={{ fontSize: 11, color: "#888" }}>Best score is kept</span></div>
      )}
      <div style={M.progressDots}>
        {QUIZ_PROBLEMS.map((prob, i) => {
          const isPerfect = bestScores[prob.id]?.score === 1.0;
          return (
            <button key={prob.id} onClick={() => { setCurrentQ(i); setFormatMsg(null); }} style={{
              ...M.dot, background: i === currentQ ? "#2774AE" : isPerfect ? "#4CAF50" : answers[prob.id] ? "#64B5F6" : "#e0e0e0",
              color: i === currentQ || isPerfect || answers[prob.id] ? "#fff" : "#999",
            }}>{isPerfect ? "✓" : prob.label}</button>
          );
        })}
      </div>
      <div style={M.questionArea}>
        {bestScores[p.id]?.score === 1.0 && (
          <div style={{ background: "#e8f5e9", borderRadius: 8, padding: "10px 14px", marginBottom: 12, display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ fontSize: 16 }}>✅</span><span style={{ fontSize: 13, color: "#2e7d32", fontWeight: 600 }}>You already got this one right!</span>
          </div>
        )}
        {bestScores[p.id] && bestScores[p.id].score < 1.0 && (
          <div style={{ background: "#FFF8E1", borderRadius: 8, padding: "10px 14px", marginBottom: 12, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontSize: 13, color: "#F57F17" }}>Previous best: {Math.round(bestScores[p.id].score * 100)}%</span>
            <span style={{ fontSize: 12, color: "#999" }}>Try to improve!</span>
          </div>
        )}
        <div style={{ fontSize: 18, fontWeight: 700, color: "#2774AE", marginBottom: 8 }}>{p.label} <span style={{ fontWeight: 400, color: "#999" }}>· {p.points} pts</span></div>
        <p style={{ fontSize: 14, color: "#333", lineHeight: 1.6, margin: "0 0 12px" }}>{p.text}</p>
        <div style={M.mintermBox}>
          <p style={M.mintermLabel}>Minterms</p>
          <p style={M.mintermVal}>{p.minterms}</p>
          {p.dont_cares && <><p style={M.mintermLabel}>Don't-cares</p><p style={M.mintermVal}>{p.dont_cares}</p></>}
        </div>
        <textarea style={M.answerInput} placeholder={p.placeholder} value={answers[p.id] || ""}
          onChange={e => { setAnswers({ ...answers, [p.id]: e.target.value }); setFormatMsg(null); }} rows={2} />
        {formatMsg && <p style={{ fontSize: 13, color: formatMsg.ok ? "#2e7d32" : "#c62828", margin: "4px 0 0", fontWeight: 500 }}>{formatMsg.msg}</p>}
        <div style={{ display: "flex", gap: 10, marginTop: 8 }}>
          <button style={M.checkBtn} onClick={checkFormat}>Check Format</button>
          {currentQ < QUIZ_PROBLEMS.length - 1
            ? <button style={M.nextBtn} onClick={() => { setCurrentQ(currentQ + 1); setFormatMsg(null); }}>Next →</button>
            : <button style={M.submitBtn} onClick={() => setShowConfirm(true)}>{attempts > 0 ? "Resubmit" : "Submit Quiz"}</button>}
        </div>
        {currentQ > 0 && <button style={M.backLink} onClick={() => { setCurrentQ(currentQ - 1); setFormatMsg(null); }}>← Previous</button>}
      </div>
      {showConfirm && (
        <div style={M.overlay}><div style={M.confirmBox}>
          <h3 style={{ fontSize: 17, fontWeight: 700, margin: "0 0 8px" }}>{attempts > 0 ? "Resubmit?" : "Submit quiz?"}</h3>
          <p style={{ fontSize: 14, color: "#666", margin: "0 0 4px" }}>{QUIZ_PROBLEMS.filter(pr => answers[pr.id]).length} of {QUIZ_PROBLEMS.length} answered.</p>
          {QUIZ_PROBLEMS.some(pr => !answers[pr.id]) && <p style={{ fontSize: 13, color: "#c62828", margin: "0 0 8px", fontWeight: 500 }}>⚠ Unanswered questions.</p>}
          <p style={{ fontSize: 13, color: "#2e7d32", margin: "0 0 16px" }}>✓ You'll see your score and can retry if time remains.</p>
          <div style={{ display: "flex", gap: 10 }}>
            <button style={M.confirmCancel} onClick={() => setShowConfirm(false)}>Go Back</button>
            <button style={M.confirmSubmit} onClick={handleSubmit}>{attempts > 0 ? "Resubmit" : "Submit"}</button>
          </div>
        </div></div>
      )}
    </div>
  );
}

// ── INSTRUCTOR QUIZ CONTROL ──

function InstructorQuizControl() {
  const [quizStatus, setQuizStatus] = useState("pending");
  const [timeLeft, setTimeLeft] = useState(QUIZ.timeLimitSeconds);
  const timerRef = useRef(null);
  useEffect(() => {
    if (quizStatus === "active") {
      timerRef.current = setInterval(() => {
        setTimeLeft(t => { if (t <= 1) { clearInterval(timerRef.current); setQuizStatus("closed"); return 0; } return t - 1; });
      }, 1000);
      return () => clearInterval(timerRef.current);
    }
  }, [quizStatus]);

  const elapsed = QUIZ.timeLimitSeconds - timeLeft;
  const totalStudents = ALL_STUDENTS.length;
  const submittedStudents = useMemo(() => {
    const cutoff = quizStatus === "active" ? elapsed : QUIZ.timeLimitSeconds;
    return ALL_STUDENTS.filter(s => s.didSubmit && s.firstSubmitSec <= cutoff);
  }, [elapsed, quizStatus]);
  const retriedStudents = useMemo(() => {
    const cutoff = quizStatus === "active" ? elapsed : QUIZ.timeLimitSeconds;
    return ALL_STUDENTS.filter(s => s.retrySubmitSec && s.retrySubmitSec <= cutoff);
  }, [elapsed, quizStatus]);
  const submittedCount = submittedStudents.length;
  const retryCount = retriedStudents.length;
  const notSubmitted = ALL_STUDENTS.filter(s => quizStatus === "active" ? (!s.didSubmit || s.firstSubmitSec > elapsed) : !s.didSubmit);
  const avgBest = submittedCount > 0 ? submittedStudents.reduce((s, st) => s + (st.bestScore ?? st.firstScore), 0) / submittedCount : 0;
  const avgFirst = submittedCount > 0 ? submittedStudents.reduce((s, st) => s + st.firstScore, 0) / submittedCount : 0;
  const getDist = (useBest) => { const bins = Array(10).fill(0); submittedStudents.forEach(s => { const sc = useBest ? (s.bestScore ?? s.firstScore) : s.firstScore; bins[Math.min(9, Math.floor(sc * 10))]++; }); return bins; };
  const getErrors = (pid) => {
    const correct = QUIZ_PROBLEMS.find(p => p.id === pid)?.correct_answer;
    const errs = {}; const pool = quizStatus !== "active" ? ALL_STUDENTS.filter(s => s.didSubmit) : submittedStudents;
    pool.forEach(s => { const a = s.answers?.[pid]?.answer; if (a && a !== correct) errs[a] = (errs[a] || 0) + 1; });
    return Object.entries(errs).sort((a, b) => b[1] - a[1]).slice(0, 5);
  };
  const fmt = (s) => `${Math.floor(s/60)}:${String(s%60).padStart(2, "0")}`;
  const isUrgent = timeLeft <= 60;

  // ── PENDING ──
  if (quizStatus === "pending") {
    return (
      <div style={I.page}>
        <div style={I.hdr}><div style={{ display: "flex", alignItems: "center", gap: 12 }}><span style={I.logo}>AutoTA</span><span style={I.sep}>·</span><span style={I.course}>{QUIZ.course}</span><span style={I.sep}>·</span><span style={{ color: "#aaa" }}>Quiz Control</span></div><span style={{ color: "#aaa", fontSize: 12 }}>{QUIZ.instructor}</span></div>
        <div style={I.content}>
          <div style={I.readyCard}>
            <h2 style={{ fontSize: 22, fontWeight: 700, margin: "0 0 8px" }}>{QUIZ.title}</h2>
            <p style={{ fontSize: 14, color: "#666", margin: "0 0 24px" }}>{QUIZ_PROBLEMS.length} problems · {Math.floor(QUIZ.timeLimitSeconds / 60)} min · Unlimited retries · {totalStudents} enrolled</p>
            <div style={{ display: "flex", gap: 24, justifyContent: "center", alignItems: "center", margin: "20px 0" }}>
              <div style={I.qrBox}><p style={{ fontSize: 14, color: "#888", margin: "0 0 4px" }}>QR Code</p><p style={{ fontSize: 11, color: "#aaa", margin: 0 }}>Students scan to join</p></div>
              <div style={{ textAlign: "center" }}>
                <p style={{ fontSize: 13, color: "#888", margin: "0 0 4px" }}>Quiz Code</p>
                <p style={{ fontSize: 36, fontWeight: 700, fontFamily: "'IBM Plex Mono', monospace", color: "#2774AE", margin: 0, letterSpacing: "0.05em" }}>{QUIZ.id}</p>
                <p style={{ fontSize: 12, color: "#aaa", margin: "4px 0 0" }}>autota.app/q/{QUIZ.id.replace("-","")}</p>
              </div>
            </div>
            <div style={{ background: "#f0f7ff", borderRadius: 8, padding: "12px 16px", margin: "20px auto 24px", textAlign: "left", maxWidth: 380 }}>
              <p style={{ fontSize: 13, color: "#333", margin: "0 0 6px", fontWeight: 600 }}>How it works:</p>
              <p style={{ fontSize: 12, color: "#666", margin: "0 0 3px" }}>1. Students scan QR or enter code to join</p>
              <p style={{ fontSize: 12, color: "#666", margin: "0 0 3px" }}>2. Click Start — timer begins for everyone</p>
              <p style={{ fontSize: 12, color: "#666", margin: "0 0 3px" }}>3. Students submit → see score → can retry</p>
              <p style={{ fontSize: 12, color: "#666", margin: 0 }}>4. Best score recorded when time expires</p>
            </div>
            <button style={I.startBtn} onClick={() => setQuizStatus("active")}>▶ Start Quiz ({Math.floor(QUIZ.timeLimitSeconds / 60)} min)</button>
          </div>
        </div>
      </div>
    );
  }

  // ── ACTIVE ──
  if (quizStatus === "active") {
    const dist = getDist(true);
    const maxBin = Math.max(...dist, 1);
    return (
      <div style={I.page}>
        <div style={{ ...I.hdr, background: isUrgent ? "#b71c1c" : "#1a1a1a" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}><span style={I.logo}>AutoTA</span><span style={I.sep}>·</span><span style={I.course}>{QUIZ.title}</span><span style={I.sep}>·</span><span style={{ color: "#4CAF50", fontWeight: 700 }}>● LIVE</span></div>
          <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
            <span style={{ fontSize: 28, fontWeight: 700, fontFamily: "'IBM Plex Mono', monospace", color: isUrgent ? "#FFCDD2" : "#fff" }}>{fmt(timeLeft)}</span>
            <button style={I.endBtn} onClick={() => { clearInterval(timerRef.current); setQuizStatus("closed"); }}>End Quiz</button>
          </div>
        </div>
        <div style={I.content}>
          <div style={I.liveRow}>
            <div style={I.liveCard}><p style={I.liveNum}>{submittedCount}<span style={{ fontSize: 18, color: "#888" }}>/{totalStudents}</span></p><p style={I.liveLbl}>Submitted</p><div style={I.miniBar}><div style={{ ...I.miniFill, width: `${(submittedCount/totalStudents)*100}%` }} /></div></div>
            <div style={I.liveCard}><p style={I.liveNum}>{retryCount}</p><p style={I.liveLbl}>Retries</p><p style={{ fontSize: 11, color: "#aaa", margin: "4px 0 0" }}>{submittedCount > 0 ? Math.round(retryCount/submittedCount*100) : 0}% retried</p></div>
            <div style={I.liveCard}><p style={I.liveNum}>{submittedCount > 0 ? `${Math.round(avgBest*100)}%` : "—"}</p><p style={I.liveLbl}>Avg Best</p>{avgFirst > 0 && <p style={{ fontSize: 11, color: "#aaa", margin: "4px 0 0" }}>First: {Math.round(avgFirst*100)}%</p>}</div>
            <div style={I.liveCard}><p style={I.liveNum}>{totalStudents - submittedCount}</p><p style={I.liveLbl}>Still Working</p></div>
          </div>
          <div style={{ display: "flex", gap: 16, marginBottom: 20 }}>
            <div style={{ ...I.card, flex: 1 }}>
              <p style={I.cardTitle}>Live Score Distribution (Best Attempts)</p>
              <div style={{ display: "flex", alignItems: "flex-end", gap: 4, height: 100 }}>
                {dist.map((c, i) => (<div key={i} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center" }}>
                  <span style={{ fontSize: 10, color: "#666", marginBottom: 2 }}>{c || ""}</span>
                  <div style={{ width: "100%", borderRadius: "3px 3px 0 0", height: `${Math.max(3, (c/maxBin)*80)}px`, background: i >= 8 ? "#2774AE" : i >= 5 ? "#64B5F6" : i >= 3 ? "#FFD54F" : "#EF9A9A", transition: "height 0.5s ease" }} />
                  <span style={{ fontSize: 9, color: "#999", marginTop: 3 }}>{i*10}%</span>
                </div>))}
              </div>
            </div>
            <div style={{ ...I.card, flex: 1 }}>
              <p style={I.cardTitle}>Recent Activity</p>
              <div style={{ maxHeight: 120, overflow: "auto" }}>
                {submittedStudents.slice(-10).reverse().map((s, i) => (
                  <div key={i} style={{ display: "flex", justifyContent: "space-between", padding: "4px 0", borderBottom: "1px solid #f5f5f5", fontSize: 12 }}>
                    <span style={{ color: "#333" }}>{s.name} {retriedStudents.includes(s) && <span style={{ fontSize: 10, color: "#7B1FA2", fontWeight: 600 }}>RETRY</span>}</span>
                    <span style={{ fontFamily: "'IBM Plex Mono', monospace", fontWeight: 600, color: (s.bestScore??s.firstScore) >= 0.8 ? "#2e7d32" : (s.bestScore??s.firstScore) >= 0.5 ? "#F57F17" : "#c62828" }}>{Math.round((s.bestScore??s.firstScore)*100)}%</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
          <div style={I.card}>
            <p style={I.cardTitle}>Haven't Submitted Yet ({notSubmitted.length})</p>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
              {notSubmitted.slice(0, 40).map((s, i) => <span key={i} style={{ fontSize: 11, padding: "3px 8px", background: "#f5f5f5", borderRadius: 4, color: "#666" }}>{s.name}</span>)}
              {notSubmitted.length > 40 && <span style={{ fontSize: 11, padding: "3px 8px", color: "#999" }}>+{notSubmitted.length - 40} more</span>}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // ── CLOSED / REVIEW ──
  const final = ALL_STUDENTS.filter(s => s.didSubmit);
  const finalRetried = ALL_STUDENTS.filter(s => s.retrySubmitSec);
  const fc = final.length;
  const fAvgBest = fc > 0 ? final.reduce((s, st) => s + (st.bestScore ?? st.firstScore), 0) / fc : 0;
  const fAvgFirst = fc > 0 ? final.reduce((s, st) => s + st.firstScore, 0) / fc : 0;
  const fMedian = (() => { const sc = final.map(s => s.bestScore ?? s.firstScore).sort((a,b) => a-b); if (!sc.length) return 0; return sc.length % 2 === 0 ? (sc[sc.length/2-1]+sc[sc.length/2])/2 : sc[Math.floor(sc.length/2)]; })();
  const fDist = (() => { const b = Array(10).fill(0); final.forEach(s => b[Math.min(9, Math.floor((s.bestScore??s.firstScore)*10))]++); return b; })();
  const fMax = Math.max(...fDist, 1);
  const improvRate = finalRetried.length > 0 ? finalRetried.filter(s => s.bestScore > s.firstScore).length / finalRetried.length : 0;

  return (
    <div style={I.page}>
      <div style={I.hdr}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}><span style={I.logo}>AutoTA</span><span style={I.sep}>·</span><span style={I.course}>{QUIZ.title}</span><span style={I.sep}>·</span><span style={{ color: quizStatus === "review" ? "#FFD54F" : "#EF9A9A", fontWeight: 700 }}>{quizStatus === "review" ? "REVIEW" : "ENDED"}</span></div>
        {quizStatus === "closed" && <button style={I.reviewBtn} onClick={() => setQuizStatus("review")}>Show Solutions →</button>}
      </div>
      <div style={I.content}>
        <div style={I.liveRow}>
          <div style={I.liveCard}><p style={I.liveNum}>{fc}<span style={{ fontSize: 18, color: "#888" }}>/{totalStudents}</span></p><p style={I.liveLbl}>Submitted</p></div>
          <div style={I.liveCard}><p style={I.liveNum}>{Math.round(fAvgBest*100)}%</p><p style={I.liveLbl}>Avg Best</p><p style={{ fontSize: 11, color: "#aaa", margin: "4px 0 0" }}>First avg: {Math.round(fAvgFirst*100)}%</p></div>
          <div style={I.liveCard}><p style={I.liveNum}>{Math.round(fMedian*100)}%</p><p style={I.liveLbl}>Median</p></div>
          <div style={I.liveCard}><p style={I.liveNum}>{finalRetried.length}</p><p style={I.liveLbl}>Retried</p><p style={{ fontSize: 11, color: "#2e7d32", margin: "4px 0 0" }}>{Math.round(improvRate*100)}% improved</p></div>
        </div>
        <div style={{ ...I.card, marginBottom: 20 }}>
          <p style={I.cardTitle}>Final Score Distribution (Best Attempts)</p>
          <div style={{ display: "flex", alignItems: "flex-end", gap: 4, height: 110 }}>
            {fDist.map((c, i) => (<div key={i} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center" }}>
              <span style={{ fontSize: 10, color: "#666", marginBottom: 2 }}>{c || ""}</span>
              <div style={{ width: "100%", borderRadius: "3px 3px 0 0", height: `${Math.max(3, (c/fMax)*90)}px`, background: i >= 8 ? "#2774AE" : i >= 5 ? "#64B5F6" : i >= 3 ? "#FFD54F" : "#EF9A9A" }} />
              <span style={{ fontSize: 9, color: "#999", marginTop: 3 }}>{i*10}%</span>
            </div>))}
          </div>
        </div>
        {quizStatus === "review" && QUIZ_PROBLEMS.map(p => {
          const errors = getErrors(p.id);
          const correctCount = final.filter(s => (s.answers?.[p.id]?.bestScore ?? s.answers?.[p.id]?.score) === 1.0).length;
          return (
            <div key={p.id} style={{ ...I.card, marginBottom: 16 }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 12 }}>
                <div><span style={{ fontSize: 16, fontWeight: 700, color: "#2774AE", marginRight: 8 }}>{p.label}</span><span style={{ fontSize: 13, color: "#999" }}>{p.points} pts</span></div>
                <span style={{ fontSize: 13, color: "#888" }}>{correctCount}/{fc} correct ({fc > 0 ? Math.round(correctCount/fc*100) : 0}%)</span>
              </div>
              <p style={{ fontSize: 14, color: "#333", margin: "0 0 8px", lineHeight: 1.5 }}>{p.text}</p>
              <div style={{ background: "#f0f7ff", borderRadius: 6, padding: "10px 14px", marginBottom: 10 }}>
                <p style={{ fontSize: 11, fontWeight: 700, color: "#999", margin: "0 0 4px", textTransform: "uppercase" }}>Minterms</p>
                <p style={{ fontSize: 14, fontFamily: "'IBM Plex Mono', monospace", color: "#333", margin: 0 }}>{p.minterms}</p>
                {p.dont_cares && <><p style={{ fontSize: 11, fontWeight: 700, color: "#999", margin: "8px 0 4px", textTransform: "uppercase" }}>Don't-cares</p><p style={{ fontSize: 14, fontFamily: "'IBM Plex Mono', monospace", color: "#333", margin: 0 }}>{p.dont_cares}</p></>}
              </div>
              <div style={{ background: "#e8f5e9", borderRadius: 6, padding: "10px 14px", marginBottom: 10 }}>
                <p style={{ fontSize: 11, fontWeight: 700, color: "#2e7d32", margin: "0 0 4px", textTransform: "uppercase" }}>Correct Answer</p>
                <p style={{ fontSize: 18, fontFamily: "'IBM Plex Mono', monospace", fontWeight: 700, color: "#2e7d32", margin: 0 }}>{p.correct_answer}</p>
              </div>
              {errors.length > 0 && <div>
                <p style={{ fontSize: 12, fontWeight: 700, color: "#999", margin: "0 0 6px", textTransform: "uppercase" }}>Common Wrong Answers</p>
                {errors.map(([ans, count], i) => (
                  <div key={i} style={{ display: "flex", justifyContent: "space-between", padding: "4px 8px", background: i % 2 === 0 ? "#fff" : "#fafafa", borderRadius: 4, marginBottom: 2 }}>
                    <span style={{ fontSize: 13, fontFamily: "'IBM Plex Mono', monospace", color: "#c62828" }}>{ans}</span>
                    <span style={{ fontSize: 12, color: "#999" }}>{count} students</span>
                  </div>
                ))}
              </div>}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── MAIN ──

export default function QuizPrototype() {
  const [view, setView] = useState("selector");
  const [studentScreen, setStudentScreen] = useState("entry");
  if (view === "selector") return (
    <div style={{ minHeight: "100vh", background: "#f0f0f0", fontFamily: "'IBM Plex Sans', -apple-system, sans-serif", display: "flex", alignItems: "center", justifyContent: "center" }}>
      <div style={{ textAlign: "center" }}>
        <h1 style={{ fontSize: 24, fontWeight: 700, margin: "0 0 8px", color: "#1a1a1a" }}>AutoTA Quiz Mode</h1>
        <p style={{ fontSize: 14, color: "#888", margin: "0 0 8px" }}>In-class quizzes with instant grading & unlimited retries</p>
        <p style={{ fontSize: 12, color: "#aaa", margin: "0 0 32px" }}>Best score recorded when time expires</p>
        <div style={{ display: "flex", gap: 16 }}>
          <button onClick={() => { setView("student"); setStudentScreen("entry"); }} style={{ padding: "20px 32px", background: "#2774AE", color: "#fff", border: "none", borderRadius: 10, fontSize: 16, fontWeight: 600, cursor: "pointer", minWidth: 200 }}>
            📱 Student View<br /><span style={{ fontSize: 12, fontWeight: 400, opacity: 0.8 }}>Submit · see score · retry</span>
          </button>
          <button onClick={() => setView("instructor")} style={{ padding: "20px 32px", background: "#1a1a1a", color: "#fff", border: "none", borderRadius: 10, fontSize: 16, fontWeight: 600, cursor: "pointer", minWidth: 200 }}>
            🖥 Instructor View<br /><span style={{ fontSize: 12, fontWeight: 400, opacity: 0.8 }}>Live dashboard · review</span>
          </button>
        </div>
        <p style={{ fontSize: 12, color: "#aaa", marginTop: 20 }}>Tip: Resize narrow for mobile student experience</p>
      </div>
    </div>
  );
  if (view === "student") return (
    <div>
      <div style={{ position: "fixed", bottom: 0, left: 0, right: 0, background: "#333", padding: "6px 12px", display: "flex", gap: 8, zIndex: 100, alignItems: "center" }}>
        <button onClick={() => setView("selector")} style={devBtn}>← Back</button>
        <button onClick={() => setStudentScreen("entry")} style={{ ...devBtn, background: studentScreen === "entry" ? "#2774AE" : "#555" }}>Entry</button>
        <button onClick={() => setStudentScreen("active")} style={{ ...devBtn, background: studentScreen === "active" ? "#2774AE" : "#555" }}>Active</button>
      </div>
      {studentScreen === "entry" && <StudentQuizEntry onJoin={() => setStudentScreen("active")} />}
      {studentScreen === "active" && <StudentQuizActive />}
    </div>
  );
  if (view === "instructor") return (
    <div>
      <div style={{ position: "fixed", bottom: 0, left: 0, right: 0, background: "#333", padding: "6px 12px", display: "flex", gap: 8, zIndex: 100, alignItems: "center" }}>
        <button onClick={() => setView("selector")} style={devBtn}>← Back</button>
        <span style={{ color: "#888", fontSize: 11 }}>Click Start to begin live simulation</span>
      </div>
      <InstructorQuizControl />
    </div>
  );
}

const devBtn = { padding: "4px 10px", background: "#555", color: "#fff", border: "none", borderRadius: 4, fontSize: 11, cursor: "pointer" };

const M = {
  page: { minHeight: "100vh", background: "#f5f5f5", fontFamily: "'IBM Plex Sans', -apple-system, sans-serif" },
  topBar: { display: "flex", justifyContent: "space-between", alignItems: "center", padding: "10px 16px", background: "#2774AE", color: "#fff" },
  topLogo: { fontSize: 15, fontWeight: 700 }, topCourse: { fontSize: 12, color: "rgba(255,255,255,0.8)" },
  entryContainer: { display: "flex", flexDirection: "column", alignItems: "center", padding: "60px 24px" },
  codeInput: { fontSize: 28, fontWeight: 700, fontFamily: "'IBM Plex Mono', monospace", textAlign: "center", padding: "12px 20px", border: "2px solid #2774AE", borderRadius: 10, outline: "none", width: 200, letterSpacing: "0.1em", color: "#1a1a1a" },
  joinBtn: { marginTop: 20, padding: "14px 40px", background: "#2774AE", color: "#fff", border: "none", borderRadius: 10, fontSize: 16, fontWeight: 600, cursor: "pointer", width: 240 },
  timerBar: { display: "flex", justifyContent: "space-between", alignItems: "center", padding: "10px 16px", color: "#fff", position: "sticky", top: 0, zIndex: 10 },
  bestBanner: { display: "flex", justifyContent: "space-between", alignItems: "center", padding: "8px 16px", background: "#E8F5E9", fontSize: 13, color: "#2e7d32" },
  progressDots: { display: "flex", justifyContent: "center", gap: 8, padding: "12px 16px", background: "#fff", borderBottom: "1px solid #e8e8e8" },
  dot: { width: 40, height: 40, borderRadius: 20, border: "none", fontSize: 12, fontWeight: 700, cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" },
  questionArea: { padding: "16px 16px 100px" },
  mintermBox: { background: "#f0f7ff", borderRadius: 8, padding: "12px 14px", marginBottom: 16 },
  mintermLabel: { fontSize: 11, fontWeight: 700, color: "#999", textTransform: "uppercase", margin: "0 0 4px" },
  mintermVal: { fontSize: 15, fontFamily: "'IBM Plex Mono', monospace", color: "#1a1a1a", margin: "0 0 8px", fontWeight: 600 },
  answerInput: { width: "100%", boxSizing: "border-box", padding: "12px 14px", fontSize: 16, fontFamily: "'IBM Plex Mono', monospace", border: "2px solid #d0d0d0", borderRadius: 8, outline: "none", resize: "none", marginBottom: 8 },
  checkBtn: { flex: 1, padding: "12px", background: "#f5f5f5", color: "#333", border: "1px solid #d0d0d0", borderRadius: 8, fontSize: 14, fontWeight: 500, cursor: "pointer" },
  nextBtn: { flex: 1, padding: "12px", background: "#2774AE", color: "#fff", border: "none", borderRadius: 8, fontSize: 14, fontWeight: 600, cursor: "pointer" },
  submitBtn: { flex: 1, padding: "12px", background: "#2e7d32", color: "#fff", border: "none", borderRadius: 8, fontSize: 14, fontWeight: 600, cursor: "pointer" },
  retryBtn: { padding: "14px 32px", background: "#2774AE", color: "#fff", border: "none", borderRadius: 10, fontSize: 15, fontWeight: 600, cursor: "pointer" },
  backLink: { display: "block", marginTop: 12, background: "none", border: "none", color: "#2774AE", fontSize: 13, fontWeight: 600, cursor: "pointer", padding: 0 },
  overlay: { position: "fixed", top: 0, left: 0, right: 0, bottom: 0, background: "rgba(0,0,0,0.5)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 50 },
  confirmBox: { background: "#fff", borderRadius: 12, padding: "24px", maxWidth: 320, width: "90%", textAlign: "center" },
  confirmCancel: { flex: 1, padding: "10px", background: "#f5f5f5", color: "#333", border: "1px solid #d0d0d0", borderRadius: 8, fontSize: 14, fontWeight: 500, cursor: "pointer" },
  confirmSubmit: { flex: 1, padding: "10px", background: "#2e7d32", color: "#fff", border: "none", borderRadius: 8, fontSize: 14, fontWeight: 600, cursor: "pointer" },
  resultContainer: { display: "flex", flexDirection: "column", alignItems: "center", padding: "40px 24px", textAlign: "center" },
  bestScoreBadge: { display: "flex", flexDirection: "column", alignItems: "center", gap: 2, marginTop: 12, padding: "16px 24px", background: "#f8f8f8", borderRadius: 12 },
};

const I = {
  page: { minHeight: "100vh", background: "#f0f0f0", fontFamily: "'IBM Plex Sans', -apple-system, sans-serif" },
  hdr: { display: "flex", justifyContent: "space-between", alignItems: "center", padding: "12px 28px", background: "#1a1a1a", color: "#fff", position: "sticky", top: 0, zIndex: 50 },
  logo: { fontSize: 16, fontWeight: 700 }, sep: { color: "#555" }, course: { fontWeight: 600 },
  content: { maxWidth: 1100, margin: "0 auto", padding: "20px 24px" },
  card: { background: "#fff", borderRadius: 8, padding: "18px 22px", boxShadow: "0 1px 3px rgba(0,0,0,0.06)" },
  cardTitle: { fontSize: 14, fontWeight: 700, color: "#1a1a1a", margin: "0 0 12px" },
  readyCard: { background: "#fff", borderRadius: 12, padding: "40px", maxWidth: 560, margin: "40px auto", textAlign: "center", boxShadow: "0 2px 8px rgba(0,0,0,0.08)" },
  qrBox: { width: 140, height: 140, background: "#f5f5f5", borderRadius: 8, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", border: "2px dashed #ddd" },
  startBtn: { padding: "16px 40px", background: "#2e7d32", color: "#fff", border: "none", borderRadius: 10, fontSize: 18, fontWeight: 700, cursor: "pointer" },
  endBtn: { padding: "8px 18px", background: "#c62828", color: "#fff", border: "none", borderRadius: 6, fontSize: 13, fontWeight: 600, cursor: "pointer" },
  reviewBtn: { padding: "8px 18px", background: "#2774AE", color: "#fff", border: "none", borderRadius: 6, fontSize: 13, fontWeight: 600, cursor: "pointer" },
  liveRow: { display: "flex", gap: 12, marginBottom: 20 },
  liveCard: { flex: 1, background: "#fff", borderRadius: 8, padding: "16px 20px", boxShadow: "0 1px 3px rgba(0,0,0,0.06)", textAlign: "center" },
  liveNum: { fontSize: 32, fontWeight: 700, color: "#1a1a1a", margin: "0 0 4px", fontFamily: "'IBM Plex Mono', monospace" },
  liveLbl: { fontSize: 12, color: "#888", margin: 0 },
  miniBar: { height: 4, background: "#e8e8e8", borderRadius: 2, marginTop: 8, overflow: "hidden" },
  miniFill: { height: "100%", background: "#2774AE", borderRadius: 2, transition: "width 0.5s" },
};
