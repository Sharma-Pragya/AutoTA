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

-- variant_assignments: add attempt_id reference
ALTER TABLE variant_assignments ADD COLUMN attempt_id INTEGER REFERENCES attempts(id);


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
