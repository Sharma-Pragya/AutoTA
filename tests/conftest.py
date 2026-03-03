"""Shared pytest fixtures for HTTP endpoint tests.

Strategy: patch get_db_connection to point at a tmp_path SQLite file
(not in-memory) so that the db_conn() context manager (which calls
conn.close()) works correctly without destroying the DB state.

The patch must be active *before* TestClient(app) is created because
FastAPI's lifespan hook calls init_db() → get_db_connection().
"""

import json
import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


# ── Schema SQL ────────────────────────────────────────────────────────────────
# This is the full production schema (from migrations + init_db).
# quiz_sessions includes the migration-added columns.

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS courses (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    department TEXT
);
CREATE TABLE IF NOT EXISTS course_offerings (
    id TEXT PRIMARY KEY,
    course_id TEXT NOT NULL REFERENCES courses(id),
    quarter TEXT NOT NULL,
    year INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS instructors (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    role TEXT DEFAULT 'instructor'
);
CREATE TABLE IF NOT EXISTS sections (
    id TEXT PRIMARY KEY,
    offering_id TEXT NOT NULL REFERENCES course_offerings(id),
    label TEXT NOT NULL,
    instructor_id TEXT REFERENCES instructors(id)
);
CREATE TABLE IF NOT EXISTS students (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    section TEXT
);
CREATE TABLE IF NOT EXISTS enrollments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL REFERENCES students(id),
    section_id TEXT NOT NULL REFERENCES sections(id),
    enrolled_at TEXT DEFAULT (datetime('now')),
    dropped INTEGER DEFAULT 0,
    UNIQUE(student_id, section_id)
);
CREATE TABLE IF NOT EXISTS assignments (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    course TEXT NOT NULL DEFAULT 'ECE M16',
    spec_path TEXT NOT NULL DEFAULT '',
    instructions TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now')),
    offering_id TEXT REFERENCES course_offerings(id),
    type TEXT DEFAULT 'homework',
    max_attempts INTEGER DEFAULT 1,
    time_limit_minutes INTEGER,
    opens_at TEXT,
    closes_at TEXT
);
CREATE TABLE IF NOT EXISTS problems (
    id TEXT PRIMARY KEY,
    assignment_id TEXT NOT NULL REFERENCES assignments(id),
    parent_label TEXT NOT NULL,
    sub_label TEXT,
    display_order INTEGER NOT NULL,
    text TEXT NOT NULL,
    minterms TEXT,
    dont_cares TEXT,
    hint TEXT,
    answer_format TEXT NOT NULL,
    placeholder TEXT,
    problem_type TEXT DEFAULT 'kmap_simplification',
    points REAL DEFAULT 1.0,
    depends_on_problem_id TEXT REFERENCES problems(id)
);
CREATE TABLE IF NOT EXISTS variant_pool (
    id TEXT PRIMARY KEY,
    problem_id TEXT NOT NULL REFERENCES problems(id),
    parameters_json TEXT NOT NULL,
    parameter_hash TEXT NOT NULL DEFAULT '',
    problem_text TEXT,
    minterms TEXT,
    dont_cares TEXT,
    solution_json TEXT NOT NULL,
    generated_by TEXT DEFAULT 'template',
    verified INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS variant_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL REFERENCES students(id),
    problem_id TEXT NOT NULL REFERENCES problems(id),
    variant_id TEXT NOT NULL,
    variant_json TEXT NOT NULL,
    solution_json TEXT NOT NULL,
    attempt_number INTEGER NOT NULL DEFAULT 1,
    assigned_at TEXT DEFAULT (datetime('now')),
    attempt_id INTEGER REFERENCES attempts(id),
    UNIQUE(student_id, problem_id, attempt_number)
);
CREATE TABLE IF NOT EXISTS submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL REFERENCES students(id),
    problem_id TEXT NOT NULL REFERENCES problems(id),
    variant_assignment_id INTEGER NOT NULL REFERENCES variant_assignments(id),
    answer TEXT NOT NULL,
    score REAL,
    correct INTEGER,
    feedback TEXT,
    graded_at TEXT,
    submitted_at TEXT DEFAULT (datetime('now')),
    attestation_signed INTEGER DEFAULT 0,
    answer_normalized TEXT
);
CREATE TABLE IF NOT EXISTS grades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    submission_id INTEGER NOT NULL REFERENCES submissions(id),
    score REAL NOT NULL,
    correct INTEGER NOT NULL,
    feedback TEXT,
    grading_tier TEXT DEFAULT 'deterministic',
    grading_status TEXT DEFAULT 'graded',
    graded_by TEXT DEFAULT 'autota_verifier',
    graded_at TEXT DEFAULT (datetime('now')),
    previous_score REAL,
    previous_feedback TEXT,
    regraded_at TEXT
);
CREATE TABLE IF NOT EXISTS attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL REFERENCES students(id),
    assignment_id TEXT NOT NULL REFERENCES assignments(id),
    attempt_number INTEGER NOT NULL DEFAULT 1,
    started_at TEXT DEFAULT (datetime('now')),
    submitted_at TEXT,
    total_score REAL,
    status TEXT DEFAULT 'in_progress',
    attestation_signed INTEGER DEFAULT 0,
    attestation_signed_at TEXT,
    UNIQUE(student_id, assignment_id, attempt_number)
);
CREATE TABLE IF NOT EXISTS attempt_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    attempt_id INTEGER NOT NULL REFERENCES attempts(id),
    total_score REAL NOT NULL,
    total_points_earned REAL NOT NULL,
    total_points_possible REAL NOT NULL,
    problems_correct INTEGER NOT NULL,
    problems_total INTEGER NOT NULL,
    computed_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS draft_answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    attempt_id INTEGER NOT NULL REFERENCES attempts(id),
    problem_id TEXT NOT NULL REFERENCES problems(id),
    answer_raw TEXT NOT NULL,
    updated_at TEXT DEFAULT (datetime('now')),
    UNIQUE(attempt_id, problem_id)
);
CREATE TABLE IF NOT EXISTS quiz_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assignment_id TEXT NOT NULL REFERENCES assignments(id),
    section_id TEXT REFERENCES sections(id),
    created_by TEXT REFERENCES instructors(id),
    qr_url TEXT,
    status TEXT DEFAULT 'pending',
    opens_at TEXT,
    closes_at TEXT,
    time_limit_minutes INTEGER,
    created_at TEXT DEFAULT (datetime('now')),
    code TEXT,
    time_limit_seconds INTEGER DEFAULT 600,
    started_at TEXT,
    closed_at TEXT
);
CREATE TABLE IF NOT EXISTS quiz_participants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quiz_session_id INTEGER NOT NULL REFERENCES quiz_sessions(id),
    student_id TEXT NOT NULL,
    joined_at TEXT NOT NULL DEFAULT (datetime('now')),
    variant_assignments_json TEXT,
    UNIQUE(quiz_session_id, student_id)
);
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
"""


def _make_conn(db_path: Path):
    """Return a factory that opens the test DB at db_path."""
    def _factory():
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        return conn
    return _factory


# ── DB fixtures ───────────────────────────────────────────────────────────────

@pytest.fixture()
def db_path(tmp_path):
    """Bare schema DB (no seed data)."""
    path = tmp_path / "test.db"
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    conn.close()
    return path


@pytest.fixture()
def seeded_db(db_path):
    """DB with quiz-ready fixtures: 1 assignment, 2 problems, 2 students, 1 pending quiz."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    # Solution: minterms 0,1,2,3 (4-var: A'B'  → any valid expression)
    solution = json.dumps({
        "simplified_expression": "A'B'",
        "minterms": [0, 1, 2, 3],
        "dont_cares": [],
    })
    params = json.dumps({"minterms": [0, 1, 2, 3], "dont_cares": []})

    conn.executescript("""
        INSERT INTO assignments (id, title, course, spec_path, type, max_attempts)
        VALUES ('quiz1', 'Test Quiz', 'ECE M16', '', 'quiz', 1);

        INSERT INTO problems (id, assignment_id, parent_label, display_order,
                              text, answer_format, points, problem_type)
        VALUES
          ('p1', 'quiz1', '1', 1, 'Simplify f(A,B,C,D)=Σm(0,1,2,3)',
           'boolean_expression', 2.0, 'kmap_simplification'),
          ('p2', 'quiz1', '2', 2, 'Simplify g(A,B,C,D)=Σm(0,1,2,3)',
           'boolean_expression', 2.0, 'kmap_simplification');
    """)

    conn.execute(
        "INSERT INTO variant_pool (id, problem_id, parameters_json, parameter_hash, "
        "minterms, dont_cares, solution_json, problem_text) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        ("vp-p1-1", "p1", params, "h1", "[0,1,2,3]", "[]", solution, "Simplify f"),
    )
    conn.execute(
        "INSERT INTO variant_pool (id, problem_id, parameters_json, parameter_hash, "
        "minterms, dont_cares, solution_json, problem_text) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        ("vp-p2-1", "p2", params, "h2", "[0,1,2,3]", "[]", solution, "Simplify g"),
    )

    conn.executescript("""
        INSERT INTO students (id, name, email) VALUES
          ('S1', 'Alice', 'alice@test.edu'),
          ('S2', 'Bob', 'bob@test.edu');

        INSERT INTO quiz_sessions (assignment_id, code, status, time_limit_seconds)
        VALUES ('quiz1', 'TEST1', 'pending', 600);
    """)

    conn.commit()
    conn.close()
    return db_path


@pytest.fixture()
def instructor_db(seeded_db):
    """Extends seeded_db with graded homework data for instructor dashboard tests."""
    conn = sqlite3.connect(str(seeded_db))
    conn.row_factory = sqlite3.Row

    # A homework assignment with graded attempts
    conn.executescript("""
        INSERT INTO assignments (id, title, course, spec_path, type, max_attempts)
        VALUES ('hw1', 'Homework 1', 'ECE M16', '', 'homework', 2);

        INSERT INTO problems (id, assignment_id, parent_label, display_order,
                              text, answer_format, points, problem_type)
        VALUES ('hp1', 'hw1', '1', 1, 'HW problem', 'boolean_expression', 1.0, 'kmap_simplification');
    """)

    conn.execute(
        "INSERT INTO variant_pool (id, problem_id, parameters_json, parameter_hash, "
        "minterms, dont_cares, solution_json) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("vp-hp1", "hp1", '{"minterms":[0],"dont_cares":[]}', "hh1",
         "[0]", "[]", '{"simplified_expression":"A\'B\'C\'D\'"}'),
    )

    # Alice: graded attempt, score 1.0
    conn.execute(
        "INSERT INTO attempts (student_id, assignment_id, attempt_number, status, total_score, submitted_at)"
        " VALUES ('S1', 'hw1', 1, 'graded', 1.0, datetime('now'))"
    )
    attempt_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.execute(
        "INSERT INTO attempt_results (attempt_id, total_score, total_points_earned, "
        "total_points_possible, problems_correct, problems_total) VALUES (?, 1.0, 1.0, 1.0, 1, 1)",
        (attempt_id,)
    )
    # Need variant_assignment + submission + grade for per-problem stats
    conn.execute(
        "INSERT INTO variant_assignments (student_id, problem_id, variant_id, variant_json, "
        "solution_json, attempt_number, attempt_id) VALUES ('S1', 'hp1', 'vp-hp1', '{}', '{}', 1, ?)",
        (attempt_id,)
    )
    va_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.execute(
        "INSERT INTO submissions (student_id, problem_id, variant_assignment_id, answer, "
        "score, correct, feedback) VALUES (?, ?, ?, ?, 1.0, 1, 'Correct')",
        ("S1", "hp1", va_id, "A'B'")
    )
    sub_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.execute(
        "INSERT INTO grades (submission_id, score, correct, feedback) VALUES (?, 1.0, 1, 'Correct')",
        (sub_id,)
    )

    conn.commit()
    conn.close()
    return seeded_db


# ── Client fixtures ───────────────────────────────────────────────────────────

@pytest.fixture()
def client(seeded_db):
    """TestClient backed by seeded_db. Auth is disabled (no token set)."""
    import autota.web.auth as auth_module
    factory = _make_conn(seeded_db)
    with patch("autota.web.db.get_db_connection", side_effect=lambda: factory()), \
         patch.object(auth_module, "_TOKEN", ""):
        # Import app lazily inside patch so init_db() uses our fake connection
        from autota.web.app import app
        with TestClient(app, raise_server_exceptions=True) as c:
            yield c


@pytest.fixture()
def authed_client(seeded_db):
    """TestClient with a test instructor token enforced."""
    import autota.web.auth as auth_module
    factory = _make_conn(seeded_db)
    TOKEN = "test-secret-token"
    with patch("autota.web.db.get_db_connection", side_effect=lambda: factory()), \
         patch.object(auth_module, "_TOKEN", TOKEN):
        from autota.web.app import app
        with TestClient(app, raise_server_exceptions=True) as c:
            c._token = TOKEN
            yield c


@pytest.fixture()
def instr_client(instructor_db):
    """TestClient backed by instructor_db. Auth disabled."""
    import autota.web.auth as auth_module
    factory = _make_conn(instructor_db)
    with patch("autota.web.db.get_db_connection", side_effect=lambda: factory()), \
         patch.object(auth_module, "_TOKEN", ""):
        from autota.web.app import app
        with TestClient(app, raise_server_exceptions=True) as c:
            yield c
