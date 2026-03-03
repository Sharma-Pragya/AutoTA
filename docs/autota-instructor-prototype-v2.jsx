import { useState, useMemo } from "react";

// ── MOCK DATA ──

const OFFERING = {
  course: "ECE M16",
  courseName: "Logic Design of Digital Systems",
  quarter: "Spring 2026",
  instructor: "Prof. Mani Srivastava",
};

const SECTIONS = [
  { label: "1A", count: 98 },
  { label: "1B", count: 102 },
];
const TOTAL_ENROLLED = SECTIONS.reduce((s, sec) => s + sec.count, 0);

const PROBLEMS_HW5 = [
  { id: "hw5_1a", label: "Q1a", points: 2.0, format: "boolean_expression" },
  { id: "hw5_1b", label: "Q1b", points: 1.0, format: "value" },
  { id: "hw5_2", label: "Q2", points: 2.0, format: "boolean_expression" },
  { id: "hw5_3a", label: "Q3a", points: 2.0, format: "boolean_expression" },
  { id: "hw5_3b", label: "Q3b", points: 1.0, format: "number" },
  { id: "hw5_3c", label: "Q3c", points: 2.0, format: "boolean_expression" },
];

const PROBLEMS_HW6 = [
  { id: "hw6_1a", label: "Q1a", points: 3.0, format: "boolean_expression" },
  { id: "hw6_1b", label: "Q1b", points: 2.0, format: "boolean_expression" },
  { id: "hw6_2", label: "Q2", points: 3.0, format: "boolean_expression" },
  { id: "hw6_3", label: "Q3", points: 2.0, format: "number" },
];

const ASSIGNMENTS = [
  {
    id: "hw3", title: "PSET 3 — Boolean Algebra", type: "PSET",
    isActive: false, maxAttempts: 3, closesAt: "2026-02-01T23:59:00Z",
    totalPts: 8, problems: [],
  },
  {
    id: "hw4", title: "PSET 4 — Combinational Logic", type: "PSET",
    isActive: false, maxAttempts: 3, closesAt: "2026-02-15T23:59:00Z",
    totalPts: 10, problems: [],
  },
  {
    id: "hw5", title: "PSET 5 — Karnaugh Map Simplification", type: "PSET",
    isActive: true, maxAttempts: 3, closesAt: "2026-03-15T23:59:00Z",
    totalPts: PROBLEMS_HW5.reduce((s, p) => s + p.points, 0), problems: PROBLEMS_HW5,
  },
  {
    id: "hw6", title: "PSET 6 — Multi-Level Optimization", type: "PSET",
    isActive: true, maxAttempts: 3, closesAt: "2026-03-29T23:59:00Z",
    totalPts: PROBLEMS_HW6.reduce((s, p) => s + p.points, 0), problems: PROBLEMS_HW6,
  },
  {
    id: "quiz1", title: "Quiz 1 — Gates & Truth Tables", type: "Quiz",
    isActive: false, maxAttempts: 1, closesAt: "2026-01-31T23:59:00Z",
    totalPts: 20, problems: [],
  },
  {
    id: "quiz2", title: "Quiz 2 — K-Map Speed Round", type: "Quiz",
    isActive: false, maxAttempts: 1, closesAt: "2026-02-28T23:59:00Z",
    totalPts: 20, problems: [],
  },
  {
    id: "midterm", title: "Midterm Exam", type: "Midterm",
    isActive: false, maxAttempts: 1, closesAt: "2026-02-14T23:59:00Z",
    totalPts: 100, problems: [],
  },
  {
    id: "da1", title: "Design Assignment 1 — ALU Design", type: "Design Assignment",
    isActive: true, maxAttempts: 2, closesAt: "2026-03-22T23:59:00Z",
    totalPts: 50, problems: [],
  },
];

// Auto-detect assignment types
const ASSIGNMENT_TYPES = [...new Set(ASSIGNMENTS.map(a => a.type))];

// Generate students with per-assignment data
function makeStudents() {
  const names = [
    "Pragya Sharma","Jane Bruin","Joe Bruin","Alice Chen","Bob Kim","Carlos Rivera",
    "Diana Patel","Ethan Park","Fiona Nguyen","George Wu","Hannah Lee","Ivan Petrov",
    "Julia Santos","Kevin Tran","Lily Zhang","Marco Silva","Nina Kowalski","Oscar Mendez",
    "Priya Gupta","Quinn O'Brien","Rosa Martinez","Sam Nakamura","Tara Singh","Uma Reddy",
    "Victor Huang","Wendy Cho","Xavier Diaz","Yuki Tanaka","Zara Ahmed","Aiden Murphy",
  ];
  return names.map((name, i) => {
    const uid = `UID${String(100000000 + i).slice(0, 9)}`;
    const section = SECTIONS[i % 2].label;
    const email = name.toLowerCase().replace(/[' ]/g, "").slice(0, 10) + "@ucla.edu";

    // Generate per-assignment data
    const assignmentData = {};
    ASSIGNMENTS.forEach(asn => {
      const r = Math.random();
      let status, totalScore, attempts, problemScores, answers;

      if (asn.isActive && r < 0.12) {
        status = "not_started"; totalScore = null; attempts = 0; problemScores = {}; answers = {};
      } else if (asn.isActive && r < 0.22) {
        status = "in_progress"; totalScore = null; attempts = 1; problemScores = {}; answers = {};
      } else {
        status = "graded";
        attempts = 1 + (asn.maxAttempts > 1 ? Math.floor(Math.random() * 2) : 0);
        // Create a realistic score distribution — slightly right-skewed
        const base = Math.random();
        totalScore = base < 0.1 ? 0.3 + Math.random() * 0.3 : base < 0.3 ? 0.6 + Math.random() * 0.2 : 0.7 + Math.random() * 0.3;
        totalScore = Math.min(1.0, totalScore);

        // Per-problem scores for assignments with problems
        problemScores = {};
        answers = {};
        if (asn.problems.length > 0) {
          let totalEarned = 0;
          asn.problems.forEach(p => {
            const pr = Math.random();
            const sc = pr < 0.55 ? 1.0 : pr < 0.75 ? +(0.5 + Math.random() * 0.49).toFixed(2) : +(Math.random() * 0.5).toFixed(2);
            problemScores[p.id] = sc;
            totalEarned += sc * p.points;
            const correct = sc === 1.0;
            answers[p.id] = {
              answer_raw: p.format === "boolean_expression"
                ? (correct ? "A'D + BC + AB'C'" : ["AB + CD", "A'B", "B'C + D", "AC + BD'"][Math.floor(Math.random()*4)])
                : p.format === "value" ? (correct ? "1" : "0") : (correct ? "5" : String(Math.floor(Math.random()*10))),
              correct_answer: p.format === "boolean_expression" ? "A'D + BC + AB'C'" : p.format === "value" ? "1" : "5",
              score: sc, correct,
              feedback: correct ? "Correct!" : `Partially correct. ${Math.floor((1-sc)*16)}/16 rows mismatch.`,
              grading_tier: "deterministic",
              minterms: p.format === "boolean_expression" ? `m(${[...Array(7)].map(()=>Math.floor(Math.random()*16)).filter((v,j,a)=>a.indexOf(v)===j).sort((a,b)=>a-b).join(", ")})` : null,
              dont_cares: p.format === "boolean_expression" && Math.random() > 0.5 ? `d(${Math.floor(Math.random()*4)}, ${4+Math.floor(Math.random()*4)})` : null,
            };
          });
          totalScore = totalEarned / asn.totalPts;
        }
      }

      assignmentData[asn.id] = {
        status, totalScore: totalScore !== null ? +totalScore.toFixed(3) : null,
        totalEarned: totalScore !== null ? +(totalScore * asn.totalPts).toFixed(1) : null,
        attempts, problemScores, answers,
        submittedAt: status === "graded" ? "2026-03-01T" + String(8 + Math.floor(Math.random()*10)).padStart(2,"0") + ":00:00Z" : null,
      };
    });

    return { id: uid, name, email, section, assignmentData };
  });
}

const STUDENTS = makeStudents();

function getAsnStats(asnId) {
  const graded = STUDENTS.filter(s => s.assignmentData[asnId]?.status === "graded");
  const scores = graded.map(s => s.assignmentData[asnId].totalScore).sort((a,b) => a - b);
  if (scores.length === 0) return { mean: 0, median: 0, min: 0, max: 0, stdev: 0, submitted: 0, inProgress: 0, notStarted: 0 };
  const mean = scores.reduce((a,b) => a+b, 0) / scores.length;
  const median = scores.length % 2 === 0 ? (scores[scores.length/2-1] + scores[scores.length/2]) / 2 : scores[Math.floor(scores.length/2)];
  const variance = scores.reduce((s, v) => s + (v - mean) ** 2, 0) / scores.length;
  return {
    mean, median, min: scores[0], max: scores[scores.length-1], stdev: Math.sqrt(variance),
    submitted: graded.length,
    inProgress: STUDENTS.filter(s => s.assignmentData[asnId]?.status === "in_progress").length,
    notStarted: STUDENTS.filter(s => s.assignmentData[asnId]?.status === "not_started").length,
  };
}

function getDistribution(asnId) {
  const bins = Array(10).fill(0);
  STUDENTS.filter(s => s.assignmentData[asnId]?.status === "graded").forEach(s => {
    const b = Math.min(9, Math.floor(s.assignmentData[asnId].totalScore * 10));
    bins[b]++;
  });
  return bins.map((count, i) => ({ label: `${i*10}`, count }));
}

function getProblemStats(asn) {
  if (!asn.problems.length) return [];
  const graded = STUDENTS.filter(s => s.assignmentData[asn.id]?.status === "graded");
  return asn.problems.map(p => {
    const withScore = graded.filter(s => s.assignmentData[asn.id].problemScores[p.id] !== undefined);
    const correct = withScore.filter(s => s.assignmentData[asn.id].problemScores[p.id] === 1.0).length;
    const avg = withScore.length > 0 ? withScore.reduce((s, st) => s + st.assignmentData[asn.id].problemScores[p.id], 0) / withScore.length : 0;
    const wrongAnswers = {};
    withScore.filter(s => s.assignmentData[asn.id].problemScores[p.id] < 1.0 && s.assignmentData[asn.id].answers[p.id])
      .forEach(s => { const a = s.assignmentData[asn.id].answers[p.id].answer_raw; wrongAnswers[a] = (wrongAnswers[a] || 0) + 1; });
    const topErrors = Object.entries(wrongAnswers).sort((a,b) => b[1] - a[1]).slice(0, 3).map(([answer, count]) => ({ answer, count }));
    return { ...p, pctCorrect: withScore.length > 0 ? correct / withScore.length : 0, avgScore: avg, topErrors };
  });
}

// ── SHARED COMPONENTS ──

function ScoreCell({ score, size }) {
  if (score === null || score === undefined) return <span style={{ color: "#ccc" }}>—</span>;
  const pct = Math.round(score * 100);
  const bg = pct >= 80 ? "#e8f5e9" : pct >= 50 ? "#fff8e1" : "#ffebee";
  const color = pct >= 80 ? "#2e7d32" : pct >= 50 ? "#f57f17" : "#c62828";
  return (
    <span style={{ background: bg, color, padding: "2px 8px", borderRadius: 4, fontSize: size || 12, fontWeight: 600, fontFamily: "'IBM Plex Mono', monospace" }}>
      {pct}%
    </span>
  );
}

function StatusBadge({ status }) {
  const map = {
    graded: { bg: "#e8f5e9", color: "#2e7d32", text: "Graded" },
    in_progress: { bg: "#fff8e1", color: "#f57f17", text: "In Progress" },
    not_started: { bg: "#f5f5f5", color: "#999", text: "Not Started" },
  };
  const s = map[status] || map.not_started;
  return <span style={{ background: s.bg, color: s.color, padding: "2px 10px", borderRadius: 10, fontSize: 11, fontWeight: 600 }}>{s.text}</span>;
}

function ActiveBadge({ active }) {
  return (
    <span style={{ background: active ? "#e8f5e9" : "#f5f5f5", color: active ? "#2e7d32" : "#999",
      padding: "2px 10px", borderRadius: 10, fontSize: 11, fontWeight: 600 }}>
      {active ? "Active" : "Closed"}
    </span>
  );
}

function TypeBadge({ type }) {
  const colors = {
    "PSET": { bg: "#E3F2FD", color: "#1565C0" },
    "Quiz": { bg: "#F3E5F5", color: "#7B1FA2" },
    "Midterm": { bg: "#FFF3E0", color: "#E65100" },
    "Design Assignment": { bg: "#E8F5E9", color: "#2E7D32" },
    "Final Exam": { bg: "#FCE4EC", color: "#C62828" },
  };
  const c = colors[type] || { bg: "#f5f5f5", color: "#666" };
  return <span style={{ background: c.bg, color: c.color, padding: "2px 10px", borderRadius: 10, fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.03em" }}>{type}</span>;
}

function Header({ children, right }) {
  return (
    <div style={S.hdr}>
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <span style={S.logo}>AutoTA</span>
        <span style={S.hdrSep}>·</span>
        <span style={S.hdrCourse}>{OFFERING.course}</span>
        <span style={S.hdrSep}>·</span>
        <span style={S.hdrLabel}>{children}</span>
      </div>
      <span style={S.hdrRight}>{right || OFFERING.instructor}</span>
    </div>
  );
}

// ── DASHBOARD ──

function Dashboard({ onViewAssignment, onViewRoster, onViewDetails }) {
  // Compute summary across all assignments
  const summaryByType = useMemo(() => {
    const byType = {};
    ASSIGNMENT_TYPES.forEach(t => { byType[t] = { type: t, count: 0, totalPts: 0, meanScore: [] }; });
    ASSIGNMENTS.forEach(asn => {
      const bt = byType[asn.type];
      bt.count++;
      bt.totalPts += asn.totalPts;
      const stats = getAsnStats(asn.id);
      if (stats.submitted > 0) bt.meanScore.push(stats.mean);
    });
    Object.values(byType).forEach(bt => {
      bt.avgMean = bt.meanScore.length > 0 ? bt.meanScore.reduce((a,b)=>a+b,0) / bt.meanScore.length : null;
    });
    return byType;
  }, []);

  // Overall class stats
  const overallStats = useMemo(() => {
    const gradedAsns = ASSIGNMENTS.filter(a => getAsnStats(a.id).submitted > 0);
    const allMeans = gradedAsns.map(a => getAsnStats(a.id).mean);
    const overallMean = allMeans.length ? allMeans.reduce((a,b)=>a+b,0) / allMeans.length : 0;
    const totalSubmitted = ASSIGNMENTS.reduce((s, a) => s + getAsnStats(a.id).submitted, 0);
    const totalPossible = ASSIGNMENTS.length * TOTAL_ENROLLED;
    return { overallMean, submissionRate: totalPossible > 0 ? totalSubmitted / totalPossible : 0, gradedAsns: gradedAsns.length };
  }, []);

  return (
    <div style={S.page}>
      <Header>Instructor Dashboard</Header>
      <div style={S.content}>

        {/* Top summary cards */}
        <div style={S.summaryRow}>
          <div style={S.summaryCard}>
            <p style={S.summaryNum}>{TOTAL_ENROLLED}</p>
            <p style={S.summaryLabel}>Enrolled</p>
            <p style={{ fontSize: 11, color: "#aaa", margin: "2px 0 0" }}>{SECTIONS.map(s => `${s.label}: ${s.count}`).join(" · ")}</p>
          </div>
          <div style={S.summaryCard}>
            <p style={S.summaryNum}>{ASSIGNMENTS.length}</p>
            <p style={S.summaryLabel}>Assignments</p>
            <p style={{ fontSize: 11, color: "#aaa", margin: "2px 0 0" }}>{ASSIGNMENTS.filter(a=>a.isActive).length} active</p>
          </div>
          <div style={S.summaryCard}>
            <p style={S.summaryNum}>{Math.round(overallStats.overallMean * 100)}%</p>
            <p style={S.summaryLabel}>Class Average</p>
            <p style={{ fontSize: 11, color: "#aaa", margin: "2px 0 0" }}>across {overallStats.gradedAsns} graded</p>
          </div>
          <div style={S.summaryCard}>
            <p style={S.summaryNum}>{Math.round(overallStats.submissionRate * 100)}%</p>
            <p style={S.summaryLabel}>Submission Rate</p>
            <p style={{ fontSize: 11, color: "#aaa", margin: "2px 0 0" }}>overall</p>
          </div>
        </div>

        {/* Summary table by type */}
        <div style={S.card}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
            <h3 style={S.cardTitle}>Summary by Category</h3>
            <button style={S.btnText} onClick={onViewRoster}>View Full Roster →</button>
          </div>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
            <thead>
              <tr style={{ borderBottom: "2px solid #e8e8e8" }}>
                <th style={S.th}>Category</th>
                <th style={S.thC}>Count</th>
                <th style={S.thC}>Total Points</th>
                <th style={S.thC}>Avg Class Mean</th>
                <th style={S.thC}>Status</th>
              </tr>
            </thead>
            <tbody>
              {ASSIGNMENT_TYPES.map(t => {
                const bt = summaryByType[t];
                const activeCount = ASSIGNMENTS.filter(a => a.type === t && a.isActive).length;
                return (
                  <tr key={t} style={{ borderBottom: "1px solid #f0f0f0" }}>
                    <td style={S.td}><TypeBadge type={t} /></td>
                    <td style={S.tdC}>{bt.count}</td>
                    <td style={S.tdC}>{bt.totalPts} pts</td>
                    <td style={S.tdC}>{bt.avgMean !== null ? <ScoreCell score={bt.avgMean} /> : "—"}</td>
                    <td style={S.tdC}>{activeCount > 0 ? <span style={{ color: "#2e7d32", fontSize: 12 }}>{activeCount} active</span> : <span style={{ color: "#999", fontSize: 12 }}>All closed</span>}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Assignment list */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", margin: "24px 0 12px" }}>
          <h3 style={{ fontSize: 15, fontWeight: 700, color: "#1a1a1a", margin: 0 }}>All Assignments</h3>
          <button style={S.btnPrimary} onClick={onViewDetails}>View Full Gradebook →</button>
        </div>

        {ASSIGNMENTS.map(asn => {
          const stats = getAsnStats(asn.id);
          return (
            <div key={asn.id} style={S.asnCard}>
              <div style={S.asnTop}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                    <h3 style={S.asnTitle}>{asn.title}</h3>
                    <TypeBadge type={asn.type} />
                    <ActiveBadge active={asn.isActive} />
                  </div>
                  <p style={S.asnMeta}>{asn.totalPts} pts · {asn.maxAttempts} attempt{asn.maxAttempts > 1 ? "s" : ""} max · Due {new Date(asn.closesAt).toLocaleDateString()}</p>
                </div>
                <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                  <button style={S.btnExport} onClick={() => alert(`Export ${asn.id} CSV`)}>Export</button>
                  <button style={S.btnPrimarySmall} onClick={() => onViewAssignment(asn.id)}>Details →</button>
                </div>
              </div>
              <div style={S.progressTrack}>
                <div style={{ ...S.progressFill, width: `${(stats.submitted / TOTAL_ENROLLED) * 100}%` }} />
              </div>
              <div style={S.asnStatsRow}>
                <span style={S.asnStatPill}>{stats.submitted}/{TOTAL_ENROLLED} submitted</span>
                {stats.inProgress > 0 && <span style={{ ...S.asnStatPill, background: "#FFF8E1", color: "#F57F17" }}>{stats.inProgress} in progress</span>}
                {stats.notStarted > 0 && <span style={{ ...S.asnStatPill, background: "#f5f5f5", color: "#999" }}>{stats.notStarted} not started</span>}
                <span style={{ flex: 1 }} />
                {stats.submitted > 0 && <>
                  <span style={S.statMini}>μ {Math.round(stats.mean * 100)}%</span>
                  <span style={S.statMini}>med {Math.round(stats.median * 100)}%</span>
                  <span style={S.statMini}>σ {Math.round(stats.stdev * 100)}%</span>
                </>}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── FULL GRADEBOOK (View Details) ──

function FullGradebook({ onBack, onViewAssignment, onViewStudent }) {
  const [search, setSearch] = useState("");
  const [sectionFilter, setSectionFilter] = useState("all");
  const [typeFilter, setTypeFilter] = useState("all");
  const [sortCol, setSortCol] = useState("name");
  const [sortDir, setSortDir] = useState("asc");

  const visibleAssignments = useMemo(() => {
    if (typeFilter === "all") return ASSIGNMENTS;
    return ASSIGNMENTS.filter(a => a.type === typeFilter);
  }, [typeFilter]);

  const filtered = useMemo(() => {
    let list = [...STUDENTS];
    if (search) {
      const q = search.toLowerCase();
      list = list.filter(s => s.name.toLowerCase().includes(q) || s.id.toLowerCase().includes(q));
    }
    if (sectionFilter !== "all") list = list.filter(s => s.section === sectionFilter);

    list.sort((a, b) => {
      let va, vb;
      if (sortCol === "name") { va = a.name; vb = b.name; }
      else if (sortCol === "overall") {
        const getOverall = (st) => {
          const scores = visibleAssignments.map(asn => st.assignmentData[asn.id]?.totalScore).filter(s => s !== null && s !== undefined);
          return scores.length ? scores.reduce((a,b)=>a+b,0) / scores.length : -1;
        };
        va = getOverall(a); vb = getOverall(b);
      } else {
        va = a.assignmentData[sortCol]?.totalScore ?? -1;
        vb = b.assignmentData[sortCol]?.totalScore ?? -1;
      }
      if (va < vb) return sortDir === "asc" ? -1 : 1;
      if (va > vb) return sortDir === "asc" ? 1 : -1;
      return 0;
    });
    return list;
  }, [search, sectionFilter, sortCol, sortDir, visibleAssignments]);

  const toggleSort = (col) => {
    if (sortCol === col) setSortDir(d => d === "asc" ? "desc" : "asc");
    else { setSortCol(col); setSortDir("asc"); }
  };

  const Arrow = ({ col }) => (
    <span style={{ opacity: sortCol === col ? 1 : 0.3, fontSize: 9, marginLeft: 2 }}>
      {sortCol === col && sortDir === "desc" ? "▼" : "▲"}
    </span>
  );

  // Compute overall average for each student across visible assignments
  const getStudentOverall = (student) => {
    const scores = visibleAssignments
      .map(a => student.assignmentData[a.id]?.totalScore)
      .filter(s => s !== null && s !== undefined);
    return scores.length ? scores.reduce((a,b)=>a+b,0) / scores.length : null;
  };

  return (
    <div style={S.page}>
      <Header>Full Gradebook</Header>
      <div style={S.content}>
        <button style={S.backBtn} onClick={onBack}>← Dashboard</button>

        {/* Controls */}
        <div style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 14, flexWrap: "wrap" }}>
          <input style={S.searchInput} placeholder="Search name or UID..." value={search} onChange={e => setSearch(e.target.value)} />
          <select style={S.selectInput} value={sectionFilter} onChange={e => setSectionFilter(e.target.value)}>
            <option value="all">All Sections</option>
            {SECTIONS.map(s => <option key={s.label} value={s.label}>{s.label}</option>)}
          </select>
          <select style={{ ...S.selectInput, minWidth: 170 }} value={typeFilter} onChange={e => setTypeFilter(e.target.value)}>
            <option value="all">All Types ({ASSIGNMENTS.length})</option>
            {ASSIGNMENT_TYPES.map(t => (
              <option key={t} value={t}>{t} ({ASSIGNMENTS.filter(a=>a.type===t).length})</option>
            ))}
          </select>
          <div style={{ flex: 1 }} />
          <button style={S.btnExport} onClick={() => alert("Full gradebook CSV exported")}>Export CSV</button>
          <button style={S.btnExport} onClick={() => alert("BruinLearn CSV exported")}>Export BruinLearn</button>
        </div>

        {/* Table */}
        <div style={{ overflowX: "auto", borderRadius: 8, border: "1px solid #e0e0e0" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
            <thead>
              <tr style={{ background: "#f8f8f8" }}>
                <th style={{ ...S.thClick, textAlign: "left", minWidth: 160, position: "sticky", left: 0, background: "#f8f8f8", zIndex: 2 }} onClick={() => toggleSort("name")}>
                  Student <Arrow col="name" />
                </th>
                <th style={{ ...S.thSmall, minWidth: 45 }}>Sec</th>
                {visibleAssignments.map(a => (
                  <th key={a.id} style={S.thClick} onClick={() => toggleSort(a.id)}>
                    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 2, cursor: "pointer" }}>
                      <span style={{ fontSize: 11, fontWeight: 700 }}>{a.id.toUpperCase()}</span>
                      <span style={{ fontSize: 9, color: "#aaa", fontWeight: 400 }}>({a.totalPts})</span>
                    </div>
                    <Arrow col={a.id} />
                  </th>
                ))}
                <th style={{ ...S.thClick, borderLeft: "2px solid #ddd" }} onClick={() => toggleSort("overall")}>
                  Overall <Arrow col="overall" />
                </th>
              </tr>
              {/* Type indicator row */}
              <tr style={{ background: "#f8f8f8", borderBottom: "2px solid #e0e0e0" }}>
                <td style={{ position: "sticky", left: 0, background: "#f8f8f8", zIndex: 2 }} />
                <td />
                {visibleAssignments.map(a => (
                  <td key={a.id} style={{ padding: "2px 4px", textAlign: "center" }}>
                    <TypeBadge type={a.type} />
                  </td>
                ))}
                <td style={{ borderLeft: "2px solid #ddd" }} />
              </tr>
            </thead>
            <tbody>
              {filtered.map((s, i) => {
                const overall = getStudentOverall(s);
                return (
                  <tr key={s.id} style={{ background: i % 2 === 0 ? "#fff" : "#fafafa", cursor: "pointer" }}
                    onClick={() => onViewStudent(s.id)}>
                    <td style={{ ...S.tdName, position: "sticky", left: 0, background: i % 2 === 0 ? "#fff" : "#fafafa", zIndex: 1 }}>
                      <span style={{ fontWeight: 500 }}>{s.name}</span>
                      <br />
                      <span style={{ fontSize: 10, color: "#aaa" }}>{s.id}</span>
                    </td>
                    <td style={S.tdC}>{s.section}</td>
                    {visibleAssignments.map(a => {
                      const ad = s.assignmentData[a.id];
                      return (
                        <td key={a.id} style={S.tdC}>
                          {ad?.status === "graded" ? <ScoreCell score={ad.totalScore} size={11} /> :
                           ad?.status === "in_progress" ? <span style={{ fontSize: 10, color: "#F57F17" }}>⏳</span> :
                           <span style={{ color: "#ddd" }}>—</span>}
                        </td>
                      );
                    })}
                    <td style={{ ...S.tdC, borderLeft: "2px solid #eee", fontWeight: 700, fontSize: 13 }}>
                      {overall !== null ? <ScoreCell score={overall} /> : "—"}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <p style={{ fontSize: 12, color: "#999", marginTop: 8 }}>
          {filtered.length} students · {visibleAssignments.length} assignments shown
        </p>
      </div>
    </div>
  );
}

// ── ASSIGNMENT DETAIL ──

function AssignmentDetail({ assignmentId, onBack, onViewStudent }) {
  const asn = ASSIGNMENTS.find(a => a.id === assignmentId);
  const stats = getAsnStats(assignmentId);
  const dist = getDistribution(assignmentId);
  const problemStats = getProblemStats(asn);
  const maxBin = Math.max(...dist.map(d => d.count), 1);

  const [search, setSearch] = useState("");
  const [sectionFilter, setSectionFilter] = useState("all");
  const [sortCol, setSortCol] = useState("name");
  const [sortDir, setSortDir] = useState("asc");

  const filtered = useMemo(() => {
    let list = [...STUDENTS];
    if (search) {
      const q = search.toLowerCase();
      list = list.filter(s => s.name.toLowerCase().includes(q) || s.id.toLowerCase().includes(q));
    }
    if (sectionFilter !== "all") list = list.filter(s => s.section === sectionFilter);
    list.sort((a, b) => {
      let va, vb;
      if (sortCol === "name") { va = a.name; vb = b.name; }
      else if (sortCol === "total") { va = a.assignmentData[assignmentId]?.totalScore ?? -1; vb = b.assignmentData[assignmentId]?.totalScore ?? -1; }
      else if (sortCol === "status") { va = a.assignmentData[assignmentId]?.status ?? ""; vb = b.assignmentData[assignmentId]?.status ?? ""; }
      else { va = a.assignmentData[assignmentId]?.problemScores?.[sortCol] ?? -1; vb = b.assignmentData[assignmentId]?.problemScores?.[sortCol] ?? -1; }
      if (va < vb) return sortDir === "asc" ? -1 : 1;
      if (va > vb) return sortDir === "asc" ? 1 : -1;
      return 0;
    });
    return list;
  }, [search, sectionFilter, sortCol, sortDir, assignmentId]);

  const toggleSort = (col) => {
    if (sortCol === col) setSortDir(d => d === "asc" ? "desc" : "asc");
    else { setSortCol(col); setSortDir("asc"); }
  };
  const Arrow = ({ col }) => <span style={{ opacity: sortCol === col ? 1 : 0.3, fontSize: 9, marginLeft: 2 }}>{sortCol === col && sortDir === "desc" ? "▼" : "▲"}</span>;

  return (
    <div style={S.page}>
      <Header>{asn.title}</Header>
      <div style={S.content}>
        <button style={S.backBtn} onClick={onBack}>← Dashboard</button>

        {/* Header card */}
        <div style={{ ...S.card, marginBottom: 16 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                <TypeBadge type={asn.type} />
                <ActiveBadge active={asn.isActive} />
                <span style={{ fontSize: 12, color: "#999" }}>{asn.totalPts} pts · {asn.maxAttempts} attempts · Due {new Date(asn.closesAt).toLocaleDateString()}</span>
              </div>
            </div>
            <div style={{ display: "flex", gap: 8 }}>
              <button style={S.btnExport} onClick={() => alert("Export BruinLearn CSV")}>Export BruinLearn</button>
              <button style={S.btnExport} onClick={() => alert("Export Full CSV")}>Export Full</button>
            </div>
          </div>
        </div>

        <div style={{ display: "flex", gap: 16, marginBottom: 20 }}>
          {/* Distribution */}
          <div style={{ ...S.card, flex: 2 }}>
            <p style={S.cardTitle}>Score Distribution</p>
            <p style={{ fontSize: 12, color: "#888", margin: "0 0 12px" }}>μ = {Math.round(stats.mean*100)}% · med = {Math.round(stats.median*100)}% · σ = {Math.round(stats.stdev*100)}%</p>
            <div style={{ display: "flex", alignItems: "flex-end", gap: 4, height: 110 }}>
              {dist.map((d, i) => (
                <div key={i} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center" }}>
                  <span style={{ fontSize: 10, color: "#666", marginBottom: 2 }}>{d.count || ""}</span>
                  <div style={{ width: "100%", borderRadius: "3px 3px 0 0", height: `${Math.max(3, (d.count / maxBin) * 90)}px`,
                    background: i >= 8 ? "#2774AE" : i >= 5 ? "#64B5F6" : i >= 3 ? "#FFD54F" : "#EF9A9A" }} />
                  <span style={{ fontSize: 9, color: "#999", marginTop: 3 }}>{d.label}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Problem breakdown (if has problems) */}
          {problemStats.length > 0 && (
            <div style={{ ...S.card, flex: 3 }}>
              <p style={S.cardTitle}>Problem Breakdown</p>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
                <thead>
                  <tr style={{ borderBottom: "2px solid #e8e8e8" }}>
                    <th style={S.th}>Problem</th><th style={S.thC}>Pts</th><th style={S.thC}>% Correct</th><th style={S.thC}>Avg</th><th style={S.th}>Top Error</th>
                  </tr>
                </thead>
                <tbody>
                  {problemStats.map(p => (
                    <tr key={p.id} style={{ borderBottom: "1px solid #f0f0f0" }}>
                      <td style={S.td}><span style={{ fontWeight: 600, color: "#2774AE" }}>{p.label}</span></td>
                      <td style={S.tdC}>{p.points}</td>
                      <td style={S.tdC}><ScoreCell score={p.pctCorrect} size={11} /></td>
                      <td style={S.tdC}><ScoreCell score={p.avgScore} size={11} /></td>
                      <td style={{ ...S.td, fontFamily: "'IBM Plex Mono', monospace", fontSize: 11, color: "#888" }}>
                        {p.topErrors[0] ? `${p.topErrors[0].answer} (${p.topErrors[0].count})` : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Grade table */}
        <div style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 10 }}>
          <input style={S.searchInput} placeholder="Search..." value={search} onChange={e => setSearch(e.target.value)} />
          <select style={S.selectInput} value={sectionFilter} onChange={e => setSectionFilter(e.target.value)}>
            <option value="all">All Sections</option>
            {SECTIONS.map(s => <option key={s.label} value={s.label}>{s.label}</option>)}
          </select>
        </div>
        <div style={{ overflowX: "auto", borderRadius: 8, border: "1px solid #e0e0e0" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
            <thead>
              <tr style={{ background: "#f8f8f8" }}>
                <th style={{ ...S.thClick, textAlign: "left", minWidth: 150 }} onClick={() => toggleSort("name")}>Student <Arrow col="name" /></th>
                <th style={S.thSmall}>Sec</th>
                <th style={S.thSmall}>Att.</th>
                {asn.problems.length > 0 && asn.problems.map(p => (
                  <th key={p.id} style={S.thClick} onClick={() => toggleSort(p.id)}>{p.label} <span style={{ fontSize: 9, color: "#aaa" }}>({p.points})</span> <Arrow col={p.id} /></th>
                ))}
                <th style={S.thClick} onClick={() => toggleSort("total")}>Total <Arrow col="total" /></th>
                <th style={S.thClick} onClick={() => toggleSort("status")}>Status <Arrow col="status" /></th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((s, i) => {
                const ad = s.assignmentData[assignmentId];
                return (
                  <tr key={s.id} style={{ background: i % 2 === 0 ? "#fff" : "#fafafa", cursor: "pointer" }} onClick={() => onViewStudent(s.id)}>
                    <td style={S.tdName}><span style={{ fontWeight: 500 }}>{s.name}</span> <span style={{ fontSize: 10, color: "#aaa" }}>{s.id}</span></td>
                    <td style={S.tdC}>{s.section}</td>
                    <td style={S.tdC}>{ad?.attempts || 0}</td>
                    {asn.problems.length > 0 && asn.problems.map(p => (
                      <td key={p.id} style={S.tdC}><ScoreCell score={ad?.problemScores?.[p.id]} size={11} /></td>
                    ))}
                    <td style={S.tdC}>{ad?.totalScore !== null && ad?.totalScore !== undefined ? <span style={{ fontWeight: 700 }}>{Math.round(ad.totalScore * 100)}%</span> : "—"}</td>
                    <td style={S.tdC}><StatusBadge status={ad?.status || "not_started"} /></td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <p style={{ fontSize: 12, color: "#999", marginTop: 8 }}>{filtered.length} students</p>
      </div>
    </div>
  );
}

// ── STUDENT DRILL-DOWN ──

function StudentDrillDown({ studentId, fromScreen, onBack }) {
  const student = STUDENTS.find(s => s.id === studentId);
  const [selectedAsn, setSelectedAsn] = useState(ASSIGNMENTS[ASSIGNMENTS.length - 1]?.id);
  const [overrideId, setOverrideId] = useState(null);
  const [overrideScore, setOverrideScore] = useState("");
  const [overrideFeedback, setOverrideFeedback] = useState("");
  const [overrides, setOverrides] = useState({});

  if (!student) return <div style={S.page}><Header>Student</Header><div style={S.content}><p>Not found.</p><button style={S.backBtn} onClick={onBack}>← Back</button></div></div>;

  const asn = ASSIGNMENTS.find(a => a.id === selectedAsn);
  const ad = student.assignmentData[selectedAsn];

  const startOverride = (pid) => {
    const ans = ad?.answers?.[pid];
    setOverrideId(pid);
    setOverrideScore(String(Math.round((overrides[`${selectedAsn}_${pid}`]?.score ?? ans?.score ?? 0) * 100)));
    setOverrideFeedback(overrides[`${selectedAsn}_${pid}`]?.feedback ?? ans?.feedback ?? "");
  };

  const saveOverride = (pid) => {
    setOverrides(prev => ({ ...prev, [`${selectedAsn}_${pid}`]: { score: parseInt(overrideScore) / 100, feedback: overrideFeedback } }));
    setOverrideId(null);
  };

  // Overall student stats
  const gradedAssignments = ASSIGNMENTS.filter(a => student.assignmentData[a.id]?.status === "graded");
  const overallAvg = gradedAssignments.length ? gradedAssignments.reduce((s, a) => s + student.assignmentData[a.id].totalScore, 0) / gradedAssignments.length : null;

  return (
    <div style={S.page}>
      <Header right={`${student.id} · ${student.email}`}>{student.name}</Header>
      <div style={S.content}>
        <button style={S.backBtn} onClick={onBack}>← {fromScreen === "gradebook" ? "Gradebook" : "Assignment"}</button>

        {/* Student header */}
        <div style={{ ...S.card, marginBottom: 16 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <h2 style={{ fontSize: 20, fontWeight: 700, margin: "0 0 4px" }}>{student.name}</h2>
              <p style={{ fontSize: 13, color: "#666", margin: 0 }}>{student.id} · {student.email} · Section {student.section}</p>
            </div>
            <div style={{ textAlign: "right" }}>
              <p style={{ fontSize: 28, fontWeight: 700, margin: 0 }}>{overallAvg !== null ? `${Math.round(overallAvg * 100)}%` : "—"}</p>
              <p style={{ fontSize: 12, color: "#888", margin: 0 }}>Overall Average · {gradedAssignments.length} graded</p>
            </div>
          </div>
        </div>

        {/* Assignment summary mini-table */}
        <div style={{ ...S.card, marginBottom: 16 }}>
          <p style={S.cardTitle}>All Assignments</p>
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
            {ASSIGNMENTS.map(a => {
              const d = student.assignmentData[a.id];
              const active = a.id === selectedAsn;
              return (
                <button key={a.id} onClick={() => setSelectedAsn(a.id)} style={{
                  padding: "6px 14px", borderRadius: 6, fontSize: 12, fontWeight: 600, cursor: "pointer",
                  border: active ? "2px solid #1a1a1a" : "1px solid #e0e0e0",
                  background: active ? "#1a1a1a" : "#fff", color: active ? "#fff" : "#333",
                  display: "flex", flexDirection: "column", alignItems: "center", gap: 2, minWidth: 65,
                }}>
                  <span>{a.id.toUpperCase()}</span>
                  <span style={{ fontSize: 10, fontWeight: 400, color: active ? "#ccc" : "#999" }}>
                    {d?.status === "graded" ? `${Math.round(d.totalScore * 100)}%` : d?.status === "in_progress" ? "⏳" : "—"}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Selected assignment detail */}
        {asn && (
          <div style={S.card}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
              <div>
                <h3 style={{ fontSize: 15, fontWeight: 700, margin: "0 0 4px" }}>{asn.title}</h3>
                <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
                  <TypeBadge type={asn.type} />
                  <StatusBadge status={ad?.status || "not_started"} />
                  <span style={{ fontSize: 12, color: "#999" }}>Attempt {ad?.attempts || 0} of {asn.maxAttempts}</span>
                </div>
              </div>
              {ad?.totalScore !== null && ad?.totalScore !== undefined && (
                <div style={{ textAlign: "right" }}>
                  <p style={{ fontSize: 24, fontWeight: 700, margin: 0 }}>{Math.round(ad.totalScore * 100)}%</p>
                  <p style={{ fontSize: 12, color: "#888", margin: 0 }}>{ad.totalEarned}/{asn.totalPts} pts</p>
                </div>
              )}
            </div>

            {/* Per-problem cards (if assignment has problems) */}
            {asn.problems.length > 0 && ad?.status === "graded" ? asn.problems.map(p => {
              const ans = ad.answers?.[p.id];
              const ov = overrides[`${selectedAsn}_${p.id}`];
              const score = ov ? ov.score : ans?.score;
              const feedback = ov ? ov.feedback : ans?.feedback;
              const isOverriding = overrideId === p.id;

              return (
                <div key={p.id} style={{ padding: "14px 0", borderTop: "1px solid #f0f0f0" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                        <span style={{ fontSize: 13, fontWeight: 700, color: "#2774AE" }}>{p.label}</span>
                        <span style={{ fontSize: 11, color: "#999" }}>{p.points} pts</span>
                        {ov && <span style={{ fontSize: 10, background: "#FFF3E0", color: "#E65100", padding: "1px 8px", borderRadius: 8, fontWeight: 600 }}>Overridden</span>}
                      </div>
                      {ans?.minterms && (
                        <p style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: 11, color: "#555", margin: "0 0 4px" }}>
                          {ans.minterms}{ans.dont_cares ? ` · ${ans.dont_cares}` : ""}
                        </p>
                      )}
                    </div>
                    <ScoreCell score={score} />
                  </div>

                  {ans && (
                    <>
                      <div style={{ display: "flex", gap: 16, margin: "8px 0", padding: "8px 12px", background: "#f8f8f8", borderRadius: 6 }}>
                        <div style={{ flex: 1 }}>
                          <p style={{ fontSize: 10, fontWeight: 700, color: "#999", textTransform: "uppercase", margin: "0 0 3px" }}>Student</p>
                          <p style={{ fontSize: 13, fontFamily: "'IBM Plex Mono', monospace", fontWeight: 600, margin: 0, color: ans.correct ? "#2e7d32" : "#c62828" }}>{ans.answer_raw}</p>
                        </div>
                        <div style={{ flex: 1 }}>
                          <p style={{ fontSize: 10, fontWeight: 700, color: "#999", textTransform: "uppercase", margin: "0 0 3px" }}>Correct</p>
                          <p style={{ fontSize: 13, fontFamily: "'IBM Plex Mono', monospace", fontWeight: 600, margin: 0, color: "#2e7d32" }}>{ans.correct_answer}</p>
                        </div>
                      </div>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <p style={{ fontSize: 12, color: "#666", margin: 0, flex: 1 }}>{feedback}</p>
                        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                          <span style={{ fontSize: 10, background: "#f0f0f0", color: "#888", padding: "2px 8px", borderRadius: 8 }}>{ov ? "human" : ans.grading_tier}</span>
                          {!isOverriding && <button style={S.overrideBtn} onClick={() => startOverride(p.id)}>✏️</button>}
                        </div>
                      </div>
                      {isOverriding && (
                        <div style={S.overridePanel}>
                          <p style={{ fontSize: 12, fontWeight: 700, color: "#E65100", margin: "0 0 8px" }}>Grade Override</p>
                          <div style={{ display: "flex", gap: 12, marginBottom: 8 }}>
                            <div>
                              <label style={{ fontSize: 11, color: "#888" }}>Score (%)</label>
                              <input type="number" min="0" max="100" style={{ ...S.overrideInput, width: 80 }} value={overrideScore} onChange={e => setOverrideScore(e.target.value)} />
                            </div>
                          </div>
                          <label style={{ fontSize: 11, color: "#888" }}>Feedback</label>
                          <textarea style={{ ...S.overrideInput, width: "100%", minHeight: 50, resize: "vertical" }} value={overrideFeedback} onChange={e => setOverrideFeedback(e.target.value)} />
                          <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
                            <button style={S.btnSaveOverride} onClick={() => saveOverride(p.id)}>Save</button>
                            <button style={S.btnCancel} onClick={() => setOverrideId(null)}>Cancel</button>
                          </div>
                        </div>
                      )}
                    </>
                  )}
                </div>
              );
            }) : ad?.status !== "graded" ? (
              <p style={{ color: "#999", fontSize: 13, fontStyle: "italic", marginTop: 12 }}>
                {ad?.status === "in_progress" ? "Student has not submitted yet." : "Student has not started this assignment."}
              </p>
            ) : (
              <p style={{ color: "#666", fontSize: 13, marginTop: 12 }}>
                Score: {Math.round(ad.totalScore * 100)}% ({ad.totalEarned}/{asn.totalPts} pts). Detailed problem breakdown not available for this assignment type.
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// ── STUDENT ROSTER ──

function StudentRoster({ onBack, onViewStudent }) {
  const [search, setSearch] = useState("");
  const filtered = useMemo(() => {
    if (!search) return STUDENTS;
    const q = search.toLowerCase();
    return STUDENTS.filter(s => s.name.toLowerCase().includes(q) || s.id.toLowerCase().includes(q) || s.email.toLowerCase().includes(q));
  }, [search]);

  return (
    <div style={S.page}>
      <Header>Student Roster</Header>
      <div style={S.content}>
        <button style={S.backBtn} onClick={onBack}>← Dashboard</button>
        <input style={{ ...S.searchInput, marginBottom: 16, maxWidth: 400 }} placeholder="Search name, UID, email..." value={search} onChange={e => setSearch(e.target.value)} />
        <div style={{ overflowX: "auto", borderRadius: 8, border: "1px solid #e0e0e0" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
            <thead>
              <tr style={{ background: "#f8f8f8" }}>
                <th style={{ ...S.th, minWidth: 140 }}>Name</th>
                <th style={S.thSmall}>UID</th>
                <th style={S.thSmall}>Email</th>
                <th style={S.thSmall}>Sec</th>
                {ASSIGNMENTS.map(a => <th key={a.id} style={S.thSmall}>{a.id.toUpperCase()}</th>)}
                <th style={{ ...S.thSmall, borderLeft: "2px solid #ddd" }}>Avg</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((s, i) => {
                const gradedScores = ASSIGNMENTS.map(a => s.assignmentData[a.id]?.totalScore).filter(v => v !== null && v !== undefined);
                const avg = gradedScores.length ? gradedScores.reduce((a,b)=>a+b,0) / gradedScores.length : null;
                return (
                  <tr key={s.id} style={{ background: i % 2 === 0 ? "#fff" : "#fafafa", cursor: "pointer" }} onClick={() => onViewStudent(s.id)}>
                    <td style={S.tdName}><span style={{ fontWeight: 500 }}>{s.name}</span></td>
                    <td style={S.tdC}><span style={{ fontSize: 10, fontFamily: "'IBM Plex Mono', monospace" }}>{s.id}</span></td>
                    <td style={S.tdC}><span style={{ fontSize: 11, color: "#666" }}>{s.email}</span></td>
                    <td style={S.tdC}>{s.section}</td>
                    {ASSIGNMENTS.map(a => {
                      const ad = s.assignmentData[a.id];
                      return <td key={a.id} style={S.tdC}>{ad?.status === "graded" ? <ScoreCell score={ad.totalScore} size={10} /> : ad?.status === "in_progress" ? <span style={{ fontSize: 10, color: "#F57F17" }}>⏳</span> : <span style={{ color: "#ddd" }}>—</span>}</td>;
                    })}
                    <td style={{ ...S.tdC, borderLeft: "2px solid #eee" }}>{avg !== null ? <ScoreCell score={avg} size={11} /> : "—"}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <p style={{ fontSize: 12, color: "#999", marginTop: 8 }}>{filtered.length} students</p>
      </div>
    </div>
  );
}

// ── MAIN APP ──

export default function InstructorDashboard() {
  const [screen, setScreen] = useState("dashboard");
  const [selectedAssignment, setSelectedAssignment] = useState(null);
  const [selectedStudent, setSelectedStudent] = useState(null);
  const [studentFrom, setStudentFrom] = useState("dashboard");

  const viewStudent = (id, from) => { setSelectedStudent(id); setStudentFrom(from); setScreen("student"); };

  if (screen === "dashboard") return (
    <Dashboard
      onViewAssignment={(id) => { setSelectedAssignment(id); setScreen("assignment"); }}
      onViewRoster={() => setScreen("roster")}
      onViewDetails={() => setScreen("gradebook")}
    />
  );
  if (screen === "gradebook") return (
    <FullGradebook
      onBack={() => setScreen("dashboard")}
      onViewAssignment={(id) => { setSelectedAssignment(id); setScreen("assignment"); }}
      onViewStudent={(id) => viewStudent(id, "gradebook")}
    />
  );
  if (screen === "assignment") return (
    <AssignmentDetail
      assignmentId={selectedAssignment}
      onBack={() => setScreen("dashboard")}
      onViewStudent={(id) => viewStudent(id, "assignment")}
    />
  );
  if (screen === "student") return (
    <StudentDrillDown
      studentId={selectedStudent}
      fromScreen={studentFrom}
      onBack={() => setScreen(studentFrom === "gradebook" ? "gradebook" : selectedAssignment ? "assignment" : "dashboard")}
    />
  );
  if (screen === "roster") return (
    <StudentRoster
      onBack={() => setScreen("dashboard")}
      onViewStudent={(id) => viewStudent(id, "roster")}
    />
  );
  return null;
}

// ── STYLES ──

const S = {
  page: { minHeight: "100vh", background: "#f0f0f0", fontFamily: "'IBM Plex Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif" },
  hdr: { display: "flex", justifyContent: "space-between", alignItems: "center", padding: "12px 28px", background: "#1a1a1a", color: "#fff", fontSize: 13, fontWeight: 500, position: "sticky", top: 0, zIndex: 50 },
  logo: { fontSize: 16, fontWeight: 700, letterSpacing: "-0.02em" },
  hdrSep: { color: "#555" },
  hdrCourse: { fontWeight: 600 },
  hdrLabel: { color: "#aaa" },
  hdrRight: { color: "#aaa", fontSize: 12 },
  content: { maxWidth: 1200, margin: "0 auto", padding: "20px 24px" },
  backBtn: { background: "none", border: "none", color: "#2774AE", fontSize: 13, fontWeight: 600, cursor: "pointer", padding: 0, marginBottom: 16 },

  summaryRow: { display: "flex", gap: 12, marginBottom: 20 },
  summaryCard: { flex: 1, background: "#fff", borderRadius: 8, padding: "16px 20px", boxShadow: "0 1px 3px rgba(0,0,0,0.06)" },
  summaryNum: { fontSize: 22, fontWeight: 700, color: "#1a1a1a", margin: "0 0 2px" },
  summaryLabel: { fontSize: 12, color: "#888", margin: 0 },

  card: { background: "#fff", borderRadius: 8, padding: "20px 24px", boxShadow: "0 1px 3px rgba(0,0,0,0.06)", marginBottom: 12 },
  cardTitle: { fontSize: 14, fontWeight: 700, color: "#1a1a1a", margin: "0 0 12px" },

  asnCard: { background: "#fff", borderRadius: 8, padding: "18px 22px", boxShadow: "0 1px 3px rgba(0,0,0,0.06)", marginBottom: 10 },
  asnTop: { display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 10 },
  asnTitle: { fontSize: 15, fontWeight: 700, color: "#1a1a1a", margin: 0 },
  asnMeta: { fontSize: 12, color: "#888", margin: "4px 0 0" },
  progressTrack: { height: 5, background: "#e8e8e8", borderRadius: 3, overflow: "hidden", marginBottom: 8 },
  progressFill: { height: "100%", background: "#2774AE", borderRadius: 3 },
  asnStatsRow: { display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" },
  asnStatPill: { fontSize: 11, padding: "2px 10px", borderRadius: 10, background: "#E3F2FD", color: "#1565C0", fontWeight: 500 },
  statMini: { fontSize: 12, color: "#888", fontWeight: 500, fontFamily: "'IBM Plex Mono', monospace" },

  btnPrimary: { padding: "8px 18px", background: "#2774AE", color: "#fff", border: "none", borderRadius: 6, fontSize: 13, fontWeight: 600, cursor: "pointer" },
  btnPrimarySmall: { padding: "6px 14px", background: "#2774AE", color: "#fff", border: "none", borderRadius: 6, fontSize: 12, fontWeight: 600, cursor: "pointer" },
  btnExport: { padding: "7px 14px", background: "#fff", color: "#333", border: "1px solid #d0d0d0", borderRadius: 6, fontSize: 12, fontWeight: 500, cursor: "pointer" },
  btnText: { background: "none", border: "none", color: "#2774AE", fontSize: 13, fontWeight: 600, cursor: "pointer", padding: 0 },

  th: { textAlign: "left", padding: "8px 10px", fontSize: 11, fontWeight: 700, color: "#888", textTransform: "uppercase", letterSpacing: "0.04em" },
  thC: { textAlign: "center", padding: "8px 8px", fontSize: 11, fontWeight: 700, color: "#888", textTransform: "uppercase" },
  thSmall: { textAlign: "center", padding: "8px 6px", fontSize: 10, fontWeight: 700, color: "#888", textTransform: "uppercase" },
  thClick: { textAlign: "center", padding: "8px 8px", fontSize: 10, fontWeight: 700, color: "#888", textTransform: "uppercase", cursor: "pointer", userSelect: "none" },
  td: { padding: "8px 10px" },
  tdC: { padding: "8px 6px", textAlign: "center" },
  tdName: { padding: "10px 10px" },
  searchInput: { padding: "7px 12px", fontSize: 13, border: "1px solid #d0d0d0", borderRadius: 6, outline: "none", width: 220, fontFamily: "'IBM Plex Sans', sans-serif" },
  selectInput: { padding: "7px 10px", fontSize: 13, border: "1px solid #d0d0d0", borderRadius: 6, outline: "none", background: "#fff", cursor: "pointer" },

  overrideBtn: { background: "none", border: "1px solid #e0e0e0", borderRadius: 4, padding: "2px 6px", cursor: "pointer", fontSize: 13 },
  overridePanel: { marginTop: 10, padding: "12px 14px", background: "#FFF8E1", border: "1px solid #FFE082", borderRadius: 6 },
  overrideInput: { display: "block", padding: "5px 8px", fontSize: 13, border: "1px solid #d0d0d0", borderRadius: 4, outline: "none", marginTop: 4, boxSizing: "border-box", fontFamily: "'IBM Plex Sans', sans-serif" },
  btnSaveOverride: { padding: "5px 14px", background: "#2e7d32", color: "#fff", border: "none", borderRadius: 5, fontSize: 12, fontWeight: 600, cursor: "pointer" },
  btnCancel: { padding: "5px 14px", background: "#fff", color: "#666", border: "1px solid #d0d0d0", borderRadius: 5, fontSize: 12, fontWeight: 500, cursor: "pointer" },
};
