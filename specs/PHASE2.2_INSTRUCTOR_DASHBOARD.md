# AutoTA Phase 2.2 — Instructor Dashboard

## Context

The student-facing web UI (Phase 2) and production schema (Phase 2.1) are complete. Students can take assessments, get instant grading, and retry with fresh variants. The `v_grade_report` and `v_student_attempt_status` views already exist in the database.

Now we need the instructor side: a dashboard where Mani (and TAs) can monitor assignments, review grades, export to BruinLearn, and manage the assessment pipeline.

Read these files first:
1. `PHASE2_COMPLETE.md` — what exists (student UI)
2. `PHASE2.1_SCHEMA_MIGRATION.md` — current schema (19 tables, 2 views)
3. `docs/instructor-prototype.jsx` — **interactive prototype of the instructor dashboard — MATCH THIS EXACTLY**
4. `docs/ui-prototype.jsx` — student UI design reference (for style consistency)
5. `autota/web/routes/` — existing backend routes

---

## Who Uses This

**Primary user: Prof. Mani Srivastava** — checks how the class is doing, exports grades to BruinLearn, configures assignments. Wants to see the big picture fast.

**Secondary: TAs** — look up individual students, review edge cases, answer student questions about grading. Need to drill into specific submissions.

**Access model (Phase 2.2):** URL-based role, same as student side for now. `http://localhost:5173/instructor`. Real auth deferred to Phase 3+.

---

## Design Principles

1. **Dashboard-first.** The landing page is an at-a-glance overview, not a nav menu. Mani opens it and immediately sees: which assignments are active, how many students have submitted, what the score distribution looks like.

2. **Two clicks to any data.** Dashboard → assignment → student drill-down. Never more than two clicks from the top level to a specific student's specific answer on a specific problem.

3. **Export is a first-class action.** The CSV export button should be prominent, not buried in a settings menu. Mani exports grades weekly.

4. **Same design language as student UI.** UCLA blue (#2774AE), IBM Plex Sans + IBM Plex Mono fonts, same card/shadow pattern. But the header bar is dark charcoal (`#1a1a1a`) so it's immediately obvious this is not the student view.

5. **Read-heavy, write-light.** Phase 2.2 is primarily about viewing data. The only write operations are: activate/deactivate an assignment, and override a grade. Assignment creation is done via CLI + seed scripts for now (Phase 3+).

---

## Screens (5 total)

### 1. Dashboard (Landing)

**URL:** `/instructor`

**Header bar** (dark `#1a1a1a`, NOT UCLA blue — distinguishes from student view): "AutoTA · ECE M16 · Instructor Dashboard". Instructor name on right. Sticky at top.

**Top summary cards** — four white cards in a row:
- **Enrolled**: total count (large number) + per-section breakdown (e.g. "1A: 98 · 1B: 102")
- **Assignments**: total count + how many active
- **Class Average**: mean score across all graded assignments (percentage)
- **Submission Rate**: overall percentage across all assignments

**Summary by Category table** — white card with table. One row per assignment type. Types are auto-detected from `assignments.type` in the DB. For M16 expect: PSET, Quiz, Midterm, Design Assignment, Final Exam. Columns:
- Category (type badge, color-coded)
- Count
- Total Points
- Avg Class Mean (ScoreCell)
- Status (e.g. "2 active" or "All closed")
- "View Full Roster →" link in the table header row

**All Assignments list** — one card per assignment, ordered by closes_at. Each card shows:
- Title + type badge (color-coded) + active/closed badge
- Metadata: total points, max attempts, due date
- Progress bar (UCLA blue on gray track)
- Stat pills: "X/Y submitted" (blue), "N in progress" (yellow if > 0), "N not started" (gray if > 0)
- Score stats on right side: μ, median, σ in monospace
- Two buttons: "Export" and "Details →"

**"View Full Gradebook →" button** — prominent, above the assignments list, navigates to Full Gradebook screen.

### 2. Full Gradebook

**URL:** `/instructor/gradebook`

The cross-assignment view. Every student × every assignment in one table.

**Controls row:**
- Search input (name or UID)
- Section dropdown (All Sections, 1A, 1B)
- **Assignment type dropdown** — auto-populated from unique `assignments.type` values in DB. Shows "All Types (8)", "PSET (4)", "Quiz (2)", "Midterm (1)", "Design Assignment (1)", etc. Selecting a type filters the visible columns.
- Export CSV + Export BruinLearn buttons on right

**Table:**
- **Rows**: one per student. Name + UID in first column (sticky left)
- **Columns**: one per assignment (filtered by type dropdown). Header shows assignment ID in caps (e.g. "HW5") + point total in parens. Below each column header: its type badge
- **Cells**: color-coded ScoreCell (green >= 80%, yellow 50-79%, red < 50%). Show hourglass for in-progress. Dash for not started
- **Overall column** (right side, separated by left border): average across visible assignments
- **Sortable**: click any column header to sort asc/desc (arrow indicators)
- **Zebra striping**: alternating white / #fafafa rows
- Click any row → Student Drill-Down

**Footer**: "{N} students · {M} assignments shown"

### 3. Assignment Detail

**URL:** `/instructor/assignment/{assignment_id}`

Reached by clicking "Details →" on a dashboard assignment card.

**Back button**: "← Dashboard" (top left, blue text link)

**Header card**: type badge + active/closed badge + metadata (points, attempts, due date). Export BruinLearn + Export Full buttons on right.

**Two-panel layout** (side by side):

Left panel — **Score distribution chart**: vertical bar histogram, 10 bins (0%, 10%, 20%, ..., 90%). Bar height proportional to count. Color-coded: red (0-30%), yellow (30-50%), light blue (50-80%), UCLA blue (80-100%). Count shown above each bar. Stats line below title: "μ = X% · med = Y% · σ = Z%".

Right panel — **Problem breakdown table** (only shown for assignments with problem data): Problem label (blue), Points, % Correct (ScoreCell), Avg Score (ScoreCell), Top Error (monospace, with count).

**Student grade table** (below panels):
- Controls: search input + section dropdown
- Columns: Student (name + UID), Section, Attempts, per-problem score columns (if problems exist), Total (bold %), Status badge
- Sortable by all columns
- Click row → Student Drill-Down

### 4. Student Drill-Down

**URL:** `/instructor/student/{student_id}`

Reached by clicking a student row from Gradebook, Assignment Detail, or Roster.

**Back button**: "← Gradebook" or "← Assignment" (context-dependent)

**Student header card**: name (h2) + UID + email + section on left. Overall average (large number) + "N graded" on right.

**Assignment selector pills** — horizontal row of buttons, one per assignment. Each shows assignment ID in caps + student's score (or hourglass or dash). Active pill: dark background (`#1a1a1a`) + white text. Inactive: white background + border. Click to switch between assignments without navigating away.

**Selected assignment detail card**:
- Title, type badge, status badge, "Attempt N of M"
- Total score (large, right-aligned) + points earned/possible

**Per-problem breakdown** (for assignments with graded problem data):
- Each problem separated by `1px solid #f0f0f0` dividers (not separate cards)
- Problem label (blue, bold) + points + "Overridden" badge (orange bg) if applicable
- Variant info line: minterms + don't-cares in monospace (if applicable)
- **Answer comparison block** (gray `#f8f8f8` background, rounded): two columns — "Student" label + answer (red if wrong, green if right) vs "Correct" label + answer (always green). Both in IBM Plex Mono.
- Feedback text + grading tier badge (gray pill) + override button (pencil icon)

**Grade override** (inline expansion, NOT a modal):
1. Click pencil → yellow panel (`#FFF8E1` bg, `#FFE082` border) expands below the problem
2. "Grade Override" title in orange
3. Score (%) number input + Feedback textarea (pre-filled with current values)
4. "Save" (green `#2e7d32`) + "Cancel" (white/gray) buttons
5. On save: POST to override endpoint, show "Overridden" badge on that problem

For assignments without detailed problem data: show score summary line.
For not-started / in-progress students: show italic status message.

### 5. Student Roster

**URL:** `/instructor/students`

The TA office-hours view.

**Back button**: "← Dashboard"

**Search bar** (name, UID, email)

**Table:**
- Columns: Name, UID (monospace), Email, Section, one column per assignment (score or hourglass or dash), Overall average (separated by border)
- Zebra-striped, clickable rows
- Click row → Student Drill-Down

---

## Assignment Type Badges (Color Mapping)

Types are auto-detected from `assignments.type` in the DB. Color map:

| Type | Background | Text Color |
|------|-----------|------------|
| PSET | `#E3F2FD` | `#1565C0` |
| Quiz | `#F3E5F5` | `#7B1FA2` |
| Midterm | `#FFF3E0` | `#E65100` |
| Design Assignment | `#E8F5E9` | `#2E7D32` |
| Final Exam | `#FCE4EC` | `#C62828` |

Default (unknown type): `#f5f5f5` bg, `#666` text.

---

## API Endpoints (New)

All instructor endpoints live under `/api/instructor/`. Phase 2.2 does not enforce auth. Real auth is Phase 3+.

### `GET /api/instructor/dashboard`

Returns all assignments for the offering with summary stats, category summary, and enrollment data.

**Response:**
```json
{
  "offering": {
    "id": "ECE_M16_SP26",
    "course": "ECE M16",
    "course_name": "Logic Design of Digital Systems",
    "quarter": "Spring 2026",
    "instructor": "Prof. Mani Srivastava"
  },
  "total_enrolled": 200,
  "sections": [
    { "label": "1A", "count": 98 },
    { "label": "1B", "count": 102 }
  ],
  "class_average": 0.78,
  "submission_rate": 0.85,
  "category_summary": [
    { "type": "PSET", "count": 4, "total_pts": 38, "avg_mean": 0.76, "active_count": 2 },
    { "type": "Quiz", "count": 2, "total_pts": 40, "avg_mean": 0.82, "active_count": 0 }
  ],
  "assignments": [
    {
      "id": "hw5",
      "title": "PSET 5 — Karnaugh Map Simplification",
      "type": "PSET",
      "is_active": true,
      "max_attempts": 3,
      "total_pts": 10,
      "closes_at": "2026-03-15T23:59:00Z",
      "not_started": 45,
      "in_progress": 12,
      "submitted": 143,
      "score_stats": {
        "mean": 0.78,
        "median": 0.82,
        "stdev": 0.15
      }
    }
  ]
}
```

### `GET /api/instructor/gradebook`

Returns all students with scores across all assignments, for the Full Gradebook table.

**Query params:**
- `type` — filter by assignment type (optional, default: all)
- `section` — filter by section label (optional)
- `search` — filter by name or UID (optional)

**Response:**
```json
{
  "assignments": [
    { "id": "hw3", "title": "PSET 3...", "type": "PSET", "total_pts": 8 },
    { "id": "hw5", "title": "PSET 5...", "type": "PSET", "total_pts": 10 }
  ],
  "assignment_types": ["PSET", "Quiz", "Midterm", "Design Assignment"],
  "students": [
    {
      "student_id": "UID123456789",
      "name": "Pragya Sharma",
      "section": "1A",
      "scores": {
        "hw3": { "total_score": 0.9, "status": "graded", "attempts": 1 },
        "hw5": { "total_score": 0.875, "status": "graded", "attempts": 2 }
      }
    }
  ]
}
```

### `GET /api/instructor/assignment/{assignment_id}`

Returns full grade data for an assignment, including distribution, problem stats, and student grades.

**Response:**
```json
{
  "assignment": { "id": "hw5", "title": "...", "type": "PSET", "max_attempts": 3, "is_active": true, "total_pts": 10, "closes_at": "..." },
  "problems": [
    { "id": "hw5_1a", "label": "Q1a", "points": 2.0, "pct_correct": 0.72, "avg_score": 0.81 }
  ],
  "score_distribution": [
    { "bin": 0, "count": 2 }, { "bin": 10, "count": 5 }, { "bin": 90, "count": 48 }
  ],
  "common_errors": {
    "hw5_1a": [
      { "answer": "AB + CD", "count": 12 },
      { "answer": "A'B", "count": 7 }
    ]
  },
  "students": [
    {
      "student_id": "UID123456789",
      "name": "Pragya Sharma",
      "section": "1A",
      "attempts": 2,
      "status": "graded",
      "total_score": 0.875,
      "total_points_earned": 8.5,
      "problem_scores": {
        "hw5_1a": { "score": 1.0, "correct": true },
        "hw5_1b": { "score": 1.0, "correct": true }
      }
    }
  ]
}
```

### `GET /api/instructor/student/{student_id}`

Returns student info + scores across ALL assignments + detailed per-problem data for each assignment.

**Response:**
```json
{
  "student": { "id": "UID123456789", "name": "Pragya Sharma", "email": "pragya@ucla.edu", "section": "1A" },
  "overall_average": 0.83,
  "assignments": [
    {
      "assignment_id": "hw5",
      "title": "PSET 5...",
      "type": "PSET",
      "max_attempts": 3,
      "total_pts": 10,
      "status": "graded",
      "attempts": 2,
      "total_score": 0.875,
      "total_earned": 8.5,
      "problems": [
        {
          "problem_id": "hw5_1a",
          "label": "Q1a",
          "points": 2.0,
          "minterms": "m(0,1,3,5,7,10,11,12,14)",
          "dont_cares": "d(2,4)",
          "answer_raw": "AB + C'D",
          "correct_answer": "A'D + BC + AB'C'",
          "score": 0.5,
          "correct": false,
          "feedback": "Partially correct. 8/16 rows match.",
          "grading_tier": "deterministic"
        }
      ]
    }
  ]
}
```

### `POST /api/instructor/override-grade`

Instructor manually overrides a grade.

**Request:**
```json
{
  "submission_id": 123,
  "new_score": 0.85,
  "new_feedback": "Accepted — equivalent expression using different grouping.",
  "instructor_id": "msrivastava"
}
```

**Response:**
```json
{
  "updated": true,
  "previous_score": 0.5,
  "new_score": 0.85,
  "attempt_result_recalculated": true,
  "new_total_score": 0.92
}
```

**Logic:**
1. Update `grades` row: set `score`, `feedback`, `grading_tier = 'human'`, `graded_by`, `graded_at = now()`
2. Store old values in `previous_score`, `previous_feedback`, `regraded_at`
3. Recalculate `attempt_results` for the affected attempt (weighted aggregate)

### `POST /api/instructor/toggle-assignment`

Activate or deactivate an assignment.

**Request:**
```json
{ "assignment_id": "hw5", "is_active": false }
```

### `GET /api/instructor/export/{assignment_id}`

Returns CSV file as download. Two formats via query param `format`:

**`?format=bruinlearn`** — BruinLearn/Canvas compatible:
```csv
Student,ID,Section,PSET 5 (10)
"Sharma, Pragya",123456789,1A,8.5
"Bruin, Jane",987654321,1A,7.0
```
- UID: 9 digits with leading zeros (CRITICAL for BruinLearn import)
- Name: "Last, First" format
- Score column header includes point total in parentheses
- Score is raw points earned (not percentage)
- Uses best attempt per student

**`?format=full`** — detailed export:
```csv
Student Name,UID,Email,Section,Attempt,Q1a (2),Q1b (1),Q2 (2),Q3a (2),Q3b (1),Q3c (2),Total Points,Total Pct,Status,Submitted At
Pragya Sharma,UID123456789,pragya@ucla.edu,1A,2,2.0,1.0,1.5,2.0,0.0,2.0,8.5,85.0%,graded,2026-03-01T12:00:00Z
```

### `GET /api/instructor/students`

Returns the full student roster with per-assignment summary scores.

---

## Frontend Structure (New Files)

```
frontend/src/
├── instructor/
│   ├── InstructorApp.jsx       # Instructor layout + screen routing
│   ├── screens/
│   │   ├── Dashboard.jsx       # Summary cards + category table + assignment list
│   │   ├── FullGradebook.jsx   # Cross-assignment table with type filtering
│   │   ├── AssignmentDetail.jsx # Distribution chart + problem breakdown + grade table
│   │   ├── StudentDrillDown.jsx # Assignment pills + per-problem detail + grade override
│   │   └── StudentRoster.jsx   # Searchable student list with per-assignment scores
│   ├── components/
│   │   ├── ScoreCell.jsx       # Color-coded score display (green/yellow/red)
│   │   ├── StatusBadge.jsx     # Graded/In Progress/Not Started badges
│   │   ├── TypeBadge.jsx       # Color-coded assignment type badges
│   │   ├── ActiveBadge.jsx     # Active/Closed badge
│   │   ├── ScoreChart.jsx      # Histogram bar chart
│   │   ├── OverridePanel.jsx   # Inline grade override (yellow panel)
│   │   └── Header.jsx          # Dark charcoal header bar
│   └── instructorApi.js        # API wrappers for all instructor endpoints
```

**Routing:** The main `App.jsx` checks the URL path. If it starts with `/instructor`, render `InstructorApp`. Otherwise render the student flow as before. The student UI is unchanged.

---

## Database Changes

### New view: `v_assignment_summary`

```sql
CREATE VIEW IF NOT EXISTS v_assignment_summary AS
SELECT
    asn.id AS assignment_id,
    asn.title,
    asn.type,
    asn.is_active,
    asn.max_attempts,
    asn.closes_at,
    asn.offering_id,
    COUNT(DISTINCT e.student_id) AS total_students,
    COUNT(DISTINCT CASE WHEN a.status IS NULL THEN e.student_id END) AS not_started,
    COUNT(DISTINCT CASE WHEN a.status = 'in_progress' THEN e.student_id END) AS in_progress,
    COUNT(DISTINCT CASE WHEN a.status IN ('submitted', 'graded') THEN e.student_id END) AS submitted
FROM assignments asn
JOIN course_offerings co ON asn.offering_id = co.id
JOIN sections sec ON sec.offering_id = co.id
JOIN enrollments e ON e.section_id = sec.id AND e.dropped = 0
LEFT JOIN attempts a ON a.student_id = e.student_id AND a.assignment_id = asn.id
GROUP BY asn.id;
```

### New view: `v_best_attempt`

```sql
CREATE VIEW IF NOT EXISTS v_best_attempt AS
SELECT
    a.student_id,
    a.assignment_id,
    a.id AS attempt_id,
    a.attempt_number,
    a.status,
    a.submitted_at,
    ar.total_score,
    ar.total_points_earned,
    ar.total_points_possible,
    ar.problems_correct,
    ar.problems_total
FROM attempts a
JOIN attempt_results ar ON a.id = ar.attempt_id
WHERE a.id = (
    SELECT a2.id FROM attempts a2
    JOIN attempt_results ar2 ON a2.id = ar2.attempt_id
    WHERE a2.student_id = a.student_id
      AND a2.assignment_id = a.assignment_id
    ORDER BY ar2.total_score DESC, a2.attempt_number DESC
    LIMIT 1
);
```

### Migration: `migrations/003_instructor_views.sql`

Contains the two views above. No table changes needed — the Phase 2.1 schema already has everything the dashboard queries require.

### Seeding: Update `seed.py`

Add more assignments to the seed script so the dashboard has realistic data:

```python
SEED_ASSIGNMENTS = [
    {"id": "hw3", "title": "PSET 3 — Boolean Algebra", "type": "PSET", "max_attempts": 3, "total_pts": 8, "is_active": False, "closes_at": "2026-02-01T23:59:00Z"},
    {"id": "hw4", "title": "PSET 4 — Combinational Logic", "type": "PSET", "max_attempts": 3, "total_pts": 10, "is_active": False, "closes_at": "2026-02-15T23:59:00Z"},
    {"id": "hw5", "title": "PSET 5 — Karnaugh Map Simplification", "type": "PSET", "max_attempts": 3, "total_pts": 10, "is_active": True, "closes_at": "2026-03-15T23:59:00Z"},
    {"id": "hw6", "title": "PSET 6 — Multi-Level Optimization", "type": "PSET", "max_attempts": 3, "total_pts": 10, "is_active": True, "closes_at": "2026-03-29T23:59:00Z"},
    {"id": "quiz1", "title": "Quiz 1 — Gates & Truth Tables", "type": "Quiz", "max_attempts": 1, "total_pts": 20, "is_active": False, "closes_at": "2026-01-31T23:59:00Z"},
    {"id": "quiz2", "title": "Quiz 2 — K-Map Speed Round", "type": "Quiz", "max_attempts": 1, "total_pts": 20, "is_active": False, "closes_at": "2026-02-28T23:59:00Z"},
    {"id": "midterm", "title": "Midterm Exam", "type": "Midterm", "max_attempts": 1, "total_pts": 100, "is_active": False, "closes_at": "2026-02-14T23:59:00Z"},
    {"id": "da1", "title": "Design Assignment 1 — ALU Design", "type": "Design Assignment", "max_attempts": 2, "total_pts": 50, "is_active": True, "closes_at": "2026-03-22T23:59:00Z"},
]
```

For assignments other than hw5 (which has real problem data and verifiers), seed with randomized scores directly in `attempt_results`. These don't need per-problem granularity — the dashboard just shows the total score. Only hw5 (and hw6 if you wire up problems) need full problem-level data.

Also seed ~30 students instead of 3, with randomized enrollment across sections, so the dashboard looks realistic.

---

## CSV Export Details

### BruinLearn Format

BruinLearn (Canvas) imports grades via CSV. Critical formatting requirements:

- **UID column**: 9-digit number with leading zeros preserved. Column header: "ID". Format as text to prevent Excel stripping zeros.
- **Name column**: "Last, First" format. Column header: "Student".
- **Section column**: Header: "Section".
- **Score column**: Header: `{Assignment Title} ({total_points})`. Value: raw points earned (not percentage).
- **File encoding**: UTF-8, comma-delimited, `.csv` extension.

Set `Content-Disposition: attachment; filename="ECE_M16_SP26_hw5_grades.csv"` and `Content-Type: text/csv`.

### Full Export Format

For instructor analysis. All attempts, all problem scores, answers, timestamps. One row per student per attempt.

---

## What NOT to Build

- Assignment creation/editing UI (use CLI + seed scripts)
- Student enrollment management (manual DB or CSV import)
- Real authentication (URL param for now)
- Variant pool management UI
- Quiz session creation/QR code generation
- Email notifications
- Analytics over time (cross-assignment trends)
- LMS integration beyond CSV export

---

## Testing

1. Run migration: `sqlite3 data/autota.db < migrations/003_instructor_views.sql`
2. Re-run seed: `./seed.sh` (adds new assignments + more students)
3. Visit `http://localhost:5173/instructor`
4. **Dashboard**: verify summary cards, category table, all 8 assignment cards with stats
5. **Full Gradebook**: click "View Full Gradebook" → verify cross-assignment table. Filter by type (PSET, Quiz, etc.) → verify columns filter correctly
6. **Assignment Detail**: click "Details →" on hw5 → verify distribution chart, problem breakdown, grade table
7. **Student Drill-Down**: click a student → verify assignment pills, per-problem detail. Switch between assignments using pills
8. **Grade Override**: click pencil on a problem → enter new score → save → verify "Overridden" badge + recalculated total
9. **Student Roster**: click "View Full Roster →" → search by name → click student
10. **CSV Export**: export BruinLearn CSV → open in Excel → verify UID leading zeros preserved
11. **Student UI unchanged**: `http://localhost:5173/?sid=UID123456789` still works
12. Run `pytest` — all Phase 1 tests pass

---

## Build Order

1. Create `migrations/003_instructor_views.sql` and run it
2. Update `seed.py` — add 8 assignments, ~30 students, randomized scores
3. Implement `routes/instructor.py` — all API endpoints
4. Add instructor routing to `app.py` (mount under `/api/instructor/`)
5. Build shared components: ScoreCell, StatusBadge, TypeBadge, ActiveBadge, Header
6. Build Dashboard screen (summary cards + category table + assignment cards)
7. Build FullGradebook screen (cross-assignment table + type dropdown filter)
8. Build AssignmentDetail screen (chart + problem breakdown + grade table)
9. Build StudentDrillDown screen (assignment pills + per-problem detail + grade override)
10. Build StudentRoster screen (searchable roster)
11. Implement CSV export endpoint (both BruinLearn and full formats)
12. Implement grade override endpoint + inline UI
13. Add instructor routing to frontend App.jsx (path-based: /instructor → InstructorApp)
14. Test full flow end-to-end
15. Run `pytest`
