import { useState } from 'react';
import { S } from '../styles';
import { getQuestionLabel, validateFormat } from '../utils';

export default function ReviewPage({
  problems,
  answers,
  course,
  title,
  studentName,
  attemptNumber,
  maxAttempts,
  canRetry,
  attemptsRemaining,
  submitting,
  submitted,
  results,
  onGoToQuestion,
  onMainPage,
  onSubmit,
  onRetry
}) {
  const [confirming, setConfirming] = useState(false);

  if (submitted) {
    return (
      <div style={S.page}>
        <div style={S.card}>
          <div style={{ ...S.bar, background: "#2d8659" }} />
          <div style={S.body}>
            <div style={{ fontSize: 48, marginBottom: 10, textAlign: "center" }}>✓</div>
            <h1 style={{ ...S.h1, textAlign: "center" }}>Submitted</h1>
            <p style={{ ...S.sub, textAlign: "center", marginBottom: 24 }}>
              {studentName} · Attempt #{attemptNumber} · Answers recorded.
            </p>
            <div style={S.box}>
              {problems.map((p, i) => (
                <div
                  key={i}
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    padding: "5px 0",
                    borderBottom: i < problems.length - 1 ? "1px solid #f0f0f0" : "none"
                  }}
                >
                  <span style={{ fontSize: 13, fontWeight: 700, color: "#2774AE" }}>
                    {getQuestionLabel(p)}
                  </span>
                  <span
                    style={{
                      fontSize: 13,
                      fontFamily: "'IBM Plex Mono', monospace",
                      color: answers[i] ? "#1a1a1a" : "#bbb"
                    }}
                  >
                    {answers[i] || "(blank)"}
                  </span>
                </div>
              ))}
            </div>
            {canRetry && (
              <div style={{ marginTop: 24, textAlign: "center" }}>
                <p style={{ fontSize: 13, color: "#555", marginBottom: 12 }}>
                  You have {attemptsRemaining} attempt(s) remaining.
                </p>
                <button style={S.btnG} onClick={onRetry}>
                  Start New Attempt
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={S.page}>
      <div style={S.wide}>
        <div style={S.hdr}>
          <span style={S.hdrL}>{course}</span>
          <span style={S.hdrC}>Review Answers</span>
          <span style={S.pill}>Final</span>
        </div>
        <div style={S.qb}>
          <p style={S.stud}>{studentName} · Attempt #{attemptNumber}</p>
          <p style={S.ql}>Review Your Answers</p>
          <p style={{ color: "#555", marginBottom: 18, fontSize: 13.5 }}>
            Click any row to edit.
          </p>
          {problems.map((p, i) => {
            const has = answers[i]?.trim();
            const v = has ? validateFormat(answers[i], p.answer_format) : null;
            return (
              <div key={i} style={S.rRow} onClick={() => onGoToQuestion(i)}>
                <span style={S.rQ}>{getQuestionLabel(p)}</span>
                <span style={{ ...S.rA, color: has ? "#1a1a1a" : "#bbb" }}>
                  {has ? answers[i] : "(no answer)"}
                </span>
                {has && (
                  <span
                    style={{
                      fontSize: 11,
                      fontWeight: 600,
                      color: v?.valid ? "#2d8659" : "#c0392b",
                      minWidth: 50,
                      textAlign: "right"
                    }}
                  >
                    {v?.valid ? "✓ Valid" : "✗ Error"}
                  </span>
                )}
              </div>
            );
          })}
          <div style={{ ...S.bRow, marginTop: 24 }}>
            <button style={S.btn2} onClick={onMainPage} disabled={submitting}>
              ← Main Page
            </button>
            {!confirming ? (
              <button style={S.btnG} onClick={() => setConfirming(true)} disabled={submitting}>
                Submit All Answers
              </button>
            ) : (
              <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
                <span style={{ color: "#c0392b", fontSize: 13, fontWeight: 600 }}>
                  Final — cannot be undone.
                </span>
                <button style={S.btn2} onClick={() => setConfirming(false)} disabled={submitting}>
                  Cancel
                </button>
                <button style={S.btnG} onClick={onSubmit} disabled={submitting}>
                  {submitting ? "Submitting..." : "Confirm Submit"}
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
