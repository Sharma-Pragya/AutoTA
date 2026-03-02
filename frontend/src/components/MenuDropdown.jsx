import { useState } from 'react';
import { S } from '../styles';
import { getQuestionLabel } from '../utils';

export default function MenuDropdown({ allProblems, answers, currentIndex, menuGroups, onGoToQuestion, onClose }) {
  const [expanded, setExpanded] = useState(() => {
    const cur = allProblems[currentIndex];
    return cur ? { [cur.parent_label]: true } : {};
  });

  const toggle = (parent) => {
    setExpanded(prev => ({ ...prev, [parent]: !prev[parent] }));
  };

  return (
    <>
      <div style={S.bk} onClick={onClose} />
      <div style={S.dd}>
        <p style={S.ddT}>Questions</p>
        {menuGroups.map(g => {
          const hasSubs = g.items.length > 1;
          const allAnswered = g.items.every(p => {
            const idx = allProblems.findIndex(prob => prob.id === p.id);
            return answers[idx]?.trim();
          });
          const someAnswered = g.items.some(p => {
            const idx = allProblems.findIndex(prob => prob.id === p.id);
            return answers[idx]?.trim();
          });
          const isExp = expanded[g.parent];

          if (!hasSubs) {
            const p = g.items[0];
            const qi = allProblems.findIndex(prob => prob.id === p.id);
            const has = answers[qi]?.trim();
            const cur = qi === currentIndex;
            return (
              <div
                key={g.parent}
                style={{ ...S.ddI, ...(cur ? S.ddA : {}) }}
                onClick={() => { onGoToQuestion(qi); onClose(); }}
              >
                <span style={S.ddQ}>Q{g.parent}</span>
                <span style={{ fontSize: 12, color: has ? "#2d8659" : "#ccc" }}>
                  {has ? "●" : "○"}
                </span>
              </div>
            );
          }

          return (
            <div key={g.parent}>
              <div style={{ ...S.ddI, cursor: "pointer" }} onClick={() => toggle(g.parent)}>
                <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  <span style={{
                    fontSize: 10,
                    color: "#999",
                    transition: "transform 0.15s",
                    display: "inline-block",
                    transform: isExp ? "rotate(90deg)" : "rotate(0deg)"
                  }}>▶</span>
                  <span style={S.ddQ}>Q{g.parent}</span>
                </div>
                <span style={{ fontSize: 12, color: allAnswered ? "#2d8659" : someAnswered ? "#e6a817" : "#ccc" }}>
                  {allAnswered ? "●" : someAnswered ? "◐" : "○"}
                </span>
              </div>
              {isExp && g.items.map(p => {
                const qi = allProblems.findIndex(prob => prob.id === p.id);
                const has = answers[qi]?.trim();
                const cur = qi === currentIndex;
                return (
                  <div
                    key={p.id}
                    style={{ ...S.ddSub, ...(cur ? S.ddA : {}) }}
                    onClick={() => { onGoToQuestion(qi); onClose(); }}
                  >
                    <span style={S.ddSubQ}>{p.sub_label}</span>
                    <span style={{ fontSize: 11, color: has ? "#2d8659" : "#ccc" }}>
                      {has ? "●" : "○"}
                    </span>
                  </div>
                );
              })}
            </div>
          );
        })}
      </div>
    </>
  );
}
