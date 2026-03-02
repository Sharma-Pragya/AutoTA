# AutoTA Phase 2.1 — Schema Hardening & Variant Pool

## Context

Phase 2 is complete and working. The web UI, 5 API endpoints, 6 DB tables, grading integration, and auto-save are all functional. **Do not break any of this.**

Phase 2.1 extends the backend data model to be production-grade. The frontend changes are minimal — mostly just displaying new fields that the API now returns (attempt limits, point weights, retry option).

Read these files first:
1. `PHASE2_COMPLETE.md` — what exists now
2. `ARCHITECTURE.md` — the system design
3. `migrations/001_initial_schema.sql` — the target schema (full reference)
4. The existing `autota/web/db.py` and `autota/web/routes/` — the code you're extending

---

## What Exists Now (Phase 2 — 6 tables)

```
students           — id, name, email, section
assignments        — id, title, course, spec_path, instructions, is_active, created_at
problems           — id, assignment_id, parent_label, sub_label, display_order, text,
                     minterms, dont_cares, hint, answer_format, placeholder
variant_assignments — id, student_id, problem_id, variant_id, variant_json,
                      solution_json, attempt_number, assigned_at
submissions        — id, student_id, problem_id, variant_assignment_id, answer,
                     score, correct, feedback, graded_at, submitted_at, attestation_signed
attempts           — id, student_id, assignment_id, attempt_number, started_at,
                     submitted_at, total_score
```

This works but has limitations:
- No institutional hierarchy (courses, sections, instructors are just strings)
- Variants are stored inline in variant_assignments (no reusable pool)
- No separation between drafts and final submissions
- Grading metadata (tier, status, regrader) not tracked
- No weighted scoring (all problems treated equally)
- No retry logic with variant exclusion
- Attempt state machine not enforced

---

## What Phase 2.1 Adds

### New Tables (CREATE)

```sql
-- Institutional hierarchy
courses
course_offerings
instructors
sections
enrollments

-- Variant pool (decoupled from assignments)
variant_pool

-- Separated draft layer
draft_answers

-- Proper grading layer
grades
attempt_results

-- Quiz stub (Phase 5, table created now)
quiz_sessions
```

### Modified Tables (ALTER)

```sql
-- assignments: add offering_id, type, max_attempts, time_limit_minutes, opens_at, closes_at
-- problems: add problem_type, points, depends_on_problem_id
-- attempts: add status, attestation_signed, attestation_signed_at
-- variant_assignments: restructure to reference variant_pool.id + attempt_id instead of storing JSON inline
```

### Views (CREATE)
```sql
v_student_attempt_status  — quick lookup: can this student retry?
v_grade_report            — full grade report for instructor export
```

---

## Migration Strategy

**Do NOT drop and recreate.** The existing DB has seeded data that should survive.

### Step 1: Run the migration SQL

Create `migrations/002_schema_hardening.sql` with:

```sql
-- ============================================================
-- Phase 2.1: Schema Hardening Migration
-- Run: sqlite3 data/autota.db < migrations/002_schema_hardening.sql
-- ============================================================

-- 1. NEW TABLES: Institutional layer

CREATE TABLE IF NOT EXISTS courses (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    department TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS course_offerings (
    id TEXT PRIMARY KEY,
    course_id TEXT NOT NULL REFERENCES courses(id),
    quarter TEXT NOT NULL,
    year INTEGER NOT NULL,
    UNIQUE(course_id, quarter, year)
);

CREATE TABLE IF NOT EXISTS instructors (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    role TEXT NOT NULL DEFAULT 'instructor'
);

CREATE TABLE IF NOT EXISTS sections (
    id TEXT PRIMARY KEY,
    offering_id TEXT NOT NULL REFERENCES course_offerings(id),
    label TEXT NOT NULL,
    instructor_id TEXT REFERENCES instructors(id),
    UNIQUE(offering_id, label)
);

CREATE TABLE IF NOT EXISTS enrollments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL REFERENCES students(id),
    section_id TEXT NOT NULL REFERENCES sections(id),
    enrolled_at TEXT DEFAULT (datetime('now')),
    dropped INTEGER DEFAULT 0,
    UNIQUE(student_id, section_id)
);

CREATE INDEX IF NOT EXISTS idx_enrollments_section ON enrollments(section_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_student ON enrollments(student_id);


-- 2. NEW TABLE: Variant pool

CREATE TABLE IF NOT EXISTS variant_pool (
    id TEXT PRIMARY KEY,
    problem_id TEXT NOT NULL REFERENCES problems(id),
    parameters_json TEXT NOT NULL,
    parameter_hash TEXT NOT NULL,
    problem_text TEXT,
    minterms TEXT,
    dont_cares TEXT,
    solution_json TEXT NOT NULL,
    generated_by TEXT NOT NULL DEFAULT 'template',
    verified INTEGER NOT NULL DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(problem_id, parameter_hash)
);

CREATE INDEX IF NOT EXISTS idx_variant_pool_problem ON variant_pool(problem_id);


-- 3. NEW TABLE: Draft answers (separated from submissions)

CREATE TABLE IF NOT EXISTS draft_answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    attempt_id INTEGER NOT NULL REFERENCES attempts(id),
    problem_id TEXT NOT NULL REFERENCES problems(id),
    answer_raw TEXT NOT NULL DEFAULT '',
    updated_at TEXT DEFAULT (datetime('now')),
    UNIQUE(attempt_id, problem_id)
);

CREATE INDEX IF NOT EXISTS idx_drafts_attempt ON draft_answers(attempt_id);


-- 4. NEW TABLE: Grades (separated from submissions)

CREATE TABLE IF NOT EXISTS grades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    submission_id INTEGER NOT NULL REFERENCES submissions(id),
    score REAL NOT NULL,
    correct INTEGER NOT NULL,
    feedback TEXT,
    grading_tier TEXT NOT NULL DEFAULT 'deterministic',
    grading_status TEXT NOT NULL DEFAULT 'graded',
    graded_by TEXT,
    graded_at TEXT DEFAULT (datetime('now')),
    previous_score REAL,
    previous_feedback TEXT,
    regraded_at TEXT,
    UNIQUE(submission_id)
);

CREATE INDEX IF NOT EXISTS idx_grades_submission ON grades(submission_id);


-- 5. NEW TABLE: Attempt results (denormalized aggregate)

CREATE TABLE IF NOT EXISTS attempt_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    attempt_id INTEGER NOT NULL REFERENCES attempts(id),
    total_score REAL NOT NULL,
    total_points_earned REAL NOT NULL,
    total_points_possible REAL NOT NULL,
    problems_correct INTEGER NOT NULL,
    problems_total INTEGER NOT NULL,
    computed_at TEXT DEFAULT (datetime('now')),
    UNIQUE(attempt_id)
);


-- 6. NEW TABLE: Quiz sessions (Phase 5 stub)

CREATE TABLE IF NOT EXISTS quiz_sessions (
    id TEXT PRIMARY KEY,
    assignment_id TEXT NOT NULL REFERENCES assignments(id),
    section_id TEXT REFERENCES sections(id),
    created_by TEXT NOT NULL REFERENCES instructors(id),
    qr_url TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    opens_at TEXT,
    closes_at TEXT,
    time_limit_minutes INTEGER,
    created_at TEXT DEFAULT (datetime('now'))
);


-- 7. ALTER existing tables (SQLite requires careful handling)

-- assignments: add new columns
ALTER TABLE assignments ADD COLUMN offering_id TEXT REFERENCES course_offerings(id);
ALTER TABLE assignments ADD COLUMN type TEXT NOT NULL DEFAULT 'homework';
ALTER TABLE assignments ADD COLUMN max_attempts INTEGER NOT NULL DEFAULT 1;
ALTER TABLE assignments ADD COLUMN time_limit_minutes INTEGER;
ALTER TABLE assignments ADD COLUMN opens_at TEXT;
ALTER TABLE assignments ADD COLUMN closes_at TEXT;

-- problems: add new columns
ALTER TABLE problems ADD COLUMN problem_type TEXT NOT NULL DEFAULT 'kmap_simplification';
ALTER TABLE problems ADD COLUMN points REAL NOT NULL DEFAULT 1.0;
ALTER TABLE problems ADD COLUMN depends_on_problem_id TEXT REFERENCES problems(id);

-- attempts: add new columns
ALTER TABLE attempts ADD COLUMN status TEXT NOT NULL DEFAULT 'created';
ALTER TABLE attempts ADD COLUMN attestation_signed INTEGER DEFAULT 0;
ALTER TABLE attempts ADD COLUMN attestation_signed_at TEXT;

-- submissions: add normalized answer column
ALTER TABLE submissions ADD COLUMN answer_normalized TEXT;


-- 8. VIEWS

CREATE VIEW IF NOT EXISTS v_student_attempt_status AS
SELECT
    a.student_id,
    a.assignment_id,
    a.attempt_number,
    a.status,
    a.started_at,
    a.submitted_at,
    ar.total_score,
    ar.problems_correct,
    ar.problems_total,
    asn.max_attempts,
    CASE WHEN a.attempt_number < asn.max_attempts AND a.status = 'graded' THEN 1 ELSE 0 END AS can_retry
FROM attempts a
JOIN assignments asn ON a.assignment_id = asn.id
LEFT JOIN attempt_results ar ON a.id = ar.attempt_id;

CREATE VIEW IF NOT EXISTS v_grade_report AS
SELECT
    s.id AS student_id,
    s.name AS student_name,
    a.assignment_id,
    a.attempt_number,
    p.parent_label,
    p.sub_label,
    p.points AS problem_points,
    sub.answer AS answer_raw,
    g.score,
    g.correct,
    g.feedback,
    g.grading_tier
FROM submissions sub
JOIN attempts a ON sub.student_id = a.student_id
    AND sub.submitted_at >= a.started_at
JOIN students s ON a.student_id = s.id
JOIN problems p ON sub.problem_id = p.id
LEFT JOIN grades g ON sub.id = g.submission_id;


-- 9. Backfill: populate status for existing attempts
UPDATE attempts SET status = 'graded' WHERE submitted_at IS NOT NULL AND total_score IS NOT NULL;
UPDATE attempts SET status = 'submitted' WHERE submitted_at IS NOT NULL AND total_score IS NULL;
UPDATE attempts SET status = 'in_progress' WHERE submitted_at IS NULL;

-- 10. Backfill: set hw5 max_attempts
UPDATE assignments SET max_attempts = 3 WHERE id = 'hw5';
```

### Step 2: Backfill variant_pool from existing variant_assignments

After the migration SQL runs, write a Python script (`migrations/backfill_variant_pool.py`) that:

1. Reads all rows from `variant_assignments`
2. For each unique `(problem_id, variant_json)` combination:
   - Parses the variant_json
   - Computes a SHA256 hash of the canonical parameters
   - Inserts into `variant_pool` (id = existing variant_id, problem_id, parameters_json, solution_json, etc.)
3. This means all existing variants are now in the pool and can be reused

Do NOT modify the existing `variant_assignments` table structure — it still works. The pool is an additive layer.

### Step 3: Update seed.py

Update the seeding script to also populate:
- `courses`: ECE_M16
- `course_offerings`: ECE_M16_SP26
- `instructors`: msrivastava (Mani Srivastava)
- `sections`: ECE_M16_SP26_1A
- `enrollments`: all 3 students → section 1A
- `variant_pool`: generate 10 variants per K-map problem using TemplateGenerator
- `assignments.offering_id`, `assignments.max_attempts = 3`
- `problems.points`: K-map problems = 2.0, follow-up = 1.0
- `attempts.status`: set correctly for each test student

---

## Backend Code Changes

### New file: `autota/web/variant_draw.py`

The variant pool draw logic. This is the most important new code.

```python
def draw_variants(db, student_id: str, assignment_id: str, attempt_id: int) -> dict:
    """
    Draw one variant per independent problem group from the pool.

    Rules:
    1. For each parent group (e.g. Q1 with sub-parts a, b, c):
       - All sub-parts share ONE variant draw from the parent's pool
    2. Exclude any variant_ids this student has seen in prior attempts
    3. If pool exhausted, fall back to TemplateGenerator for fresh variant

    Returns: {problem_id: variant_pool_row} mapping
    """
```

### New file: `autota/web/routes/retry.py`

```
POST /api/retry/{student_id}/{assignment_id}
```

Logic:
1. Verify latest attempt is "graded" (or "submitted" with grades)
2. Verify attempt_number < assignment.max_attempts
3. Create new attempt (attempt_number + 1, status = "created")
4. Call `draw_variants()` — gets fresh variants excluding prior ones
5. Insert into variant_assignments
6. Return new attempt_id + attempt_number

### Modified: `autota/web/routes/assignment.py`

**GET /api/assignment/{student_id}** response now includes:
- `attempt.status` field
- `assignment.max_attempts` field
- `problems[].points` field
- `can_retry` boolean (true if latest attempt graded + under max)
- `attempts_remaining` count

When the latest attempt is "graded" and can_retry is true, the frontend shows a "Start New Attempt" button.

### Modified: `autota/web/routes/submit.py`

**POST /api/submit** changes:
- Takes `attempt_id` in request body (not just student_id)
- Verifies attempt is in "in_progress" status before accepting
- After grading each problem, inserts into `grades` table (separate from submissions)
- Computes weighted score: Σ(grade.score × problem.points) / Σ(problem.points)
- Inserts into `attempt_results`
- Updates attempt.status to "graded"
- Response includes `points_earned` per problem, `total_points_earned`, `total_points_possible`, `can_retry`, `attempts_remaining`

**POST /api/save-answer** changes:
- Saves to `draft_answers` table (upsert) instead of/in addition to submissions
- Drafts are mutable. Submissions (on final submit) are immutable.

### Modified: `autota/web/db.py`

Add query functions for:
- `get_variant_from_pool(problem_id, exclude_ids)` — random draw
- `insert_variant_to_pool(variant_data)` — for backfill and on-demand generation
- `get_student_prior_variants(student_id, assignment_id)` — for exclusion
- `create_attempt(student_id, assignment_id)` — with proper numbering
- `get_attempt_status(student_id, assignment_id)` — latest attempt info
- `insert_draft_answer(attempt_id, problem_id, answer)` — upsert
- `get_draft_answers(attempt_id)` — for resume
- `insert_grade(submission_id, score, correct, feedback, tier)` — separate from submission
- `compute_attempt_result(attempt_id)` — weighted aggregate

---

## Frontend Changes (Minimal)

### Review.jsx / Results screen

After submit, if `can_retry` is true:
- Show "You have {attempts_remaining} attempt(s) remaining"
- Show "Start New Attempt" button
- Button calls `POST /api/retry/{sid}/{assignment_id}` then reloads

### Question.jsx

If `problem.points` is available, show it:
- Next to the problem label: "Q1a · 2 pts"

### Landing.jsx

Show: "Attempt {n} of {max_attempts}" instead of just "Attempt #{n}"

### api.js

Add:
- `retryAssignment(studentId, assignmentId)` — calls POST /api/retry
- Update `submitAnswers()` to send `attempt_id`
- Update `saveAnswer()` to use draft endpoint semantics

---

## Testing

1. Run migration: `sqlite3 data/autota.db < migrations/002_schema_hardening.sql`
2. Run backfill: `python -m migrations.backfill_variant_pool`
3. Re-run seed: `./seed.sh` (should be idempotent — skips existing data)
4. Test existing flow still works (name check → answer → submit → graded)
5. Test retry: after grading, click "Start New Attempt" → should get different variants
6. Verify sub-parts share variants: Q1a and Q1b should reference the same parent variant
7. Verify weighted scoring: K-map problem (2 pts) wrong affects score more than follow-up (1 pt)
8. Run `pytest` — all 79 Phase 1 tests must pass
9. Check views: `SELECT * FROM v_student_attempt_status;` should show correct data

---

## Build Order

1. Create `migrations/002_schema_hardening.sql` and run it
2. Write + run `migrations/backfill_variant_pool.py`
3. Update `seed.py` to populate new tables
4. Implement `variant_draw.py`
5. Implement `routes/retry.py`
6. Update `routes/assignment.py` (add new response fields)
7. Update `routes/submit.py` (attempt_id, grades table, weighted scoring)
8. Update `routes/submit.py` save-answer (draft_answers table)
9. Update frontend: results retry button, points display, attempt count
10. Test full flow including retry
11. Run `pytest`

---

## What NOT to Touch

- The existing frontend screens (NameCheck, Landing, Question, MainPage, Attestation) — no structural changes
- The Phase 1 verifier code (`autota/verify/`)
- The Phase 1 template generator (`autota/template_generator.py`)
- The Phase 1 CLI (`autota/cli.py`)
- The existing 79 tests
