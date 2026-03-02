import { useState } from 'react';
import { S } from '../styles';
import { verifyName } from '../api';

export default function NameCheckScreen({ studentId, examData, onVerified }) {
  const [input, setInput] = useState("");
  const [error, setError] = useState(null);
  const [ok, setOk] = useState(false);
  const [checking, setChecking] = useState(false);

  const check = async () => {
    setChecking(true);
    try {
      const result = await verifyName(studentId, input);
      if (result.verified) {
        setOk(true);
        setError(null);
      } else {
        setOk(false);
        setError(result.error || "Name does not match our records for this assignment.");
      }
    } catch (err) {
      setError("Error verifying name. Please try again.");
      setOk(false);
    } finally {
      setChecking(false);
    }
  };

  const handleBegin = () => {
    if (ok) {
      onVerified(input.trim());
    }
  };

  return (
    <div style={S.page}>
      <div style={S.card}>
        <div style={S.bar} />
        <div style={S.body}>
          <p style={S.code}>{examData.course}</p>
          <h1 style={S.h1}>{examData.course_name}</h1>
          <p style={S.sub}>{examData.quarter} · {examData.instructor}</p>
          <div style={S.hr} />
          <h2 style={S.h2}>{examData.title}</h2>
          <p style={S.meta}>Attempt #{examData.attempt_number || 1}</p>
          <div style={{ marginTop: 24 }}>
            <label style={S.label}>Verify Your Identity</label>
            <p style={{ fontSize: 13, color: "#555", margin: "0 0 10px", lineHeight: 1.5 }}>
              Enter your full name as it appears in your UCLA registration.
            </p>
            <input
              style={{ ...S.inp, borderColor: error ? "#c0392b" : ok ? "#2d8659" : "#d0d0d0" }}
              value={input}
              onChange={e => {
                setInput(e.target.value);
                setError(null);
                setOk(false);
              }}
              placeholder="e.g. Jane Bruin"
              onKeyDown={e => e.key === "Enter" && !checking && input.trim() && check()}
              disabled={checking}
            />
            {error && <div style={S.err}>{error}</div>}
            {ok && <div style={S.ok}>✓ Identity verified — {input.trim()}</div>}
          </div>
          <div style={S.rEnd}>
            {!ok && (
              <button
                style={S.btn2}
                onClick={check}
                disabled={!input.trim() || checking}
              >
                {checking ? "Checking..." : "Check"}
              </button>
            )}
            {ok && (
              <button style={S.btn1} onClick={handleBegin}>
                Begin Exam →
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
