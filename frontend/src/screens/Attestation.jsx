import { useState } from 'react';
import { S } from '../styles';

export default function AttestationPage({ studentName, onBack, onProceed }) {
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
              <a
                href="https://studentconduct.ucla.edu/2026-individual-student-code"
                target="_blank"
                rel="noopener noreferrer"
                style={{ color: "#2774AE", fontWeight: 600, textDecoration: "underline" }}
              >
                UCLA Student Conduct Code
              </a>{" "}
              and may result in disciplinary action by the Office of Student Conduct.
            </p>
          </div>
          <label style={{
            display: "flex",
            gap: 12,
            alignItems: "flex-start",
            cursor: "pointer",
            margin: "20px 0 24px",
            fontSize: 14,
            color: "#1a1a1a",
            lineHeight: 1.5
          }}>
            <input
              type="checkbox"
              checked={checked}
              onChange={() => setChecked(!checked)}
              style={{
                marginTop: 3,
                width: 18,
                height: 18,
                accentColor: "#2774AE",
                flexShrink: 0,
                cursor: "pointer"
              }}
            />
            <span>
              I, <strong>{studentName}</strong>, have read and agree to the above statement. I attest that the work I am about to submit is entirely my own and completed in accordance with UCLA's academic integrity policies.
            </span>
          </label>
          <div style={S.bRow}>
            <button style={S.btn2} onClick={onBack}>
              ← Back
            </button>
            <button
              style={{
                ...S.btnG,
                opacity: checked ? 1 : 0.4,
                cursor: checked ? "pointer" : "not-allowed"
              }}
              onClick={() => checked && onProceed()}
              disabled={!checked}
            >
              Proceed to Review →
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
