import { useState, useEffect, useMemo } from "react";
import {
  getInstructorDashboard,
  getInstructorGradebook,
  getInstructorAssignment,
  getInstructorStudent,
  getInstructorRoster,
} from "../api";

// ── Styles ────────────────────────────────────────────────────────────────────

const S = {
  page: {
    minHeight: "100vh",
    background: "#f0f0f0",
    fontFamily: "'IBM Plex Sans', -apple-system, BlinkMacSystemFont, sans-serif",
    fontSize: 14,
  },
  header: {
    position: "sticky",
    top: 0,
    zIndex: 100,
    background: "#1a1a1a",
    color: "#fff",
    padding: "0 24px",
    height: 48,
    display: "flex",
    alignItems: "center",
    gap: 16,
  },
  headerLogo: { fontSize: 16, fontWeight: 700, letterSpacing: "-0.5px" },
  headerSep: { color: "#555", fontSize: 18 },
  headerCourse: { fontSize: 13, color: "#bbb" },
  headerLabel: {
    fontSize: 11, fontWeight: 600, letterSpacing: "0.05em",
    background: "#333", borderRadius: 4, padding: "2px 8px", color: "#aaa",
  },
  headerRight: { marginLeft: "auto", fontSize: 12, color: "#999" },
  content: { maxWidth: 1200, margin: "0 auto", padding: "24px 24px" },
  nav: {
    display: "flex", gap: 4, marginBottom: 20,
    borderBottom: "1px solid #ddd", paddingBottom: 0,
  },
  navTab: {
    padding: "8px 16px", cursor: "pointer", fontSize: 13, fontWeight: 500,
    border: "none", background: "transparent", borderBottom: "2px solid transparent",
    color: "#666", marginBottom: -1,
  },
  navTabActive: {
    padding: "8px 16px", cursor: "pointer", fontSize: 13, fontWeight: 600,
    border: "none", background: "transparent", borderBottom: "2px solid #2774AE",
    color: "#2774AE", marginBottom: -1,
  },
  card: {
    background: "#fff", borderRadius: 8, boxShadow: "0 1px 3px rgba(0,0,0,0.08)",
    padding: 20, marginBottom: 16,
  },
  cardTitle: { fontSize: 13, fontWeight: 600, color: "#333", marginBottom: 12, textTransform: "uppercase", letterSpacing: "0.05em" },
  summaryGrid: { display: "flex", gap: 12, flexWrap: "wrap", marginBottom: 16 },
  summaryCard: {
    background: "#fff", borderRadius: 8, padding: "16px 20px",
    boxShadow: "0 1px 3px rgba(0,0,0,0.08)", flex: "1 1 140px", minWidth: 140,
  },
  summaryNum: { fontSize: 22, fontWeight: 700, color: "#1a1a1a" },
  summaryLabel: { fontSize: 12, color: "#888", marginTop: 2 },
  table: { width: "100%", borderCollapse: "collapse" },
  th: {
    padding: "8px 12px", textAlign: "left", fontSize: 11, fontWeight: 600,
    color: "#888", textTransform: "uppercase", letterSpacing: "0.05em",
    borderBottom: "1px solid #eee", whiteSpace: "nowrap",
  },
  thC: {
    padding: "8px 12px", textAlign: "center", fontSize: 11, fontWeight: 600,
    color: "#888", textTransform: "uppercase", letterSpacing: "0.05em",
    borderBottom: "1px solid #eee", whiteSpace: "nowrap",
  },
  thClick: {
    padding: "8px 12px", textAlign: "left", fontSize: 11, fontWeight: 600,
    color: "#888", textTransform: "uppercase", letterSpacing: "0.05em",
    borderBottom: "1px solid #eee", whiteSpace: "nowrap", cursor: "pointer",
    userSelect: "none",
  },
  td: {
    padding: "9px 12px", borderBottom: "1px solid #f0f0f0",
    fontSize: 13, color: "#333",
  },
  tdC: {
    padding: "9px 12px", borderBottom: "1px solid #f0f0f0",
    fontSize: 13, color: "#333", textAlign: "center",
  },
  tdName: {
    padding: "9px 12px", borderBottom: "1px solid #f0f0f0",
    fontSize: 13, color: "#2774AE", fontWeight: 500, cursor: "pointer",
  },
  badge: (color, bg) => ({
    display: "inline-block", padding: "2px 8px", borderRadius: 10,
    fontSize: 11, fontWeight: 600, color, background: bg,
  }),
  progressTrack: {
    height: 6, background: "#eee", borderRadius: 3, overflow: "hidden",
    margin: "4px 0",
  },
  progressFill: (pct, color = "#2774AE") => ({
    height: "100%", width: `${Math.round(pct * 100)}%`,
    background: color, borderRadius: 3, transition: "width 0.3s",
  }),
  btnPrimary: {
    background: "#2774AE", color: "#fff", border: "none", borderRadius: 6,
    padding: "7px 16px", fontSize: 13, fontWeight: 600, cursor: "pointer",
  },
  btnExport: {
    background: "#fff", color: "#555", border: "1px solid #ccc", borderRadius: 6,
    padding: "7px 14px", fontSize: 12, cursor: "pointer",
  },
  btnText: {
    background: "none", border: "none", color: "#2774AE", fontSize: 12,
    cursor: "pointer", padding: "4px 0", fontWeight: 500,
  },
  searchInput: {
    border: "1px solid #ccc", borderRadius: 6, padding: "6px 10px",
    fontSize: 13, width: 220, outline: "none",
  },
  selectInput: {
    border: "1px solid #ccc", borderRadius: 6, padding: "6px 10px",
    fontSize: 13, outline: "none", background: "#fff",
  },
  statPill: {
    display: "inline-flex", alignItems: "center", gap: 4,
    fontSize: 11, color: "#666", background: "#f5f5f5",
    borderRadius: 4, padding: "2px 7px",
  },
  miniStat: { fontSize: 11, color: "#888" },
  overrideBox: {
    background: "#FFF3E0", border: "1px solid #FFD54F", borderRadius: 6,
    padding: 12, marginTop: 8,
  },
  btnSaveOverride: {
    background: "#2e7d32", color: "#fff", border: "none", borderRadius: 6,
    padding: "6px 14px", fontSize: 12, fontWeight: 600, cursor: "pointer",
  },
  btnCancel: {
    background: "#fff", color: "#555", border: "1px solid #ccc", borderRadius: 6,
    padding: "6px 14px", fontSize: 12, cursor: "pointer",
  },
  loading: {
    minHeight: "60vh", display: "flex", alignItems: "center",
    justifyContent: "center", color: "#888", fontSize: 14,
  },
};

// ── Helpers ───────────────────────────────────────────────────────────────────

function ScoreCell({ pct }) {
  if (pct === null || pct === undefined) {
    return <span style={{ color: "#bbb" }}>—</span>;
  }
  const color = pct >= 80 ? "#2e7d32" : pct >= 50 ? "#f57f17" : "#c62828";
  return <span style={{ fontWeight: 600, color }}>{pct.toFixed(1)}%</span>;
}

function StatusBadge({ status }) {
  const map = {
    graded: ["#2e7d32", "#e8f5e9"],
    in_progress: ["#E65100", "#FFF3E0"],
    not_started: ["#555", "#f5f5f5"],
  };
  const [color, bg] = map[status] || ["#555", "#f5f5f5"];
  const label = status === "graded" ? "Graded" : status === "in_progress" ? "In Progress" : "Not Started";
  return <span style={S.badge(color, bg)}>{label}</span>;
}

function TypeBadge({ type }) {
  const map = {
    homework: ["#1565C0", "#E3F2FD"],
    quiz: ["#6A1B9A", "#F3E5F5"],
    exam: ["#B71C1C", "#FFEBEE"],
    project: ["#1B5E20", "#E8F5E9"],
  };
  const [color, bg] = map[type] || ["#555", "#f5f5f5"];
  return <span style={S.badge(color, bg)}>{type.charAt(0).toUpperCase() + type.slice(1)}</span>;
}

function ActiveBadge({ isActive }) {
  return isActive
    ? <span style={S.badge("#E65100", "#FFF3E0")}>Active</span>
    : <span style={S.badge("#888", "#f5f5f5")}>Closed</span>;
}

// ── Header ────────────────────────────────────────────────────────────────────

function Header({ offering }) {
  return (
    <div style={S.header}>
      <span style={S.headerLogo}>AutoTA</span>
      <span style={S.headerSep}>|</span>
      <span style={S.headerCourse}>{offering?.course || "ECE M16"}</span>
      <span style={S.headerLabel}>Instructor</span>
      <span style={S.headerRight}>{offering?.instructor || "Prof. Mani Srivastava"}</span>
    </div>
  );
}

// ── Dashboard screen ──────────────────────────────────────────────────────────

function Dashboard({ data, onSelectAssignment }) {
  if (!data) return <div style={S.loading}>Loading dashboard…</div>;

  const { sections, total_enrolled, class_avg_pct, assignments, category_summary } = data;

  const activePsets = assignments.filter(a => a.is_active && a.type === "homework").length;
  const submissionRate = assignments.length > 0
    ? Math.round(assignments.reduce((s, a) => s + a.submission_rate, 0) / assignments.length * 100)
    : 0;

  return (
    <>
      {/* Summary cards */}
      <div style={S.summaryGrid}>
        <div style={S.summaryCard}>
          <div style={S.summaryNum}>{total_enrolled}</div>
          <div style={S.summaryLabel}>
            Students enrolled
            {sections.map(s => (
              <span key={s.label} style={{ marginLeft: 8, fontSize: 11, color: "#aaa" }}>
                §{s.label}: {s.cnt}
              </span>
            ))}
          </div>
        </div>
        <div style={S.summaryCard}>
          <div style={S.summaryNum}>{assignments.length}</div>
          <div style={S.summaryLabel}>{activePsets} active right now</div>
        </div>
        <div style={S.summaryCard}>
          <div style={S.summaryNum}>{class_avg_pct}%</div>
          <div style={S.summaryLabel}>Class average (all graded)</div>
        </div>
        <div style={S.summaryCard}>
          <div style={S.summaryNum}>{submissionRate}%</div>
          <div style={S.summaryLabel}>Avg submission rate</div>
        </div>
      </div>

      {/* Category summary */}
      <div style={S.card}>
        <div style={S.cardTitle}>Summary by Category</div>
        <table style={S.table}>
          <thead>
            <tr>
              <th style={S.th}>Type</th>
              <th style={S.thC}>Count</th>
              <th style={S.thC}>Total Submissions</th>
              <th style={S.thC}>Avg Score</th>
            </tr>
          </thead>
          <tbody>
            {category_summary.map((cat, i) => (
              <tr key={cat.type} style={{ background: i % 2 === 0 ? "#fff" : "#fafafa" }}>
                <td style={S.td}><TypeBadge type={cat.type} /></td>
                <td style={S.tdC}>{cat.count}</td>
                <td style={S.tdC}>{cat.submitted_total}</td>
                <td style={S.tdC}><ScoreCell pct={cat.avg_score} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* All assignments */}
      <div style={S.card}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
          <div style={S.cardTitle}>All Assignments</div>
          <button style={S.btnExport} onClick={() => window.open('/api/instructor/gradebook/export', '_blank')}>Export CSV</button>
        </div>
        <table style={S.table}>
          <thead>
            <tr>
              <th style={S.th}>Assignment</th>
              <th style={S.thC}>Type</th>
              <th style={S.thC}>Status</th>
              <th style={S.thC}>Pts</th>
              <th style={S.thC}>Submitted</th>
              <th style={{ ...S.thC, minWidth: 140 }}>Submission Progress</th>
              <th style={S.thC}>Mean</th>
              <th style={S.thC}>Median</th>
              <th style={S.thC}>σ</th>
              <th style={S.thC}>Min</th>
              <th style={S.thC}>Max</th>
            </tr>
          </thead>
          <tbody>
            {assignments.map((a, i) => (
              <tr key={a.id} style={{ background: i % 2 === 0 ? "#fff" : "#fafafa" }}>
                <td style={S.td}>
                  <button style={S.btnText} onClick={() => onSelectAssignment(a.id)}>
                    {a.title}
                  </button>
                </td>
                <td style={S.tdC}><TypeBadge type={a.type} /></td>
                <td style={S.tdC}><ActiveBadge isActive={a.is_active} /></td>
                <td style={S.tdC}>{a.total_pts}</td>
                <td style={S.tdC}>
                  {a.submitted}/{a.submitted + a.not_submitted}
                </td>
                <td style={{ ...S.tdC, minWidth: 140 }}>
                  <div style={S.progressTrack}>
                    <div style={S.progressFill(a.submission_rate)} />
                  </div>
                  <span style={S.miniStat}>{Math.round(a.submission_rate * 100)}%</span>
                </td>
                <td style={S.tdC}><ScoreCell pct={a.mean ? a.mean * 100 : null} /></td>
                <td style={S.tdC}><ScoreCell pct={a.median ? a.median * 100 : null} /></td>
                <td style={S.tdC}>
                  <span style={S.miniStat}>{a.stdev ? (a.stdev * 100).toFixed(1) : "—"}</span>
                </td>
                <td style={S.tdC}><ScoreCell pct={a.min ? a.min * 100 : null} /></td>
                <td style={S.tdC}><ScoreCell pct={a.max ? a.max * 100 : null} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}

// ── Gradebook screen ──────────────────────────────────────────────────────────

function Gradebook({ onSelectStudent, onSelectAssignment }) {
  const [data, setData] = useState(null);
  const [search, setSearch] = useState("");
  const [sectionFilter, setSectionFilter] = useState("all");
  const [sortCol, setSortCol] = useState("name");
  const [sortDir, setSortDir] = useState(1);

  useEffect(() => {
    getInstructorGradebook().then(setData);
  }, []);

  const students = useMemo(() => {
    if (!data) return [];
    let list = data.students;
    if (search) {
      const q = search.toLowerCase();
      list = list.filter(s => s.name.toLowerCase().includes(q) || s.id.toLowerCase().includes(q));
    }
    if (sectionFilter !== "all") {
      list = list.filter(s => s.section === sectionFilter);
    }
    list = [...list].sort((a, b) => {
      if (sortCol === "name") return sortDir * a.name.localeCompare(b.name);
      if (sortCol === "avg") return sortDir * ((a.overall_avg || -1) - (b.overall_avg || -1));
      const aScore = a.scores[sortCol] ?? -1;
      const bScore = b.scores[sortCol] ?? -1;
      return sortDir * (aScore - bScore);
    });
    return list;
  }, [data, search, sectionFilter, sortCol, sortDir]);

  if (!data) return <div style={S.loading}>Loading gradebook…</div>;

  const toggleSort = (col) => {
    if (sortCol === col) setSortDir(d => -d);
    else { setSortCol(col); setSortDir(1); }
  };

  const sortIcon = (col) => sortCol === col ? (sortDir === 1 ? " ↑" : " ↓") : "";

  return (
    <div style={S.card}>
      <div style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 14, flexWrap: "wrap" }}>
        <div style={{ ...S.cardTitle, margin: 0 }}>Full Gradebook</div>
        <input
          style={S.searchInput}
          placeholder="Search name or UID…"
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
        <select
          style={S.selectInput}
          value={sectionFilter}
          onChange={e => setSectionFilter(e.target.value)}
        >
          <option value="all">All Sections</option>
          <option value="1A">Section 1A</option>
          <option value="1B">Section 1B</option>
        </select>
        <span style={S.miniStat}>{students.length} students</span>
        <button style={{ ...S.btnExport, marginLeft: "auto" }}>Export CSV</button>
      </div>

      <div style={{ overflowX: "auto" }}>
        <table style={{ ...S.table, minWidth: 900 }}>
          <thead>
            <tr>
              <th style={{ ...S.thClick, position: "sticky", left: 0, background: "#fff" }} onClick={() => toggleSort("name")}>
                Student{sortIcon("name")}
              </th>
              <th style={S.thC}>Section</th>
              <th style={{ ...S.thClick }} onClick={() => toggleSort("avg")}>
                Overall{sortIcon("avg")}
              </th>
              {data.assignments.map(a => (
                <th
                  key={a.id}
                  style={{ ...S.thClick, minWidth: 80 }}
                  onClick={() => toggleSort(a.id)}
                >
                  <button
                    style={{ ...S.btnText, fontSize: 10, padding: 0 }}
                    onClick={(e) => { e.stopPropagation(); onSelectAssignment(a.id); }}
                  >
                    {a.id.toUpperCase()}
                  </button>
                  <div style={{ fontSize: 9, color: "#aaa" }}>{a.total_pts}pt</div>
                  {sortIcon(a.id)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {students.map((s, i) => (
              <tr key={s.id} style={{ background: i % 2 === 0 ? "#fff" : "#fafafa" }}>
                <td style={{ ...S.tdName, position: "sticky", left: 0, background: i % 2 === 0 ? "#fff" : "#fafafa" }}
                  onClick={() => onSelectStudent(s.id)}>
                  <div>{s.name}</div>
                  <div style={{ fontSize: 11, color: "#888", fontWeight: 400 }}>{s.id}</div>
                </td>
                <td style={S.tdC}>{s.section}</td>
                <td style={S.tdC}><ScoreCell pct={s.overall_avg} /></td>
                {data.assignments.map(a => (
                  <td key={a.id} style={S.tdC}>
                    <ScoreCell pct={s.scores[a.id]} />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ── Assignment Detail screen ──────────────────────────────────────────────────

function AssignmentDetail({ assignmentId, onSelectStudent, onBack }) {
  const [data, setData] = useState(null);
  const [search, setSearch] = useState("");

  useEffect(() => {
    if (assignmentId) getInstructorAssignment(assignmentId).then(setData);
  }, [assignmentId]);

  if (!data) return <div style={S.loading}>Loading…</div>;

  const { assignment, stats, distribution, problem_stats, students } = data;

  const filteredStudents = students.filter(s => {
    if (!search) return true;
    const q = search.toLowerCase();
    return s.name.toLowerCase().includes(q) || s.id.toLowerCase().includes(q);
  });

  const maxBin = Math.max(...distribution.map(d => d.count), 1);

  return (
    <>
      <button style={{ ...S.btnText, marginBottom: 12, fontSize: 13 }} onClick={onBack}>
        ← Back
      </button>

      <div style={S.card}>
        <div style={{ display: "flex", gap: 12, alignItems: "flex-start", flexWrap: "wrap" }}>
          <div>
            <div style={{ fontSize: 18, fontWeight: 700 }}>{assignment.title}</div>
            <div style={{ fontSize: 12, color: "#888", marginTop: 3 }}>
              <TypeBadge type={assignment.type} />
              {" "}·{" "}<ActiveBadge isActive={assignment.is_active} />
              {" "}· {assignment.total_pts} pts · max {assignment.max_attempts} attempts
            </div>
          </div>
          <button style={{ ...S.btnExport, marginLeft: "auto" }}>Export CSV</button>
        </div>

        {/* Stats row */}
        <div style={{ display: "flex", gap: 16, flexWrap: "wrap", marginTop: 16 }}>
          {[
            ["Submitted", `${stats.submitted} / ${stats.submitted + stats.not_submitted}`],
            ["Sub Rate", `${Math.round(stats.submission_rate * 100)}%`],
            ["Mean", `${(stats.mean * 100).toFixed(1)}%`],
            ["Median", `${(stats.median * 100).toFixed(1)}%`],
            ["Stdev", `${(stats.stdev * 100).toFixed(1)}%`],
            ["Min", `${(stats.min * 100).toFixed(1)}%`],
            ["Max", `${(stats.max * 100).toFixed(1)}%`],
          ].map(([label, val]) => (
            <div key={label} style={S.statPill}>
              <span style={{ color: "#aaa" }}>{label}</span>
              <span style={{ fontWeight: 600, color: "#333" }}>{val}</span>
            </div>
          ))}
        </div>
      </div>

      <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
        {/* Distribution histogram */}
        <div style={{ ...S.card, flex: "0 0 260px" }}>
          <div style={S.cardTitle}>Score Distribution</div>
          {distribution.map((bin, i) => (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 4 }}>
              <span style={{ fontSize: 10, color: "#888", width: 50, textAlign: "right" }}>
                {bin.range}
              </span>
              <div style={{ flex: 1, background: "#eee", borderRadius: 2, height: 14, overflow: "hidden" }}>
                <div style={{
                  height: "100%",
                  width: `${(bin.count / maxBin) * 100}%`,
                  background: i >= 8 ? "#2e7d32" : i >= 5 ? "#2774AE" : "#c62828",
                  borderRadius: 2,
                }} />
              </div>
              <span style={{ fontSize: 11, color: "#555", width: 20 }}>{bin.count}</span>
            </div>
          ))}
        </div>

        {/* Problem breakdown */}
        <div style={{ ...S.card, flex: 1 }}>
          <div style={S.cardTitle}>Problem Breakdown</div>
          <table style={S.table}>
            <thead>
              <tr>
                <th style={S.th}>Problem</th>
                <th style={S.thC}>Points</th>
                <th style={S.thC}>Attempts</th>
                <th style={S.thC}>Correct</th>
                <th style={S.thC}>Correctness %</th>
                <th style={S.thC}>Avg Score</th>
              </tr>
            </thead>
            <tbody>
              {problem_stats.map((p, i) => (
                <tr key={p.id} style={{ background: i % 2 === 0 ? "#fff" : "#fafafa" }}>
                  <td style={S.td}>{p.label}</td>
                  <td style={S.tdC}>{p.points}</td>
                  <td style={S.tdC}>{p.attempts}</td>
                  <td style={S.tdC}>{p.correct_count}</td>
                  <td style={S.tdC}>
                    <ScoreCell pct={p.correctness_pct * 100} />
                  </td>
                  <td style={S.tdC}>
                    <ScoreCell pct={p.avg_score * 100} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Student scores table */}
      <div style={S.card}>
        <div style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 12 }}>
          <div style={{ ...S.cardTitle, margin: 0 }}>Student Grades</div>
          <input
            style={S.searchInput}
            placeholder="Search student…"
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
          <span style={{ ...S.miniStat, marginLeft: "auto" }}>{filteredStudents.length} students</span>
        </div>
        <table style={S.table}>
          <thead>
            <tr>
              <th style={S.th}>Student</th>
              <th style={S.thC}>Section</th>
              <th style={S.thC}>Status</th>
              <th style={S.thC}>Attempt</th>
              <th style={S.thC}>Score</th>
              <th style={S.thC}>Pts Earned</th>
              {problem_stats.map(p => (
                <th key={p.id} style={S.thC}>{p.label}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filteredStudents.map((s, i) => (
              <tr key={s.id} style={{ background: i % 2 === 0 ? "#fff" : "#fafafa" }}>
                <td style={S.tdName} onClick={() => onSelectStudent(s.id)}>
                  <div>{s.name}</div>
                  <div style={{ fontSize: 11, color: "#888", fontWeight: 400 }}>{s.id}</div>
                </td>
                <td style={S.tdC}>{s.section}</td>
                <td style={S.tdC}><StatusBadge status={s.status} /></td>
                <td style={S.tdC}>{s.attempt_number || "—"}</td>
                <td style={S.tdC}><ScoreCell pct={s.total_score} /></td>
                <td style={S.tdC}>
                  {s.points_earned != null
                    ? `${s.points_earned.toFixed(1)} / ${s.points_possible}`
                    : "—"}
                </td>
                {problem_stats.map(p => (
                  <td key={p.id} style={S.tdC}>
                    {s.problem_scores[p.id] != null ? (
                      <ScoreCell pct={s.problem_scores[p.id].score * 100} />
                    ) : "—"}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}

// ── Student DrillDown screen ──────────────────────────────────────────────────

function StudentDrillDown({ studentId, onBack, onSelectAssignment }) {
  const [data, setData] = useState(null);
  const [selectedAsgn, setSelectedAsgn] = useState(null);

  useEffect(() => {
    if (studentId) {
      getInstructorStudent(studentId).then(d => {
        setData(d);
        if (d.assignments?.length > 0) {
          // Default to first graded assignment
          const first = d.assignments.find(a => a.status === "graded") || d.assignments[0];
          setSelectedAsgn(first.id);
        }
      });
    }
  }, [studentId]);

  if (!data) return <div style={S.loading}>Loading…</div>;

  const { student, assignments } = data;
  const currentAsgn = assignments.find(a => a.id === selectedAsgn);

  const gradedAssignments = assignments.filter(a => a.status === "graded");
  const overallPct = student.overall_avg;

  return (
    <>
      <button style={{ ...S.btnText, marginBottom: 12, fontSize: 13 }} onClick={onBack}>
        ← Back
      </button>

      {/* Student header */}
      <div style={S.card}>
        <div style={{ display: "flex", gap: 20, alignItems: "flex-start", flexWrap: "wrap" }}>
          <div>
            <div style={{ fontSize: 20, fontWeight: 700 }}>{student.name}</div>
            <div style={{ fontSize: 12, color: "#888", marginTop: 2 }}>
              {student.id} · {student.email} · Section {student.section}
            </div>
          </div>
          <div style={{ marginLeft: "auto", display: "flex", gap: 16 }}>
            {[
              ["Overall Avg", overallPct != null ? `${overallPct.toFixed(1)}%` : "—"],
              ["Submitted", `${student.submitted_count} / ${student.total_assignments}`],
            ].map(([label, val]) => (
              <div key={label} style={{ textAlign: "center" }}>
                <div style={{ fontSize: 22, fontWeight: 700, color: "#1a1a1a" }}>{val}</div>
                <div style={{ fontSize: 11, color: "#888" }}>{label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Assignment selector */}
      <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 16 }}>
        {assignments.map(a => (
          <button
            key={a.id}
            onClick={() => setSelectedAsgn(a.id)}
            style={{
              padding: "6px 12px", borderRadius: 6, fontSize: 12, fontWeight: 500,
              cursor: "pointer",
              background: selectedAsgn === a.id ? "#2774AE" : "#fff",
              color: selectedAsgn === a.id ? "#fff" : "#555",
              border: selectedAsgn === a.id ? "1px solid #2774AE" : "1px solid #ccc",
            }}
          >
            {a.id.toUpperCase()}
            {a.status === "graded" && (
              <span style={{ marginLeft: 5, fontSize: 11 }}>
                {a.total_score_pct?.toFixed(0)}%
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Selected assignment detail */}
      {currentAsgn && (
        <div style={S.card}>
          <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 16 }}>
            <div>
              <div style={{ fontSize: 15, fontWeight: 600 }}>{currentAsgn.title}</div>
              <div style={{ fontSize: 12, color: "#888", marginTop: 2 }}>
                <TypeBadge type={currentAsgn.type} />
                {" · "}<StatusBadge status={currentAsgn.status} />
                {currentAsgn.attempt_number && ` · Attempt ${currentAsgn.attempt_number}`}
              </div>
            </div>
            {currentAsgn.total_score_pct != null && (
              <div style={{ marginLeft: "auto", textAlign: "center" }}>
                <div style={{ fontSize: 24, fontWeight: 700 }}>
                  <ScoreCell pct={currentAsgn.total_score_pct} />
                </div>
                <div style={{ fontSize: 11, color: "#888" }}>
                  {currentAsgn.points_earned?.toFixed(1)} / {currentAsgn.points_possible} pts
                </div>
              </div>
            )}
          </div>

          {currentAsgn.status === "not_started" && (
            <div style={{ color: "#888", fontStyle: "italic", padding: "12px 0" }}>
              Student has not started this assignment.
            </div>
          )}

          {currentAsgn.problems?.length > 0 && currentAsgn.problems.map((p, i) => (
            <div key={p.id} style={{
              borderRadius: 6,
              border: "1px solid #eee",
              padding: "12px 14px",
              marginBottom: 10,
              background: p.correct ? "#f9fdf9" : "#fff9f9",
            }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
                <span style={{ fontWeight: 600, fontSize: 13 }}>{p.label}</span>
                <span style={{ fontSize: 12, color: "#888" }}>{p.points} pt{p.points !== 1 ? "s" : ""}</span>
                <span style={S.badge(p.correct ? "#2e7d32" : "#c62828", p.correct ? "#e8f5e9" : "#ffebee")}>
                  {p.correct ? "✓ Correct" : "✗ Incorrect"}
                </span>
                <span style={{ marginLeft: "auto" }}>
                  <ScoreCell pct={p.score != null ? p.score * 100 : null} />
                </span>
              </div>
              <div style={{ fontSize: 12, color: "#333" }}>
                <span style={{ color: "#888" }}>Answer: </span>
                <code style={{ fontFamily: "'IBM Plex Mono', monospace", background: "#f5f5f5", padding: "1px 6px", borderRadius: 3 }}>
                  {p.answer || "—"}
                </code>
              </div>
              {p.feedback && (
                <div style={{ fontSize: 11, color: "#666", marginTop: 4 }}>
                  {p.feedback}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Assignment summary table */}
      <div style={S.card}>
        <div style={S.cardTitle}>All Assignments Summary</div>
        <table style={S.table}>
          <thead>
            <tr>
              <th style={S.th}>Assignment</th>
              <th style={S.thC}>Type</th>
              <th style={S.thC}>Status</th>
              <th style={S.thC}>Score</th>
              <th style={S.thC}>Points</th>
              <th style={S.thC}>Correct</th>
              <th style={S.thC}>Submitted</th>
            </tr>
          </thead>
          <tbody>
            {assignments.map((a, i) => (
              <tr key={a.id} style={{ background: i % 2 === 0 ? "#fff" : "#fafafa" }}>
                <td style={S.td}>
                  <button style={S.btnText} onClick={() => onSelectAssignment(a.id)}>
                    {a.title}
                  </button>
                </td>
                <td style={S.tdC}><TypeBadge type={a.type} /></td>
                <td style={S.tdC}><StatusBadge status={a.status} /></td>
                <td style={S.tdC}><ScoreCell pct={a.total_score_pct} /></td>
                <td style={S.tdC}>
                  {a.points_earned != null
                    ? `${a.points_earned.toFixed(1)} / ${a.points_possible}`
                    : "—"}
                </td>
                <td style={S.tdC}>
                  {a.problems_correct != null
                    ? `${a.problems_correct} / ${a.problems_total}`
                    : "—"}
                </td>
                <td style={S.tdC}>
                  {a.submitted_at ? new Date(a.submitted_at).toLocaleDateString() : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}

// ── Roster screen ─────────────────────────────────────────────────────────────

function Roster({ onSelectStudent }) {
  const [data, setData] = useState(null);
  const [search, setSearch] = useState("");
  const [sectionFilter, setSectionFilter] = useState("all");

  useEffect(() => {
    getInstructorRoster().then(setData);
  }, []);

  if (!data) return <div style={S.loading}>Loading roster…</div>;

  const students = data.students.filter(s => {
    if (sectionFilter !== "all" && s.section !== sectionFilter) return false;
    if (!search) return true;
    const q = search.toLowerCase();
    return s.name.toLowerCase().includes(q) || s.id.toLowerCase().includes(q) || s.email.toLowerCase().includes(q);
  });

  return (
    <div style={S.card}>
      <div style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 14, flexWrap: "wrap" }}>
        <div style={{ fontSize: 13, fontWeight: 600, color: "#333", textTransform: "uppercase", letterSpacing: "0.05em" }}>
          Student Roster
        </div>
        <input
          style={S.searchInput}
          placeholder="Search name, UID, or email…"
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
        <select
          style={S.selectInput}
          value={sectionFilter}
          onChange={e => setSectionFilter(e.target.value)}
        >
          <option value="all">All Sections</option>
          <option value="1A">Section 1A</option>
          <option value="1B">Section 1B</option>
        </select>
        <span style={S.miniStat}>{students.length} / {data.total_enrolled} students</span>
        <button style={{ ...S.btnExport, marginLeft: "auto" }}>Export CSV</button>
      </div>
      <table style={S.table}>
        <thead>
          <tr>
            <th style={S.th}>Student</th>
            <th style={S.th}>Email</th>
            <th style={S.thC}>Section</th>
            <th style={S.thC}>Submitted</th>
          </tr>
        </thead>
        <tbody>
          {students.map((s, i) => (
            <tr key={s.id} style={{ background: i % 2 === 0 ? "#fff" : "#fafafa" }}>
              <td style={S.tdName} onClick={() => onSelectStudent(s.id)}>
                <div>{s.name}</div>
                <div style={{ fontSize: 11, color: "#888", fontWeight: 400 }}>{s.id}</div>
              </td>
              <td style={S.td}>{s.email}</td>
              <td style={S.tdC}>{s.section}</td>
              <td style={S.tdC}>{s.submitted_count} / {s.total_assignments}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ── Main InstructorDashboard component ────────────────────────────────────────

export default function InstructorDashboard() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [dashData, setDashData] = useState(null);
  const [selectedAssignment, setSelectedAssignment] = useState(null);
  const [selectedStudent, setSelectedStudent] = useState(null);
  const [studentFrom, setStudentFrom] = useState(null);  // which tab we came from

  useEffect(() => {
    getInstructorDashboard().then(setDashData);
  }, []);

  const offering = dashData?.offering;

  const tabs = [
    { id: "dashboard", label: "Dashboard" },
    { id: "gradebook", label: "Gradebook" },
    { id: "roster", label: "Roster" },
  ];

  function handleSelectAssignment(id) {
    setSelectedAssignment(id);
    setActiveTab("assignment");
  }

  function handleSelectStudent(id, fromTab) {
    setSelectedStudent(id);
    setStudentFrom(fromTab || activeTab);
    setActiveTab("student");
  }

  function handleBackFromAssignment() {
    setSelectedAssignment(null);
    setActiveTab("dashboard");
  }

  function handleBackFromStudent() {
    setSelectedStudent(null);
    setActiveTab(studentFrom || "gradebook");
  }

  return (
    <div style={S.page}>
      <Header offering={offering} />

      <div style={S.content}>
        {/* Tab navigation — hidden on sub-screens */}
        {activeTab !== "assignment" && activeTab !== "student" && (
          <div style={S.nav}>
            {tabs.map(t => (
              <button
                key={t.id}
                style={activeTab === t.id ? S.navTabActive : S.navTab}
                onClick={() => setActiveTab(t.id)}
              >
                {t.label}
              </button>
            ))}
          </div>
        )}

        {/* Screen rendering */}
        {activeTab === "dashboard" && (
          <Dashboard data={dashData} onSelectAssignment={handleSelectAssignment} />
        )}
        {activeTab === "gradebook" && (
          <Gradebook
            onSelectStudent={(id) => handleSelectStudent(id, "gradebook")}
            onSelectAssignment={handleSelectAssignment}
          />
        )}
        {activeTab === "roster" && (
          <Roster onSelectStudent={(id) => handleSelectStudent(id, "roster")} />
        )}
        {activeTab === "assignment" && selectedAssignment && (
          <AssignmentDetail
            assignmentId={selectedAssignment}
            onSelectStudent={(id) => handleSelectStudent(id, "assignment")}
            onBack={handleBackFromAssignment}
          />
        )}
        {activeTab === "student" && selectedStudent && (
          <StudentDrillDown
            studentId={selectedStudent}
            onBack={handleBackFromStudent}
            onSelectAssignment={handleSelectAssignment}
          />
        )}
      </div>
    </div>
  );
}
