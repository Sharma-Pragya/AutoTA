import { useState } from "react";

// --- Simulated DB data (would come from API) ---
const STUDENT_DB = {
  expectedName: "Pragya Sharma",
  studentId: "UID 123456789",
  attempt: 2,
};

const EXAM_DATA = {
  course: "ECE M16",
  courseName: "Logic Design of Digital Systems",
  quarter: "Spring 2026",
  assessmentTitle: "Homework 5 — Karnaugh Map Simplification",
  instructor: "Prof. Mani Srivastava",
  instructions: [
    "Each problem presents a Boolean function as a set of minterms. Simplify using a K-map.",
    "Express all answers as minimal sum-of-products (SOP) expressions.",
    "Use standard notation: AND (implicit), OR (+), NOT (').",
    "Don't-care conditions may be used to further simplify your expression.",
    "Use \"Check Format\" to validate your syntax before moving on.",
  ],
  problems: [
    {
      id: "1a", parent: "1", subLabel: "a",
      text: "Simplify the Boolean function F(A,B,C,D) defined by:",
      minterms: "m(2, 5, 6, 7, 10, 12, 13, 15)", dontCares: "d(1, 3)",
      hint: "Look for groupings that wrap around the K-map edges.",
      answerFormat: "boolean_expression",
    },
    {
      id: "1b", parent: "1", subLabel: "b",
      text: "Using your simplified expression from part (a), determine the output F when A=1, B=0, C=1, D=1.",
      minterms: null, dontCares: null,
      hint: "Substitute the values into your SOP expression from part (a).",
      answerFormat: "value", placeholder: "0 or 1",
    },
    {
      id: "2", parent: "2", subLabel: null,
      text: "Simplify the Boolean function F(A,B,C,D) defined by:",
      minterms: "m(0, 2, 4, 5, 6, 7, 8, 10, 13)", dontCares: null,
      hint: "Try grouping the largest possible power-of-2 blocks first.",
      answerFormat: "boolean_expression",
    },
    {
      id: "3a", parent: "3", subLabel: "a",
      text: "Simplify the Boolean function F(A,B,C,D) defined by:",
      minterms: "m(1, 3, 5, 7, 8, 9, 11, 15)", dontCares: "d(0, 2, 4)",
      hint: "Don't-cares can help form larger groups. Check all four edges.",
      answerFormat: "boolean_expression",
    },
    {
      id: "3b", parent: "3", subLabel: "b",
      text: "How many literal appearances are in your minimal SOP expression from part (a)?",
      minterms: null, dontCares: null,
      hint: "Count each variable appearance (complemented or not) in every product term.",
      answerFormat: "number", placeholder: "e.g. 6",
    },
    {
      id: "3c", parent: "3", subLabel: "c",
      text: "Write the complement F'(A,B,C,D) as a minimal sum-of-products expression.",
      minterms: null, dontCares: null,
      hint: "The minterms of F' are the non-minterm, non-don't-care rows from part (a).",
      answerFormat: "boolean_expression",
    },
  ],
};

function buildMenuStructure(problems) {
  const groups = [];
  let cur = null;
  for (const p of problems) {
    if (!cur || p.parent !== cur.parent) {
      cur = { parent: p.parent, items: [] };
      groups.push(cur);
    }
    cur.items.push(p);
  }
  return groups;
}
const MENU_GROUPS = buildMenuStructure(EXAM_DATA.problems);

function validateFormat(expr, format) {
  if (!expr || !expr.trim()) return { valid: false, message: "Answer is empty." };
  const t = expr.trim();
  if (format === "value") return /^[01]$/.test(t) ? { valid: true, message: "Format OK." } : { valid: false, message: "Enter 0 or 1." };
  if (format === "number") return /^\d+$/.test(t) ? { valid: true, message: "Format OK." } : { valid: false, message: "Enter a whole number." };
  let d = 0;
  for (const c of t) { if (c === "(") d++; if (c === ")") d--; if (d < 0) return { valid: false, message: "Unmatched closing parenthesis." }; }
  if (d !== 0) return { valid: false, message: "Unmatched opening parenthesis." };
  if (!/^[A-Da-d01\s+*()'^~]+$/.test(t)) { const b = t.match(/[^A-Da-d01\s+*()'^~]/); return { valid: false, message: `Invalid character: '${b?.[0]}'.` }; }
  if (!/[A-Da-d]/.test(t)) return { valid: false, message: "Must contain at least one variable." };
  if (/\+\+/.test(t)) return { valid: false, message: "Double OR operator." };
  if (/\+\s*$/.test(t)) return { valid: false, message: "Ends with +." };
  if (/^\s*\+/.test(t)) return { valid: false, message: "Starts with +." };
  return { valid: true, message: "Format OK — valid Boolean expression." };
}

function ql(p) { return p.subLabel ? `Q${p.parent}${p.subLabel}` : `Q${p.parent}`; }

// ── NAME CHECK ──

function NameCheckScreen({ onVerified }) {
  const [input, setInput] = useState("");
  const [error, setError] = useState(null);
  const [ok, setOk] = useState(false);
  const check = () => {
    if (input.trim().toLowerCase() === STUDENT_DB.expectedName.toLowerCase()) { setOk(true); setError(null); }
    else { setOk(false); setError("Name does not match our records for this assignment. Please enter your full name exactly as registered."); }
  };
  return (
    <div style={S.page}>
      <div style={S.card}>
        <div style={S.bar} />
        <div style={S.body}>
          <p style={S.code}>{EXAM_DATA.course}</p>
          <h1 style={S.h1}>{EXAM_DATA.courseName}</h1>
          <p style={S.sub}>{EXAM_DATA.quarter} · {EXAM_DATA.instructor}</p>
          <div style={S.hr} />
          <h2 style={S.h2}>{EXAM_DATA.assessmentTitle}</h2>
          <p style={S.meta}>Attempt #{STUDENT_DB.attempt}</p>
          <div style={{ marginTop: 24 }}>
            <label style={S.label}>Verify Your Identity</label>
            <p style={{ fontSize: 13, color: "#555", margin: "0 0 10px", lineHeight: 1.5 }}>Enter your full name as it appears in your UCLA registration.</p>
            <input style={{ ...S.inp, borderColor: error ? "#c0392b" : ok ? "#2d8659" : "#d0d0d0" }} value={input} onChange={e => { setInput(e.target.value); setError(null); setOk(false); }} placeholder="e.g. Jane Bruin" onKeyDown={e => e.key === "Enter" && check()} />
            {error && <div style={S.err}>{error}</div>}
            {ok && <div style={S.ok}>✓ Identity verified — {STUDENT_DB.expectedName}</div>}
          </div>
          <div style={S.rEnd}>
            {!ok && <button style={S.btn2} onClick={check} disabled={!input.trim()}>Check</button>}
            {ok && <button style={S.btn1} onClick={() => onVerified(STUDENT_DB.expectedName)}>Begin Exam →</button>}
          </div>
        </div>
      </div>
    </div>
  );
}

// ── LANDING ──

function LandingPage({ studentName, exam, onStart }) {
  return (
    <div style={S.page}>
      <div style={S.card}>
        <div style={S.bar} />
        <div style={S.body}>
          <p style={S.code}>{exam.course}</p>
          <h1 style={S.h1}>{exam.courseName}</h1>
          <p style={S.sub}>{exam.quarter} · {exam.instructor}</p>
          <div style={S.hr} />
          <p style={S.meta}>{studentName} · Attempt #{STUDENT_DB.attempt}</p>
          <h2 style={S.h2}>{exam.assessmentTitle}</h2>
          <div style={S.box}>
            <p style={S.boxLabel}>Instructions</p>
            {exam.instructions.map((t, i) => <p key={i} style={S.boxItem}><span style={S.boxNum}>{i + 1}.</span> {t}</p>)}
          </div>
          <p style={{ fontSize: 14, color: "#666", marginBottom: 20 }}>{MENU_GROUPS.length} question{MENU_GROUPS.length !== 1 ? "s" : ""} ({exam.problems.length} parts total)</p>
          <div style={S.rEnd}><button style={S.btn1} onClick={onStart}>Begin →</button></div>
        </div>
      </div>
    </div>
  );
}

// ── QUESTION ──

function MenuDropdown({ allProblems, answers, index, onGoToQuestion, onClose }) {
  const [expanded, setExpanded] = useState(() => {
    const cur = allProblems[index];
    return cur ? { [cur.parent]: true } : {};
  });
  const toggle = (p) => setExpanded(prev => ({ ...prev, [p]: !prev[p] }));

  return <>
    <div style={S.bk} onClick={onClose} />
    <div style={S.dd}>
      <p style={S.ddT}>Questions</p>
      {MENU_GROUPS.map(g => {
        const hasSubs = g.items.length > 1;
        const allAnswered = g.items.every((p) => { const qi = allProblems.indexOf(p); return answers[qi]?.trim(); });
        const someAnswered = g.items.some((p) => { const qi = allProblems.indexOf(p); return answers[qi]?.trim(); });
        const isExp = expanded[g.parent];

        if (!hasSubs) {
          const p = g.items[0];
          const qi = allProblems.indexOf(p);
          const has = answers[qi]?.trim();
          const cur = qi === index;
          return (
            <div key={g.parent} style={{ ...S.ddI, ...(cur ? S.ddA : {}) }} onClick={() => { onGoToQuestion(qi); onClose(); }}>
              <span style={S.ddQ}>Q{g.parent}</span>
              <span style={{ fontSize: 12, color: has ? "#2d8659" : "#ccc" }}>{has ? "●" : "○"}</span>
            </div>
          );
        }

        return (
          <div key={g.parent}>
            <div style={{ ...S.ddI, cursor: "pointer" }} onClick={() => toggle(g.parent)}>
              <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <span style={{ fontSize: 10, color: "#999", transition: "transform 0.15s", display: "inline-block", transform: isExp ? "rotate(90deg)" : "rotate(0deg)" }}>▶</span>
                <span style={S.ddQ}>Q{g.parent}</span>
              </div>
              <span style={{ fontSize: 12, color: allAnswered ? "#2d8659" : someAnswered ? "#e6a817" : "#ccc" }}>
                {allAnswered ? "●" : someAnswered ? "◐" : "○"}
              </span>
            </div>
            {isExp && g.items.map(p => {
              const qi = allProblems.indexOf(p);
              const has = answers[qi]?.trim();
              const cur = qi === index;
              return (
                <div key={p.id} style={{ ...S.ddSub, ...(cur ? S.ddA : {}) }} onClick={() => { onGoToQuestion(qi); onClose(); }}>
                  <span style={S.ddSubQ}>{p.subLabel}</span>
                  <span style={{ fontSize: 11, color: has ? "#2d8659" : "#ccc" }}>{has ? "●" : "○"}</span>
                </div>
              );
            })}
          </div>
        );
      })}
    </div>
  </>;
}

function QuestionPage({ problem, index, total, answer, answers, allProblems, onAnswerChange, onCheckFormat, formatResult, onNext, onPrev, onMainPage, onGoToQuestion, isLast, studentName }) {
  const [menuOpen, setMenuOpen] = useState(false);
  return (
    <div style={S.page}>
      <div style={S.wide}>
        <div style={S.hdr}>
          <span style={S.hdrL}>{EXAM_DATA.course}</span>
          <span style={S.hdrC}>{EXAM_DATA.assessmentTitle}</span>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <span style={S.pill}>{index + 1}/{total}</span>
            <div style={{ position: "relative" }}>
              <button style={S.menuBtn} onClick={() => setMenuOpen(!menuOpen)} title="Jump to question">
                <svg width="18" height="18" viewBox="0 0 18 18" fill="none"><rect y="2" width="18" height="2" rx="1" fill="white" /><rect y="8" width="18" height="2" rx="1" fill="white" /><rect y="14" width="18" height="2" rx="1" fill="white" /></svg>
              </button>
              {menuOpen && <MenuDropdown allProblems={allProblems} answers={answers} index={index} onGoToQuestion={onGoToQuestion} onClose={() => setMenuOpen(false)} />}
            </div>
          </div>
        </div>
        <div style={S.qb}>
          <p style={S.stud}>{studentName} · Attempt #{STUDENT_DB.attempt}</p>
          <p style={S.ql}>{ql(problem)}</p>
          <p style={S.qt}>{problem.text}</p>
          {problem.minterms && (
            <div style={S.mBox}>
              <p style={S.mLine}><span style={S.mK}>Minterms:</span> {problem.minterms}</p>
              {problem.dontCares && <p style={S.mLine}><span style={S.mK}>Don't-cares:</span> {problem.dontCares}</p>}
            </div>
          )}
          <p style={S.hint}>💡 {problem.hint}</p>
          {problem.answerFormat === "boolean_expression" && (
            <p style={S.fn}>Express as a minimal SOP expression.<br /><span style={S.mono}>AND = implicit (AB) · OR = + · NOT = ' or ~ &nbsp;|&nbsp; Example: A'B + CD'</span></p>
          )}
          <div style={{ marginTop: 18 }}>
            <label style={S.label}>Your Answer</label>
            <textarea style={S.ans} value={answer} onChange={e => onAnswerChange(e.target.value)} placeholder={problem.placeholder || "e.g.  A'B + CD' + B'D"} spellCheck={false} rows={problem.answerFormat === "boolean_expression" ? 3 : 1} />
            {formatResult && <div style={{ ...S.fb, ...(formatResult.valid ? S.fbP : S.fbF) }}>{formatResult.valid ? "✓" : "✗"} {formatResult.message}</div>}
          </div>
          <div style={S.bRow}>
            <div style={{ display: "flex", gap: 10 }}>
              {index === 0
                ? <button style={S.btn2} onClick={onMainPage}>← Main Page</button>
                : <button style={S.btn2} onClick={onPrev}>← Back</button>}
            </div>
            <div style={{ display: "flex", gap: 10 }}>
              <button style={S.btnCk} onClick={onCheckFormat}>Check Format</button>
              {!isLast
                ? <button style={S.btn1} onClick={onNext}>Next →</button>
                : <button style={S.btnG} onClick={onNext}>Review & Submit</button>}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── MAIN PAGE ──

function MainPage({ problems, answers, onGoToQuestion, onReview, studentName }) {
  return (
    <div style={S.page}>
      <div style={S.wide}>
        <div style={S.hdr}>
          <span style={S.hdrL}>{EXAM_DATA.course}</span>
          <span style={S.hdrC}>{EXAM_DATA.assessmentTitle}</span>
          <span style={S.pill}>Overview</span>
        </div>
        <div style={S.qb}>
          <p style={S.stud}>{studentName} · Attempt #{STUDENT_DB.attempt}</p>
          <p style={S.ql}>Question Navigator</p>
          <p style={{ color: "#555", marginBottom: 18, fontSize: 13.5 }}>Click any item to jump to it.</p>
          <div style={S.nGrid}>
            {MENU_GROUPS.map(g => (
              <div key={g.parent} style={S.nGrp}>
                <p style={S.nGrpT}>Question {g.parent}</p>
                {g.items.map(p => {
                  const qi = problems.indexOf(p);
                  const has = answers[qi]?.trim();
                  return (
                    <div key={p.id} style={{ ...S.nItm, borderLeft: has ? "3px solid #2d8659" : "3px solid #ddd" }} onClick={() => onGoToQuestion(qi)}>
                      <span style={S.nQ}>{ql(p)}</span>
                      <span style={{ fontSize: 12, color: has ? "#2d8659" : "#aaa", fontWeight: 600 }}>{has ? "Answered" : "—"}</span>
                    </div>
                  );
                })}
              </div>
            ))}
          </div>
          <div style={S.rEnd}><button style={S.btnG} onClick={onReview}>Review & Submit →</button></div>
        </div>
      </div>
    </div>
  );
}

// ── ATTESTATION ──

function AttestationPage({ studentName, onBack, onProceed }) {
  const [checked, setChecked] = useState(false);
  return (
    <div style={S.page}>
      <div style={S.card}>
        <div style={{ ...S.bar, background: "#1a1a1a" }} />
        <div style={S.body}>
          <p style={S.ql}>Academic Integrity Statement</p>
          <div style={{ ...S.box, borderColor: "#d4c5a9", background: "#fdfaf3" }}>
            <p style={{ fontSize: 14, color: "#333", lineHeight: 1.65, margin: 0 }}>
              I, <strong>{studentName}</strong>, certify that all work submitted in this assessment is my own. I have not given or received unpermitted aid, nor have I used any unauthorized resources, including AI content generators, in completing this assignment.
            </p>
            <p style={{ fontSize: 14, color: "#333", lineHeight: 1.65, margin: "14px 0 0" }}>
              I understand that as a member of the UCLA community, I am expected to demonstrate integrity in all academic endeavors. Academic dishonesty, including but not limited to cheating, fabrication, plagiarism, and facilitating academic misconduct, is a violation of the{" "}
              <a href="https://studentconduct.ucla.edu/2026-individual-student-code" target="_blank" rel="noopener noreferrer" style={{ color: "#2774AE", fontWeight: 600, textDecoration: "underline" }}>UCLA Student Conduct Code</a>{" "}
              and may result in disciplinary action by the Office of Student Conduct.
            </p>
          </div>
          <label style={{ display: "flex", gap: 12, alignItems: "flex-start", cursor: "pointer", margin: "20px 0 24px", fontSize: 14, color: "#1a1a1a", lineHeight: 1.5 }}>
            <input type="checkbox" checked={checked} onChange={() => setChecked(!checked)} style={{ marginTop: 3, width: 18, height: 18, accentColor: "#2774AE", flexShrink: 0 }} />
            <span>I, <strong>{studentName}</strong>, have read and agree to the above statement. I attest that the work I am about to submit is entirely my own and completed in accordance with UCLA's academic integrity policies.</span>
          </label>
          <div style={S.bRow}>
            <button style={S.btn2} onClick={onBack}>← Back</button>
            <button style={{ ...S.btnG, opacity: checked ? 1 : 0.4, cursor: checked ? "pointer" : "not-allowed" }} onClick={() => checked && onProceed()}>Proceed to Review →</button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── REVIEW ──

function ReviewPage({ problems, answers, onGoToQuestion, onMainPage, studentName }) {
  const [confirming, setConfirming] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  if (submitted) {
    return (
      <div style={S.page}>
        <div style={S.card}>
          <div style={{ ...S.bar, background: "#2d8659" }} />
          <div style={S.body}>
            <div style={{ fontSize: 48, marginBottom: 10, textAlign: "center" }}>✓</div>
            <h1 style={{ ...S.h1, textAlign: "center" }}>Submitted</h1>
            <p style={{ ...S.sub, textAlign: "center", marginBottom: 24 }}>{studentName} · Attempt #{STUDENT_DB.attempt} · Answers recorded.</p>
            <div style={S.box}>
              {problems.map((p, i) => (
                <div key={i} style={{ display: "flex", justifyContent: "space-between", padding: "5px 0", borderBottom: i < problems.length - 1 ? "1px solid #f0f0f0" : "none" }}>
                  <span style={{ fontSize: 13, fontWeight: 700, color: "#2774AE" }}>{ql(p)}</span>
                  <span style={{ fontSize: 13, fontFamily: "'IBM Plex Mono', monospace", color: answers[i] ? "#1a1a1a" : "#bbb" }}>{answers[i] || "(blank)"}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={S.page}>
      <div style={S.wide}>
        <div style={S.hdr}>
          <span style={S.hdrL}>{EXAM_DATA.course}</span>
          <span style={S.hdrC}>Review Answers</span>
          <span style={S.pill}>Final</span>
        </div>
        <div style={S.qb}>
          <p style={S.stud}>{studentName} · Attempt #{STUDENT_DB.attempt}</p>
          <p style={S.ql}>Review Your Answers</p>
          <p style={{ color: "#555", marginBottom: 18, fontSize: 13.5 }}>Click any row to edit.</p>
          {problems.map((p, i) => {
            const has = answers[i]?.trim();
            const v = has ? validateFormat(answers[i], p.answerFormat) : null;
            return (
              <div key={i} style={S.rRow} onClick={() => onGoToQuestion(i)}>
                <span style={S.rQ}>{ql(p)}</span>
                <span style={{ ...S.rA, color: has ? "#1a1a1a" : "#bbb" }}>{has ? answers[i] : "(no answer)"}</span>
                {has && <span style={{ fontSize: 11, fontWeight: 600, color: v?.valid ? "#2d8659" : "#c0392b", minWidth: 50, textAlign: "right" }}>{v?.valid ? "✓ Valid" : "✗ Error"}</span>}
              </div>
            );
          })}
          <div style={{ ...S.bRow, marginTop: 24 }}>
            <button style={S.btn2} onClick={onMainPage}>← Main Page</button>
            {!confirming
              ? <button style={S.btnG} onClick={() => setConfirming(true)}>Submit All Answers</button>
              : <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
                  <span style={{ color: "#c0392b", fontSize: 13, fontWeight: 600 }}>Final — cannot be undone.</span>
                  <button style={S.btn2} onClick={() => setConfirming(false)}>Cancel</button>
                  <button style={S.btnG} onClick={() => setSubmitted(true)}>Confirm Submit</button>
                </div>}
          </div>
        </div>
      </div>
    </div>
  );
}

// ── APP ──

export default function AutoTAExam() {
  const [screen, setScreen] = useState("namecheck");
  const [studentName, setStudentName] = useState("");
  const [currentQ, setCurrentQ] = useState(0);
  const [answers, setAnswers] = useState(EXAM_DATA.problems.map(() => ""));
  const [fmts, setFmts] = useState(EXAM_DATA.problems.map(() => null));

  const upd = (i, v) => { const a = [...answers]; a[i] = v; setAnswers(a); const f = [...fmts]; f[i] = null; setFmts(f); };
  const chk = (i) => { const f = [...fmts]; f[i] = validateFormat(answers[i], EXAM_DATA.problems[i].answerFormat); setFmts(f); };
  const ps = EXAM_DATA.problems;
  const last = currentQ === ps.length - 1;

  if (screen === "namecheck") return <NameCheckScreen onVerified={n => { setStudentName(n); setScreen("landing"); }} />;
  if (screen === "landing") return <LandingPage studentName={studentName} exam={EXAM_DATA} onStart={() => { setCurrentQ(0); setScreen("question"); }} />;
  if (screen === "main") return <MainPage problems={ps} answers={answers} studentName={studentName} onGoToQuestion={i => { setCurrentQ(i); setScreen("question"); }} onReview={() => setScreen("attestation")} />;
  if (screen === "attestation") return <AttestationPage studentName={studentName} onBack={() => setScreen("main")} onProceed={() => setScreen("review")} />;
  if (screen === "review") return <ReviewPage problems={ps} answers={answers} studentName={studentName} onGoToQuestion={i => { setCurrentQ(i); setScreen("question"); }} onMainPage={() => setScreen("main")} />;

  return (
    <QuestionPage problem={ps[currentQ]} index={currentQ} total={ps.length} answer={answers[currentQ]} answers={answers} allProblems={ps} studentName={studentName}
      onAnswerChange={v => upd(currentQ, v)} onCheckFormat={() => chk(currentQ)} formatResult={fmts[currentQ]}
      onNext={() => { last ? setScreen("attestation") : setCurrentQ(currentQ + 1); }}
      onPrev={() => setCurrentQ(Math.max(0, currentQ - 1))} onMainPage={() => setScreen("main")} onGoToQuestion={i => setCurrentQ(i)} isLast={last} />
  );
}

// ── STYLES ──

const S = {
  page: { minHeight: "100vh", background: "#f0f0f0", display: "flex", justifyContent: "center", alignItems: "flex-start", padding: "28px 16px", fontFamily: "'IBM Plex Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif" },
  card: { background: "#fff", borderRadius: 8, overflow: "hidden", maxWidth: 620, width: "100%", boxShadow: "0 1px 4px rgba(0,0,0,0.07)" },
  wide: { background: "#fff", borderRadius: 8, overflow: "hidden", maxWidth: 760, width: "100%", boxShadow: "0 1px 4px rgba(0,0,0,0.07)" },
  bar: { height: 5, background: "#2774AE" },
  body: { padding: "36px 36px 32px" },
  code: { fontSize: 12, fontWeight: 700, color: "#2774AE", letterSpacing: "0.08em", textTransform: "uppercase", margin: 0 },
  h1: { fontSize: 24, fontWeight: 700, color: "#1a1a1a", margin: "5px 0 3px", lineHeight: 1.2 },
  sub: { fontSize: 13.5, color: "#666", margin: 0 },
  h2: { fontSize: 17, fontWeight: 600, color: "#1a1a1a", margin: "0 0 14px" },
  meta: { fontSize: 13, color: "#888", margin: "8px 0 14px", fontWeight: 500 },
  hr: { height: 1, background: "#e4e4e4", margin: "20px 0" },
  box: { background: "#fafafa", border: "1px solid #e8e8e8", borderRadius: 6, padding: "14px 18px", marginBottom: 16 },
  boxLabel: { fontSize: 11, fontWeight: 700, color: "#888", textTransform: "uppercase", letterSpacing: "0.06em", margin: "0 0 8px" },
  boxItem: { fontSize: 13.5, color: "#333", margin: "5px 0", lineHeight: 1.5 },
  boxNum: { fontWeight: 700, color: "#2774AE", marginRight: 4 },
  label: { display: "block", fontSize: 11, fontWeight: 700, color: "#888", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 6 },
  inp: { width: "100%", padding: "10px 12px", fontSize: 15, fontFamily: "'IBM Plex Sans', sans-serif", border: "2px solid #d0d0d0", borderRadius: 6, outline: "none", boxSizing: "border-box" },
  ans: { width: "100%", padding: "11px 13px", fontSize: 15, fontFamily: "'IBM Plex Mono', 'Menlo', monospace", border: "2px solid #d0d0d0", borderRadius: 6, outline: "none", resize: "vertical", boxSizing: "border-box", lineHeight: 1.6 },
  err: { marginTop: 8, padding: "8px 12px", borderRadius: 5, fontSize: 13, fontWeight: 600, background: "#fdf0ef", color: "#c0392b", border: "1px solid #f0c4c1" },
  ok: { marginTop: 8, padding: "8px 12px", borderRadius: 5, fontSize: 13, fontWeight: 600, background: "#eaf7f0", color: "#1e7a47", border: "1px solid #b8e6cc" },
  fb: { marginTop: 8, padding: "8px 12px", borderRadius: 5, fontSize: 13, fontWeight: 600 },
  fbP: { background: "#eaf7f0", color: "#1e7a47", border: "1px solid #b8e6cc" },
  fbF: { background: "#fdf0ef", color: "#c0392b", border: "1px solid #f0c4c1" },
  hdr: { display: "flex", justifyContent: "space-between", alignItems: "center", padding: "11px 24px", background: "#2774AE", color: "#fff", fontSize: 13, fontWeight: 600 },
  hdrL: { letterSpacing: "0.04em" },
  hdrC: { opacity: 0.85, fontSize: 12 },
  pill: { background: "rgba(255,255,255,0.2)", padding: "3px 10px", borderRadius: 4, fontSize: 12 },
  qb: { padding: "28px 24px 24px" },
  stud: { fontSize: 12, color: "#999", fontWeight: 500, margin: "0 0 4px" },
  ql: { fontSize: 12, fontWeight: 700, color: "#2774AE", textTransform: "uppercase", letterSpacing: "0.06em", margin: "0 0 10px" },
  qt: { fontSize: 15, color: "#1a1a1a", lineHeight: 1.55, margin: "0 0 10px" },
  mBox: { background: "#f7f7f7", border: "1px solid #e4e4e4", borderRadius: 6, padding: "10px 14px", marginBottom: 10, fontFamily: "'IBM Plex Mono', monospace" },
  mLine: { fontSize: 14, margin: "3px 0", color: "#1a1a1a" },
  mK: { fontWeight: 700, color: "#555" },
  hint: { fontSize: 13, color: "#666", fontStyle: "italic", margin: "6px 0" },
  fn: { fontSize: 13, color: "#555", margin: "6px 0 0", lineHeight: 1.5 },
  mono: { fontSize: 12, color: "#888", fontFamily: "'IBM Plex Mono', monospace" },
  bRow: { display: "flex", gap: 10, alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", marginTop: 24 },
  rEnd: { display: "flex", justifyContent: "flex-end", marginTop: 24 },
  btn1: { padding: "10px 22px", background: "#2774AE", color: "#fff", border: "none", borderRadius: 6, fontSize: 14, fontWeight: 600, cursor: "pointer" },
  btn2: { padding: "10px 18px", background: "#fff", color: "#444", border: "1px solid #d0d0d0", borderRadius: 6, fontSize: 14, fontWeight: 500, cursor: "pointer" },
  btnG: { padding: "10px 22px", background: "#2d8659", color: "#fff", border: "none", borderRadius: 6, fontSize: 14, fontWeight: 600, cursor: "pointer" },
  btnCk: { padding: "10px 18px", background: "#f7f7f7", color: "#333", border: "1px solid #ccc", borderRadius: 6, fontSize: 13, fontWeight: 600, cursor: "pointer", fontFamily: "'IBM Plex Mono', monospace" },
  menuBtn: { background: "rgba(255,255,255,0.15)", border: "1px solid rgba(255,255,255,0.3)", borderRadius: 5, padding: "5px 7px", cursor: "pointer", display: "flex", alignItems: "center" },
  bk: { position: "fixed", top: 0, left: 0, right: 0, bottom: 0, zIndex: 99 },
  dd: { position: "absolute", top: "calc(100% + 8px)", right: 0, width: 180, background: "#fff", border: "1px solid #e0e0e0", borderRadius: 8, boxShadow: "0 8px 24px rgba(0,0,0,0.12)", zIndex: 100, padding: "8px 0", maxHeight: 380, overflowY: "auto" },
  ddT: { fontSize: 11, fontWeight: 700, color: "#888", textTransform: "uppercase", letterSpacing: "0.06em", padding: "4px 16px 8px", margin: 0, borderBottom: "1px solid #f0f0f0" },
  ddI: { display: "flex", alignItems: "center", justifyContent: "space-between", padding: "8px 16px", cursor: "pointer", borderLeft: "3px solid transparent" },
  ddA: { background: "#f0f7ff", borderLeft: "3px solid #2774AE" },
  ddQ: { fontSize: 13, fontWeight: 600, color: "#333" },
  ddSub: { display: "flex", alignItems: "center", justifyContent: "space-between", padding: "6px 16px 6px 38px", cursor: "pointer", borderLeft: "3px solid transparent" },
  ddSubQ: { fontSize: 12, fontWeight: 500, color: "#666" },
  ddS: { height: 1, background: "#f0f0f0", margin: "4px 0" },
  nGrid: { display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: 12, marginBottom: 8 },
  nGrp: { background: "#fafafa", border: "1px solid #e8e8e8", borderRadius: 6, padding: "12px 14px" },
  nGrpT: { fontSize: 13, fontWeight: 700, color: "#1a1a1a", margin: "0 0 8px" },
  nItm: { display: "flex", justifyContent: "space-between", alignItems: "center", padding: "6px 10px", marginBottom: 4, borderRadius: 4, cursor: "pointer", background: "#fff" },
  nQ: { fontSize: 13, fontWeight: 600, color: "#2774AE" },
  rRow: { display: "flex", alignItems: "center", gap: 12, padding: "11px 14px", background: "#fafafa", border: "1px solid #e8e8e8", borderRadius: 6, marginBottom: 6, cursor: "pointer" },
  rQ: { fontSize: 13, fontWeight: 700, color: "#2774AE", minWidth: 36 },
  rA: { flex: 1, fontSize: 14, fontFamily: "'IBM Plex Mono', monospace", fontWeight: 500, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" },
};
