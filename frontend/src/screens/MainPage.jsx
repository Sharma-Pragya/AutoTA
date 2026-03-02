import { S } from '../styles';
import { getQuestionLabel } from '../utils';

export default function MainPage({
  problems,
  answers,
  menuGroups,
  course,
  title,
  studentName,
  attemptNumber,
  onGoToQuestion,
  onReview
}) {
  return (
    <div style={S.page}>
      <div style={S.wide}>
        <div style={S.hdr}>
          <span style={S.hdrL}>{course}</span>
          <span style={S.hdrC}>{title}</span>
          <span style={S.pill}>Overview</span>
        </div>
        <div style={S.qb}>
          <p style={S.stud}>{studentName} · Attempt #{attemptNumber}</p>
          <p style={S.ql}>Question Navigator</p>
          <p style={{ color: "#555", marginBottom: 18, fontSize: 13.5 }}>
            Click any item to jump to it.
          </p>
          <div style={S.nGrid}>
            {menuGroups.map(g => (
              <div key={g.parent} style={S.nGrp}>
                <p style={S.nGrpT}>Question {g.parent}</p>
                {g.items.map(p => {
                  const qi = problems.findIndex(prob => prob.id === p.id);
                  const has = answers[qi]?.trim();
                  return (
                    <div
                      key={p.id}
                      style={{ ...S.nItm, borderLeft: has ? "3px solid #2d8659" : "3px solid #ddd" }}
                      onClick={() => onGoToQuestion(qi)}
                    >
                      <span style={S.nQ}>{getQuestionLabel(p)}</span>
                      <span style={{ fontSize: 12, color: has ? "#2d8659" : "#aaa", fontWeight: 600 }}>
                        {has ? "Answered" : "—"}
                      </span>
                    </div>
                  );
                })}
              </div>
            ))}
          </div>
          <div style={S.rEnd}>
            <button style={S.btnG} onClick={onReview}>
              Review & Submit →
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
