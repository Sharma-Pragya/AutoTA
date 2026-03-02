import { S } from '../styles';

export default function LandingPage({ studentName, assignmentData, attemptNumber, maxAttempts, attemptStatus, onStart }) {
  const menuGroups = assignmentData.menu_groups || [];
  const maxAttemptsReached = attemptNumber >= maxAttempts && attemptStatus === 'graded';

  return (
    <div style={S.page}>
      <div style={S.card}>
        <div style={S.bar} />
        <div style={S.body}>
          <p style={S.code}>{assignmentData.course}</p>
          <h1 style={S.h1}>{assignmentData.course_name}</h1>
          <p style={S.sub}>{assignmentData.quarter} · {assignmentData.instructor}</p>
          <div style={S.hr} />
          <p style={S.meta}>
            {studentName} · Attempt {attemptNumber} of {maxAttempts || 1}
          </p>
          <h2 style={S.h2}>{assignmentData.title}</h2>

          {maxAttemptsReached ? (
            <div style={{
              background: "#fff3cd",
              border: "1px solid #ffc107",
              borderRadius: 6,
              padding: 16,
              marginBottom: 20
            }}>
              <p style={{ fontSize: 14, fontWeight: 600, color: "#856404", margin: 0 }}>
                You have reached the maximum number of attempts ({maxAttempts}) for this assignment.
              </p>
            </div>
          ) : (
            <>
              <div style={S.box}>
                <p style={S.boxLabel}>Instructions</p>
                {assignmentData.instructions.map((text, i) => (
                  <p key={i} style={S.boxItem}>
                    <span style={S.boxNum}>{i + 1}.</span> {text}
                  </p>
                ))}
              </div>
              <p style={{ fontSize: 14, color: "#666", marginBottom: 20 }}>
                {menuGroups.length} question{menuGroups.length !== 1 ? "s" : ""} ({assignmentData.total_parts || 0} parts total)
              </p>
              <div style={S.rEnd}>
                <button style={S.btn1} onClick={onStart}>
                  Begin →
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
