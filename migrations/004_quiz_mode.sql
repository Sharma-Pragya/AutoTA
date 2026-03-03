-- Phase 2.3: Quiz Mode tables
-- Run: sqlite3 data/autota.db < migrations/004_quiz_mode.sql
-- Note: ALTER TABLE ADD COLUMN IF NOT EXISTS not supported in SQLite < 3.37
-- New columns are added by the Python migration script instead.
-- This file only creates new tables.

-- quiz_submissions: every submit attempt per student (unlimited retries)
CREATE TABLE IF NOT EXISTS quiz_submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quiz_session_id INTEGER NOT NULL REFERENCES quiz_sessions(id),
    student_id TEXT NOT NULL,
    attempt_number INTEGER NOT NULL DEFAULT 1,
    answers_json TEXT NOT NULL,
    scores_json TEXT,
    total_score REAL,
    total_points_earned REAL,
    is_best INTEGER NOT NULL DEFAULT 0,
    submitted_at TEXT NOT NULL DEFAULT (datetime('now')),
    graded_at TEXT,
    UNIQUE(quiz_session_id, student_id, attempt_number)
);

CREATE INDEX IF NOT EXISTS idx_quiz_sub_session_student
    ON quiz_submissions(quiz_session_id, student_id);

-- quiz_participants: students who joined (even without submitting)
CREATE TABLE IF NOT EXISTS quiz_participants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quiz_session_id INTEGER NOT NULL REFERENCES quiz_sessions(id),
    student_id TEXT NOT NULL,
    joined_at TEXT NOT NULL DEFAULT (datetime('now')),
    variant_assignments_json TEXT,
    UNIQUE(quiz_session_id, student_id)
);
