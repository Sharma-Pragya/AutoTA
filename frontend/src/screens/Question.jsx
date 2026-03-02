import { useState, useEffect } from 'react';
import { S } from '../styles';
import { getQuestionLabel, validateFormat } from '../utils';
import MenuDropdown from '../components/MenuDropdown';

export default function QuestionPage({
  problem,
  index,
  total,
  answer,
  answers,
  allProblems,
  menuGroups,
  course,
  title,
  studentName,
  attemptNumber,
  saveStatus,
  onAnswerChange,
  onNext,
  onPrev,
  onMainPage,
  onGoToQuestion,
  isLast
}) {
  const [menuOpen, setMenuOpen] = useState(false);
  const [formatResult, setFormatResult] = useState(null);

  // Clear format result when question changes
  useEffect(() => {
    setFormatResult(null);
  }, [index]);

  const handleCheckFormat = () => {
    const result = validateFormat(answer, problem.answer_format);
    setFormatResult(result);
  };

  return (
    <div style={S.page}>
      <div style={S.wide}>
        <div style={S.hdr}>
          <span style={S.hdrL}>{course}</span>
          <span style={S.hdrC}>{title}</span>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <span style={S.pill}>{index + 1}/{total}</span>
            <div style={{ position: "relative" }}>
              <button
                style={S.menuBtn}
                onClick={() => setMenuOpen(!menuOpen)}
                title="Jump to question"
              >
                <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                  <rect y="2" width="18" height="2" rx="1" fill="white" />
                  <rect y="8" width="18" height="2" rx="1" fill="white" />
                  <rect y="14" width="18" height="2" rx="1" fill="white" />
                </svg>
              </button>
              {menuOpen && (
                <MenuDropdown
                  allProblems={allProblems}
                  answers={answers}
                  currentIndex={index}
                  menuGroups={menuGroups}
                  onGoToQuestion={onGoToQuestion}
                  onClose={() => setMenuOpen(false)}
                />
              )}
            </div>
          </div>
        </div>
        <div style={S.qb}>
          <p style={S.stud}>{studentName} · Attempt #{attemptNumber}</p>
          <p style={S.ql}>
            {getQuestionLabel(problem)}
            {problem.points && problem.points !== 1.0 && (
              <span style={{ fontSize: 14, fontWeight: 400, color: "#555", marginLeft: 8 }}>
                · {problem.points} pts
              </span>
            )}
          </p>
          <p style={S.qt}>{problem.text}</p>
          {problem.minterms && (
            <div style={S.mBox}>
              <p style={S.mLine}>
                <span style={S.mK}>Minterms:</span> {problem.minterms}
              </p>
              {problem.dont_cares && (
                <p style={S.mLine}>
                  <span style={S.mK}>Don't-cares:</span> {problem.dont_cares}
                </p>
              )}
            </div>
          )}
          <p style={S.hint}>💡 {problem.hint}</p>
          {problem.answer_format === "boolean_expression" && (
            <p style={S.fn}>
              Express as a minimal SOP expression.<br />
              <span style={S.mono}>
                AND = implicit (AB) · OR = + · NOT = ' or ~ &nbsp;|&nbsp; Example: A'B + CD'
              </span>
            </p>
          )}
          <div style={{ marginTop: 18 }}>
            <label style={S.label}>Your Answer</label>
            <textarea
              style={S.ans}
              value={answer}
              onChange={e => {
                onAnswerChange(e.target.value);
                setFormatResult(null);
              }}
              placeholder={problem.placeholder || "e.g.  A'B + CD' + B'D"}
              spellCheck={false}
              rows={problem.answer_format === "boolean_expression" ? 3 : 1}
            />
            {saveStatus && (
              <div style={S.saveIndicator}>{saveStatus}</div>
            )}
            {formatResult && (
              <div style={{ ...S.fb, ...(formatResult.valid ? S.fbP : S.fbF) }}>
                {formatResult.valid ? "✓" : "✗"} {formatResult.message}
              </div>
            )}
          </div>
          <div style={S.bRow}>
            <div style={{ display: "flex", gap: 10 }}>
              {index === 0 ? (
                <button style={S.btn2} onClick={onMainPage}>
                  ← Main Page
                </button>
              ) : (
                <button style={S.btn2} onClick={onPrev}>
                  ← Back
                </button>
              )}
            </div>
            <div style={{ display: "flex", gap: 10 }}>
              <button style={S.btnCk} onClick={handleCheckFormat}>
                Check Format
              </button>
              {!isLast ? (
                <button style={S.btn1} onClick={onNext}>
                  Next →
                </button>
              ) : (
                <button style={S.btnG} onClick={onNext}>
                  Review & Submit
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
